#!/usr/bin/env python3

import pytest
import os
import subprocess
from pathlib import Path
import itertools
import copier
from collections import OrderedDict
from context import types, load_in_paths, dict_choices, complex_choices


# use data= arg
# - for each synthesis object
# - search over all possible search choices. want each of them multiple and single
# - all booleans true/false
# - test custom paths for: status_plot, complex_choices
# - test load in paths for image, initial image
# - test synthesizer/optimizer interaction with dictionaries
# - check whether multi-stage works as expected
# - any errors to test? optimizer/scheduler should be torch but don't have to, so don't raise error there
#
# - run ruff on test to generated files to ensure not invalid syntax
# - then write_disbatch.py, all of generated synthesize.py?, and create_html.py
# - do with max_iter=2 and try it all?

ALL_PARAMS = complex_choices + list(types.keys())
DEFAULTS = {
    "int": [1, "[1, 10]"],
    "float": [0.5, "[0.5, 1.5]"],
}
PARAMS = OrderedDict({
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
    "loss_function": ["po.loss.mse", "test_files/loss_funcs.py", "po.loss.mse;po.loss.l2_norm"],
    "penalty_function": ["po.regularize.penalize_range", "test_files/penalties.py", "po.regularize.penalize_range;lambda x: po.regularize.penalize_range(x, (-.5, .5))"],
    "initial_image": [
        "torch.rand_like(image)",
        "test_files/images.py",
        "torch.rand_like(image);po.process.blur_downsample(po.data.curie(), 4)",
        "po.process.blur_downsample(po.data.curie(), 4);test_files/small_einstein.pgm",
    ],
    "optimized_metric": ["po.loss.mse", "test_files/loss_funcs.py", "po.loss.mse;po.loss.l2_norm"],
    "reference_metric": ["po.loss.mse", "test_files/loss_funcs.py", "po.loss.mse;po.loss.l2_norm"],
    "optimizer": ["torch.optim.Adam", "torch.optim.Adam;torch.optim.LBFGS"],
    "scheduler": ["None", "None;torch.optim.lr_scheduler.ReduceLROnPlateau"],

    "method": ["power", "['power', 'randomized_svd']"],
    "coarse_to_fine": ["separate", "['separate','together']"],
    "minmax": ["min", "['min','max']"],
})
tmp = {k: DEFAULTS[types[k]] for k in ALL_PARAMS if k not in PARAMS and "kwargs" not in k}
PARAMS.update(tmp)
OPTIMIZER_KWARGS = ["{'Adam': {'amsgrad': True, 'lr': 0.1}}", "{'Adam': [{'amsgrad': True, 'lr': 0.2}, {'amsgrad': True, 'lr': 0.1}], 'LBFGS': {}}", "{'Adam': {'amsgrad': True, 'lr': 0.1}, 'LBFGS': {}}"]
SCHEDULER_KWARGS = ["{'None': {}, 'ReduceLROnPlateau': [{'factor': 0.5}, {'factor': 0.2}]}", "{'None': {}, 'ReduceLROnPlateau': {'factor': 0.2}}"]

# add test for this
STATUS_PLOT = ["", "test_files/plot.py", "test_files/multiple_plots.py"]


met_params = ["seed", "image", "model", "loss_function", "penalty_function", "penalty_lambda", "initial_image", "optimizer", "scheduler", "stop_criterion", "stop_iters_to_check"]
metctf_params = ["seed", "image", "model", "loss_function", "penalty_function", "penalty_lambda", "coarse_to_fine", "initial_image", "optimizer", "optimizer_kwargs", "scheduler", "scheduler_kwargs", "stop_criterion", "stop_iters_to_check", "change_scale_criterion", "ctf_iters_to_check"]
mad_params = ["seed", "image", "optimized_metric", "reference_metric", "minmax", "metric_tradeoff_lambda", "penalty_function", "penalty_lambda", "initial_noise", "optimizer", "optimizer_kwargs", "scheduler", "scheduler_kwargs", "stop_criterion", "stop_iters_to_check"]
eig_params = ["seed", "image", "model", "method", "k", "p", "q", "stop_criterion"]


def construct_data(synth_params, synth_name, search_params):
    choices = []
    default_choice = {k: PARAMS[k][0] for k in synth_params}
    default_choice["synthesis_object"] = synth_name
    default_choice["animate"] = False
    default_choice["base_out"] = "."
    default_choice["cluster_prefix"] = ""
    default_choice["python_command"] = "python"
    default_choice["search_params"] = search_params
    to_search = OrderedDict({k: [v for v in PARAMS[k] if isinstance(v, str) and (Path(v).suffix == ".py" or ";" in v or v.startswith("["))] for k in search_params})
    if "optimizer" in to_search:
        to_search["optimizer_kwargs"] = OPTIMIZER_KWARGS
    if "scheduler" in to_search:
        to_search["scheduler_kwargs"] = SCHEDULER_KWARGS
    for vals in itertools.product(*to_search.values()):
        choice = default_choice.copy()
        choice.update(dict(zip(to_search.keys(), vals)))
        choice["max_iter"] = 2
        choice["status_plot"] = ""
        choices.append(choice)
    return choices


@pytest.mark.parametrize("search_param", met_params)
def test_metamer(subtests, search_param):
    test_path = Path("tests")
    choices = construct_data(met_params, "Metamer", [search_param])
    for i, choice in enumerate(choices):
        with subtests.test(msg=choices[i], choice=choice, i=i):
            tmp = test_path / f"test_metamer_{search_param}_{i}"
            copier.run_copy(".", tmp, data=choice, unsafe=True, overwrite=True)
            proc = subprocess.run(["python", "write_disbatch.py", "--no-for-disbatch", "--no-write-to-log"], cwd=tmp)
            if proc.returncode != 0:
                raise Exception(proc)
            proc = subprocess.run(["bash", "disbatch.txt"], cwd=tmp)
            if proc.returncode != 0:
                raise Exception(proc)
            proc = subprocess.run(["python", "create_html.py", "synthesis_duration", "synthesis_loss"], cwd=tmp)
            if proc.returncode != 0:
                raise Exception(proc)
