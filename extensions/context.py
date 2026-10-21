#!/usr/bin/env python3
from copier_template_extensions import ContextHook
import ast
import pathlib


class ContextUpdater(ContextHook):
    def hook(self, context):
        hyperparams = context.get("render_hyperparams", {})
        # HOW TO HANDLE NOT SEARCHING OVER IMAGE, MODEL? do same thing but instead raise
        # an error if there's more than one choice?
        for k in context.get("hyperparams", []):
            key = f"{k}_search"
            if key in context and key not in hyperparams:
                hyperparams[k] = {}
                val = context.pop(key, "")
                if val.endswith(".py"):
                    file_contents = pathlib.Path(val).read_text()
                    tree = ast.parse(file_contents)
                    funcs = [f.name for f in tree.body if isinstance(f, ast.FunctionDef)]
                    hyperparams[k]["choices"] = funcs
                    hyperparams[k]["calls"] = [f"{f}()" for f in funcs]
                    hyperparams[k]["functions"] = file_contents
                else:
                    values = val.split(",")
                    hyperparams[k]["choices"] = [i.split(".")[-1].split('(')[0] for i in values]
                    hyperparams[k]["calls"] = values
        context["render_hyperparams"] = hyperparams
        if "penalty_lambda" in context:
            penalty_lambda = context.pop("penalty_lambda")
            if not isinstance(penalty_lambda, list):
                penalty_lambda = [penalty_lambda]
            for lmbda in penalty_lambda:
                if lmbda < 0:
                    raise ValueError("penalty_lambda values must be non-negative")
            context["penalty_lambda"] = [float(lmbda) for lmbda in penalty_lambda]
