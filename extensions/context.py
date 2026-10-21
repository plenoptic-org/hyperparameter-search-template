#!/usr/bin/env python3
from copier_template_extensions import ContextHook
import ast
import pathlib


class ContextUpdater(ContextHook):
    def hook(self, context):
        if "images" in context and context["images"].endswith(".py"):
            tree = ast.parse(pathlib.Path(context["images"]).read_text())
            funcs = [f.name for f in tree.body if isinstance(f, ast.FunctionDef)]
            context["images"] = funcs
