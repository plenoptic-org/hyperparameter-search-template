#!/usr/bin/env python3

import pytest
import os
import subprocess
from pathlib import Path
import itertools
import copier
from collections import OrderedDict
from context import types, complex_choices


ALL_PARAMS = complex_choices + list(types.keys())
DEFAULTS = {
    "int": [1, [1, 10]],
    "float": [0.5, [0.5, 1.5]],
    "None | float": [None, [None, 1]],
}
PARAMS = OrderedDict(
    {
        "image": [
            "po.process.blur_downsample(po.data.einstein(), 4)",
            "test_files/images.py",
            "po.process.blur_downsample(po.data.einstein(), 4);po.process.blur_downsample(po.data.curie(), 4)",
            "po.process.blur_downsample(po.data.curie(), 4);test_files/small_einstein.pgm",
        ],
        "model": [
            "po.models.Gaussian(image.shape[-1] // 4, cache_filt=True)",
            "test_files/models.py",
            "po.models.Gaussian(4, cache_filt=True);po.models.CenterSurround(image.shape[-1] // 4, cache_filt=True)",
        ],
        "loss_function": [
            "po.loss.mse",
            "test_files/loss_funcs.py",
            "po.loss.mse;po.loss.l2_norm",
        ],
        "penalty_function": [
            "po.regularize.penalize_range",
            "test_files/penalties.py",
            "po.regularize.penalize_range;lambda x: po.regularize.penalize_range(x, (-.5, .5))",
        ],
        "initial_image": [
            "torch.rand_like(image)",
            "test_files/images.py",
            "torch.rand_like(image);po.process.blur_downsample(po.data.curie(), 4)",
            "po.process.blur_downsample(po.data.curie(), 4);test_files/small_einstein.pgm",
        ],
        "optimized_metric": [
            "po.loss.mse",
            "test_files/loss_funcs.py",
            "po.loss.mse;po.loss.l2_norm",
        ],
        "reference_metric": [
            "po.loss.mse",
            "test_files/loss_funcs.py",
            "po.loss.mse;po.loss.l2_norm",
        ],
        "optimizer": ["torch.optim.Adam", "torch.optim.Adam;torch.optim.LBFGS"],
        "scheduler": ["None", "None;torch.optim.lr_scheduler.ReduceLROnPlateau"],
        "method": ["power", ["power", "randomized_svd"]],
        "coarse_to_fine": ["separate", ["separate", "together"]],
        "minmax": ["min", ["min", "max"]],
    }
)
tmp = {
    k: DEFAULTS[types[k]] for k in ALL_PARAMS if k not in PARAMS and "kwargs" not in k
}
PARAMS.update(tmp)
OPTIMIZER_KWARGS = [
    "{'Adam': {'amsgrad': True, 'lr': 0.1}}",
    "{'Adam': [{'amsgrad': True, 'lr': 0.2}, {'amsgrad': True, 'lr': 0.1}], 'LBFGS': {}}",
    "{'Adam': {'amsgrad': True, 'lr': 0.1}, 'LBFGS': {}}",
]
SCHEDULER_KWARGS = [
    "{'None': {}, 'ReduceLROnPlateau': [{'factor': 0.5}, {'factor': 0.2}]}",
    "{'None': {}, 'ReduceLROnPlateau': {'factor': 0.2}}",
]


def construct_data(synth_params, synth_name, search_params, all_params=None):
    choices = []
    if all_params is None:
        all_params = PARAMS
    default_choice = {k: all_params[k][0] for k in synth_params}
    default_choice["synthesis_object"] = synth_name
    default_choice["animate"] = False
    default_choice["base_out"] = "."
    default_choice["cluster_prefix"] = ""
    default_choice["python_command"] = "python"
    default_choice["search_params"] = search_params
    default_choice["max_iter"] = 2
    default_choice["status_plot"] = ""
    to_search = OrderedDict(
        {
            k: [
                v
                for v in all_params[k]
                if isinstance(v, list)
                or isinstance(v, str)
                and (Path(v).suffix == ".py" or ";" in v)
            ]
            for k in search_params
        }
    )
    if "optimizer" in to_search:
        to_search["optimizer_kwargs"] = OPTIMIZER_KWARGS
    if "scheduler" in to_search:
        to_search["scheduler_kwargs"] = SCHEDULER_KWARGS
    for vals in itertools.product(*to_search.values()):
        choice = default_choice.copy()
        choice.update(dict(zip(to_search.keys(), vals)))
        choices.append(choice)
    return choices


