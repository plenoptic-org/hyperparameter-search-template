#!/usr/bin/env python3
from copier_template_extensions import ContextHook
import ast
import pathlib


class ContextUpdater(ContextHook):
    def hook(self, context):
        if "image_search" in context:
            if context["image_search"].endswith(".py"):
                file_contents = pathlib.Path(context["image_search"]).read_text()
                tree = ast.parse(file_contents)
                funcs = [f.name for f in tree.body if isinstance(f, ast.FunctionDef)]
                context["image_search_choices"] = funcs
                context["image_search_calls"] = [f"{f}()" for f in funcs]
                context["image_search_functions"] = file_contents
            else:
                images = context["image_search"].split(",")
                context["image_search_choices"] = [i.split(".")[-1].split('(')[0] for i in images]
                context["image_search_calls"] = images
        if "penalty_lambda" in context:
            penalty_lambda = context.pop("penalty_lambda")
            if not isinstance(penalty_lambda, list):
                penalty_lambda = [penalty_lambda]
            for lmbda in penalty_lambda:
                if lmbda < 0:
                    raise ValueError("penalty_lambda values must be non-negative")
            context["penalty_lambda"] = [float(lmbda) for lmbda in penalty_lambda]
