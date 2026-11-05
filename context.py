#!/usr/bin/env python3
from copier_template_extensions import ContextHook
import ast
import pathlib
import shutil


complex_choices = ["image", "model", "loss_function", "penalty_function",
                   "initial_image", "optimized_metric", "reference_metric",
                   "optimizer", "scheduler"]
# these variable are also allowed to load in paths
load_in_paths = ["image", "initial_image"]
dict_choices = ["optimizer_kwargs", "scheduler_kwargs"]
types = {"seed": "int", "penalty_lambda": "float", "max_iter": "int", "stop_criterion": "float",
         "stop_iters_to_check": "int", "method": "str", "k": "int", "p": "int", "q": "int",
         "initial_noise": "float", "change_scale_criterion": "float", "ctf_iters_to_check": "int",
         "coarse_to_fine": "str", "minmax": "str", "metric_tradeoff_lambda": "float",
         "optimizer_kwargs": "dict[str, float | int | bool | str]",
         "scheduler_kwargs": "dict[str, float | int | bool | str]"}

def validate(name, value):
    if name == "optimizer":
        value = value.split(";")
        if not all([v.startswith("torch") for v in value]):
            raise ValueError("optimizers must be torch objects!")
    elif name == "scheduler":
        value = value.split(";")
        if not all([v.startswith("torch") or v == "None" for v in value]):
            raise ValueError("schedulers must be torch objects or None!")
    elif name in ["method", "coarse_to_fine", "minmax"]:
        if not isinstance(value, list):
            value = [value]
        accepted_vals = {
            "method": {"power", "exact", "randomized_svd"},
            "coarse_to_fine": {"together", "separate"},
            "minmax": {"min", "max"},
        }
        if any([v not in accepted_vals[name] for v in value]):
            raise ValueError(f"values for {name} must be one of {accepted_vals[name]}")


class ContextUpdater(ContextHook):
    def hook(self, context):
        complex_params = {}
        simple_params = {}
        dict_params = {}
        all_params = context.get("all_params", [])
        non_search_params = set(all_params) - set(context.get("search_params", []))
        non_search_params = sorted(non_search_params, key=lambda x: all_params.index(x))
        for param in all_params:
            if param in complex_choices and param in context:
                param_dict = {}
                val = context[param]
                validate(param, val)
                if val.endswith(".py"):
                    file_contents = pathlib.Path(val).read_text()
                    tree = ast.parse(file_contents)
                    # don't bring in private functions
                    funcs = [f for f in tree.body if isinstance(f, ast.FunctionDef)
                             if not f.name.startswith("_")]
                    param_dict["choices"] = [f.name for f in funcs]
                    calls = []
                    for f in funcs:
                        args = ','.join([f"{a.arg}" for a in f.args.args])
                        calls.append(f"{f.name}({args})")
                    param_dict["calls"] = calls
                    param_dict["functions"] = file_contents
                    param_dict["script_choices"] = param_dict["choices"]
                else:
                    values = val.split(";")
                    choices = []
                    calls = []
                    script_choices = []
                    for v in values:
                        if (path_v := pathlib.Path(v)).exists():
                            if pathlib.Path(context["_copier_conf"]["dst_path"]).exists():
                                shutil.copy(path_v, context["_copier_conf"]["dst_path"] / path_v.name)
                            script_choices.append(path_v.name)
                        else:
                            choice = ""
                            for v_ in v.split("("):
                                choice += v_.split(".")[-1].split(",")[0].strip()
                                if choice not in choices:
                                    break
                                choice += "_"
                            choices.append(choice)
                            calls.append(v)
                    param_dict["calls"] = calls
                    param_dict["choices"] = choices
                    param_dict["script_choices"] = choices + script_choices
                complex_params[param] = param_dict
            elif param in context:
                param_type = types[param]
                val = context[param]
                validate(param, val)
                if isinstance(val, str) and param not in dict_choices:
                    # then this is actually a list
                    if val.startswith("["):
                        try:
                            val = ast.literal_eval(val)
                        except ValueError:
                            # then this contains torch or plenoptic objects and so we
                            # just want to turn it into a list of strings
                            val = [v for v in val[1:-1].split(",")]
                if param in dict_choices:
                    non_kwargs_param = complex_params.get(param.split("_")[0], {})
                    if non_kwargs_param and len(non_kwargs_param["choices"]) > 1:
                        val = ast.literal_eval(val)
                        new_val = {}
                        for k, v in val.items():
                            if not isinstance(v, list):
                                v = [v]
                            new_val[k] = [str(v_) for v_ in v]
                        val = new_val
                        default = {}
                    else:
                        if not isinstance(val, list):
                            val = [val]
                        default = val[0]
                        val = {non_kwargs_param["choices"][0]: val}
                    dict_params[param] = (param_type, val, default)
                else:
                    if not isinstance(val, list):
                        val = [val]
                    if param_type == "str":
                        val = [f'"{v}"' for v in val]
                    simple_params[param] = (param_type, val)
        if "status_plot" in context and context["status_plot"]:
            if context["status_plot"].endswith(".py"):
                file_contents = pathlib.Path(context["status_plot"]).read_text()
                tree = ast.parse(file_contents)
                # don't bring in private functions
                funcs = [f.name for f in tree.body if isinstance(f, ast.FunctionDef)
                         if not f.name.startswith("_")]
                context["status_plot"] = {"functions": file_contents,
                                          "calls": [f"{f}" for f in funcs]}
            else:
                raise ValueError(f"status_plot must be empty or path to a script! but got {context['status_plot']}")
        context.update({
            "render_complex_params": complex_params,
            "render_load_params": load_in_paths,
            "render_simple_params": simple_params,
            "render_dict_params": dict_params,
            "non_search_params": non_search_params,
        })
