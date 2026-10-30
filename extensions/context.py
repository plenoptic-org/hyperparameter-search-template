#!/usr/bin/env python3
from copier_template_extensions import ContextHook
import ast
import pathlib


complex_choices = ["image", "model", "loss_function", "penalty_function",
                   "initial_image", "optimized_metric", "reference_metric",
                   "optimizer", "scheduler"]
dict_choices = ["optimizer_kwargs", "scheduler_kwargs"]
types = {"seed": "int", "penalty_lambda": "float", "max_iter": "int", "stop_criterion": "float",
         "stop_iters_to_check": "int", "method": "str", "k": "int", "p": "int", "q": "int",
         "initial_noise": "float", "change_scale_criterion": "float", "ctf_iters_to_check": "int",
         "coarse_to_fine": "str", "minmax": "str", "metric_tradeoff_lambda": "float",
         "optimizer_kwargs": "dict[str, float | int | bool | str]",
         "scheduler_kwargs": "dict[str, float | int | bool | str]"}


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
                if context[param].endswith(".py"):
                    file_contents = pathlib.Path(context[param]).read_text()
                    tree = ast.parse(file_contents)
                    # don't bring in private functions
                    funcs = [f.name for f in tree.body if isinstance(f, ast.FunctionDef)
                             if not f.name.startswith("_")]
                    param_dict["choices"] = funcs
                    param_dict["calls"] = [f"{f}()" for f in funcs]
                    param_dict["functions"] = file_contents
                else:
                    values = context[param].split(";")
                    param_dict["choices"] = [i.split('(')[0].split(".")[-1] for i in values]
                    param_dict["calls"] = values
                complex_params[param] = param_dict
            elif param in context:
                param_type = types[param]
                val = context[param]
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
        return {
            "render_complex_params": complex_params,
            "render_simple_params": simple_params,
            "render_dict_params": dict_params,
            "non_search_params": non_search_params,
        }