def _run_test(choice, working_dir, plot_y="synthesis_loss"):
    copier.run_copy(".", working_dir, data=choice, unsafe=True, overwrite=True)
    proc = subprocess.run(
        ["python", "write_script.py", "--to-script", "--no-write-to-log"],
        cwd=working_dir,
    )
    if proc.returncode != 0:
        raise Exception(proc)
    proc = subprocess.run(["bash", "hyperparam_search.sh"], cwd=working_dir)
    if proc.returncode != 0:
        raise Exception(proc)
    proc = subprocess.run(
        ["python", "create_html.py", "synthesis_duration", plot_y], cwd=working_dir
    )
    if proc.returncode != 0:
        raise Exception(proc)


met_params = [
    "seed",
    "image",
    "model",
    "loss_function",
    "penalty_function",
    "penalty_lambda",
    "initial_image",
    "optimizer",
    "scheduler",
    "stop_criterion",
    "stop_iters_to_check",
]


@pytest.mark.parametrize("search_param", met_params)
def test_metamer(subtests, search_param):
    test_path = Path("tests")
    choices = construct_data(met_params, "Metamer", [search_param])
    for i, choice in enumerate(choices):
        with subtests.test(msg=choices[i], choice=choice, i=i):
            tmp = test_path / f"test_metamer_{search_param}_{i}"
            _run_test(choice, tmp)


@pytest.mark.parametrize(
    "status_plot", ["test_files/plot.py", "test_files/multiple_plots.py"]
)
def test_status_plot(subtests, status_plot):
    test_path = Path("tests")
    choices = construct_data(met_params, "Metamer", ["image"])
    for i, choice in enumerate(choices):
        choice["status_plot"] = status_plot
        with subtests.test(msg=choices[i], choice=choice, i=i):
            tmp = test_path / f"test_status_plot_{status_plot}_{i}"
            _run_test(choice, tmp)


metctf_params = [
    "seed",
    "image",
    "model",
    "loss_function",
    "penalty_function",
    "penalty_lambda",
    "coarse_to_fine",
    "initial_image",
    "optimizer",
    "scheduler",
    "stop_criterion",
    "stop_iters_to_check",
    "change_scale_criterion",
    "ctf_iters_to_check",
]


@pytest.mark.parametrize("search_param", metctf_params)
def test_metamerCTF(subtests, search_param):
    test_path = Path("tests")
    all_params = PARAMS.copy()
    # replace models with file that has ctf-supported models
    all_params["model"] = ["test_files/models_ctf.py"]
    # change_scale_criterion must be strictly greater than stop_criterion
    all_params["change_scale_criterion"] = [2, 5]
    choices = construct_data(metctf_params, "MetamerCTF", [search_param], all_params)
    for i, choice in enumerate(choices):
        with subtests.test(msg=choices[i], choice=choice, i=i):
            tmp = test_path / f"test_metamerCTF_{search_param}_{i}"
            _run_test(choice, tmp)


mad_params = [
    "seed",
    "image",
    "optimized_metric",
    "reference_metric",
    "minmax",
    "metric_tradeoff_lambda",
    "penalty_function",
    "penalty_lambda",
    "initial_noise",
    "optimizer",
    "scheduler",
    "stop_criterion",
    "stop_iters_to_check",
]


@pytest.mark.parametrize("search_param", mad_params)
def test_mad(subtests, search_param):
    test_path = Path("tests")
    choices = construct_data(mad_params, "MADCompetition", [search_param])
    for i, choice in enumerate(choices):
        with subtests.test(msg=choices[i], choice=choice, i=i):
            tmp = test_path / f"test_mad_{search_param}_{i}"
            _run_test(choice, tmp)


eig_params = ["seed", "image", "model", "method", "k", "p", "q", "stop_criterion"]


@pytest.mark.parametrize("search_param", eig_params)
def test_eig(subtests, search_param):
    test_path = Path("tests")
    choices = construct_data(eig_params, "Eigendistortion", [search_param])
    for i, choice in enumerate(choices):
        with subtests.test(msg=choices[i], choice=choice, i=i):
            tmp = test_path / f"test_eig_{search_param}_{i}"
            _run_test(choice, tmp, "max_iter")
