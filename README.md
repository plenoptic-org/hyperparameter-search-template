# Hyperparameter Search Template

This [copier](https://copier.readthedocs.io/) template allows for the quick creation of a repo for hyperparameter search when using one of the synthesis methods from [plenoptic](https://docs.plenoptic.org).

> [!WARNING]
> This template works for my purposes, but is not tested super broadly. If you have any problems, open an issue.

For now, this assumes that you are synthesizing images (which matters because of how they are saved to disk). If this is not the case for you, open an issue and let us know!

## Basic usage

To use, call [`copier copy`](https://copier.readthedocs.io/en/stable/generating/) pointing to this repo. If you use [uv](https://docs.astral.sh/uv/), that can be done with:

``` sh
uvx --with copier_template_extensions copier copy gh:plenoptic-org/hyperparameter-search-template TARGET_DIRECTORY --trust
```

The above will ask you a bunch of questions which it will use to generate the template. See [Hyperparameters](#hyperparameters) below for more info on possible values.

Note:
- `TARGET_DIRECTORY` is the directory to put the rendered template into.
- We need `copier_template_extensions` and `--trust` because we need to manipulate strings in python (see [copier docs](https://copier.readthedocs.io/en/stable/configuring/#unsafe) for more details).

The rendered directory will contain the following files:
- `write_script.py`: python script to generate a bash script which contains the calls to `synthesize.py` for every combination of hyperparameters.
- `synthesize.py`: python script which runs a single instance of synthesis.
- `create_html.py`: python script to create an interactive [altair](https://altair-viz.github.io/) and save as a stand-alone html file. Note this embeds the resulting synthesized images in the html, and so it can get large.
- `pyproject.toml`: file defining the requirements so you can easily install them, using `pip` or `uv`.
- `README.md`: readme containing basic info

All python scripts have command-line interfaces, call with `--help` to see their arguments.

The intended loop is as follows:

- Render the template, answering all questions.
- Look over the created `.py` files, to ensure they act as expected.
- Run `write_script.py` to create a script with all the `synthesize.py` calls. Note the command-line arguments here (run with the `--help` flag to see them), which you probably want to set.
- Run the created script, either directly (to run all in sequence) or using a tool such as [disBatch](https://github.com/flatironinstitute/disBatch) (to do so in parallel / on a cluster).
- Run `create_html.py` to create an interactive visualization. Note that command-line arguments *must* be set, in order to tell us e.g., what to put on the x-axis, how to facet, etc.
- Examine the created html file to determine what hyperparameters were most successful.
- Repeat:
  - If you are changing hyperparameters which use built-in pythonic types (e.g., `seed`, `optimizer_kwargs`, `penalty_lambda`), then you can simply edit `write_script.py`.
  - If you are changing hyperparameters which use python objects (e.g., `image`, `model`, `optimizer`), then you should run `copier update` (`uvx --with copier_template_extensions copier update TARGET_DIRECTORY --trust`) in order to update the template.
    - The exception here is if you would like to point `image` / `initial_image` to a file on disk, either an image file or the output of an earlier synthesis run. In that case, you can add the path to that file directly to `write_script.py`

## Virtual environments

Each rendered template will include a `pyproject.toml` file with dependencies, so you can a separate virtual environment for each project.

You can also create a shared virtual environment, if you are creating many of these. If you are using `uv`, you can use the environmental variable [`UV_PROJECT_ENVIRONMENT`](https://docs.astral.sh/uv/concepts/projects/config/#project-environment-path) so that you can still use `uv sync` / `uv run` etc. in the child directories.

## Hyperparameters

When you run `copier copy`, the template will ask you which synthesis object you wish to use and then which hyperparameters you wish to search over, only showing you those that are relevant for your chosen object.

You should select all parameters where you wish to either try multiple values OR set a non-default value (e.g., change the optimizer for `Metamer` to `LBFGS`).

There are three classes of hyperparameters, which have different expected formats:

1. `image`, `model`, `loss_function`, `penalty_function`, `initial_image`, `optimized_metric`, `reference_metric`, `optimizer`, `scheduler`: a string specifying one or more ;-separated values, e.g., `po.data.einstein();po.data.curie()`. See below for more details.
2. `optimizer_kwargs`, `scheduler_kwargs`: a single dictionary (if using the same for all `optimizer` / `scheduler` objects), a list of dictionaries (if only a single `optimizer` / `scheduler` and you wish to try different kwargs), or a dictionary of the above whose keys are the name of the `optimizer` / `scheduler` objects. See below for more details.
3. Everything else: a list of values, either ints, floats, or strings. If strings, the prompt will tell you the allowed values.

The possible values for the first two categories are explained in more detail below:

### `image` / `initial_image`

Any of the following:
- A single line which returns an image as a 4d tensor: `po.data.curie()`, `torch.rand((1, 1, 256, 256))`
- A path to an existing image: `path/to/image.jpg`
- A path to a saved synthesis object of the same type: `path/to/metamer.pt`
- A path to a script: `path/to/my_images.py`. See [custom scripts](#custom-scripts) for more details.
- A semicolon-connected list of the above: `po.data.curie();path/to/my_images.py`

`image` cannot refer to any other variables, but `initial_image` can refer to `image` (e.g., you can set it to `torch.rand_like(image)`).

Regardless of what you choose, you will always be able to pass the path to an existing image or synthesis object of the same type on the command-line to `synthesize.py`. To add these after `copier copy`, you can edit `write_script.py` directly. Unfortunately, I cannot figure out how to get the command-line help for that script to communicate that info.

`synthesize.py` will move both images to the appropriate dtype and device.

If a path is specified, the file will be copied into the rendered template directory. Note this is different from the behavior for custom scripts!

Some complex examples:
- `po.data.curie();po.data.einstein()`
- `po.process.blur_downsample(po.data.macaque(), 2)`
- `po.data.einstein();path/to/my_images.py`

### `model`

Any of the following:
- A single line which returns a [plenoptic-compatible model](https://docs.plenoptic.org/docs/tags/2.1.2/reference/models.html#model-requirements): `po.models.Gaussian(30, cache_filt=True)`.
- A path to a script: `path/to/my_models.py`. See [custom scripts](#custom-scripts) for more details.
- A semicolon-connected list of the above: `po.models.Gaussian(30, cache_filt=True);path/to/my_models.py`

`synthesize.py` calls `po.remove_grad(model)`, `model.eval()`, `model.to(dtype)`, and `model.to(device)`, so you do not need to do these yourself.

`model` can refer to `image`, so you can pass `po.models.PortillaSimoncelli(image.shape[-2:])`.

A complex example: `po.models.Gaussian(30);my_models.py;po.models.PortillaSimoncelli(image.shape[-2:])`.

### `loss_function` / `penalty_function` / `optimized_metric` / `reference_metric`

Any of the following:
- A single line which returns a plenoptic-compatible [metric](https://docs.plenoptic.org/docs/tags/2.1.2/reference/models.html#metric-requirements), loss function, or penalty function:
  - Metrics and loss functions accept two tensors and return a single scalar: `po.metric.mse`, `po.loss.l2_norm`
  - Penalty functions accept a single tensor and return a single scalar: `po.regularize.penalize_range`
- A path to a script: `path/to/my_metrics.py`. See [custom scripts](#custom-scripts) for more details.
- A semicolon-connected list of the above: `po.metric.mse;path/to/my_functions.py`

These definitions can refer to either `image` or (if relevant for the synthesis method) `model`.

`synthesize.py` **does not** call `po.remove_grad`, `.eval()`, `.to(dtype)`, or `.to(device)` on any of these, so if you are using a `torch.nn.Module` instead of a function, you will need to do that yourself. (It is recommended to do this based on `image`, e.g., `metric.to(image.dtype)`).

### `optimizer` / `scheduler`

Any of the following:
- A single line which returns a pytorch optimizer / scheduler: `torch.optim.Adam`, `torch.optim.lr_scheduler.StepLR`.
- A semicolon-connected list of the above: `torch.optim.Adam;torch.optim.LBFGS`

Note that, unlike `model`, these objects should not be initialized! That is, the proper string is `torch.optim.Adam`, **not** `torch.optim.Adam()`.

### `optimizer_kwargs` / `scheduler_kwargs`

Any of the following:
- a single dictionary defining the keyword arguments, if you are only using one optimizer/scheduler and using the same for all relevant objects: `{'lr': 0.1}`
- A list of dictionaries, if you are only using one optimizer/scheduler and wish to try different kwargs: `[{'lr': 0.1}, {'lr': 0.5}]`
- A dictionary whose keys are the name of the optimizer/scheduler objects and whose values are one of the above: `{'Adam': {'lr': 0.1, 'amsgrad': False}, 'LBFGS': [{'lr': 0.1}, {'lr': 0.2}]}`

## `status_plot`

Plots are important for understanding whether synthesis was successful or not. By default (when `status_plot` is unset), this template will set up `synthesize.py` so that it calls [`po.plot.synthesis_status(synth)`](https://docs.plenoptic.org/docs/tags/2.1.2/api/generated/plenoptic.plot.synthesis_status.html#plenoptic.plot.synthesis_status) to visualize the final synthesis status.

If you wish to customize this, you can instead pass the path to a python script. This script should contain some number of functions which accept a single synthesis object and return a matplotlib figure. In that case, `synthesize.py` call each of the script's public functions (those that do not start with `_`) in sequence, saving each as a separate `svg`.

Note that we always call `synthesis_imshow` and save the output as a `.png` file.

## Multi-stage synthesis

The ability to pass the path to an existing synthesis object to `initial_image` allows you to perform [multi-stage synthesis](https://docs.plenoptic.org/docs/tags/2.1.2/user_guide/penalties/datasaurus/general_principles.html#multi-stage-synthesis-can-help-when-things-are-hard), where the output of one synthesis procedure is used to initialize synthesis for another. This is particular useful when using [penalty functions](https://docs.plenoptic.org/docs/tags/2.1.2/user_guide/penalties/how_to_penalty.html).

However, the script created by `write_script.py` has no sense of dependencies and thus the calls to `synthesize.py` may be run in any order. Thus, if you are performing multi-stage synthesis, you should place the relevant calls in separate scripts: first, call `write_script.py` for those `synthesize.py` runs that with no dependencies, and run the resulting script. Then, edit `write_script.py` to point `initial_image` to the correct files, and repeat. If you have a more complex setup, it may be worth looking into a workflow manager, such as [snakemake](https://snakemake.readthedocs.io/).

## Custom scripts

Several of the above hyper-parameters can accept the path to a script as one of their values. In those cases, we will copy the full contents of those files into `synthesize.py` (instead of copying the script itself). The following requirements must be met:

- Any requirements beyond torch and plenoptic should be imported (e.g., `torchvision`), but torch and plenoptic do not need to (as long as you use the standard plenoptic shorthand, `po`).
- The script should contain a selection of functions. The public functions are the possible choices; private functions will be copied over but cannot be selected directly. They are intended to e.g.,, allow for shared code across the public functions.
- Each public function should return only the object of the specified type.
- Whether the public function can accept any arguments depends on the hyper-parameter. The hyper-parameters are initialized in `synthesize.py` in the following sequence, and so each hyper-parameter can refer to those that occur before it. All arguments are optional, and the tested uses are either zero arguments or `image`: `image`, `model`, `loss_function`, `penalty_function`, `penalty_lambda`, `initial_image`, `optimized_metric`, `reference_metric`.

## plenoptic version

If you need to specify a specific plenoptic version or branch, pass `--ask plenoptic_version` when running `copier copy` or `copier update`. The template will then ask you about the version to use. You can specify either a version (e.g., `2.0.0`), in which case we'll install the specified version from pypi, or a branch, in which case we'll install the specific branch from the plenoptic Github.

Note that we assume this specifies a branch if it doesn't look like a version string, and we do not validate that the branch exists.
