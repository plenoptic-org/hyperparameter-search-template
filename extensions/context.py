#!/usr/bin/env python3
from copier_template_extensions import ContextHook
import ast
import pathlib


complex_choices = ["image", "model", "loss_function", "penalty_function",
                   "initial_image", "optimized_metric", "reference_metric"]
custom_converters = {"optimizer": "eval_torch", "scheduler": "eval_torch",
                     "optimizer_kwargs": "eval_dict", "scheduler_kwargs": "eval_dict"}

class ContextUpdater(ContextHook):
    def hook(self, context):
        complex_params = {}
        simple_params = {}
        for param in context.get("all_params", []):
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
                annot = custom_converters.get(param, "")
                if annot:
                    annot = f": Annotated[str, Parameter(converter={annot})]"
                val = context[param]
                if isinstance(val, str) and val != "None":
                    # These are the special strings: dictionaries and objects from the
                    # torch or plenoptic namespaces
                    if not any([val.startswith("{"), val.startswith("torch."), val.startswith("po.")]):
                        val = f'"{val}"'
                simple_params[param] = (annot, val)
        return {
            "render_complex_params": complex_params,
            "render_simple_params": simple_params,
        }
