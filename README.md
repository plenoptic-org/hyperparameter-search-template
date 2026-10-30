# Hyperparameter Search Template

This [copier](https://copier.readthedocs.io/) template allows for the quick creation of a repo for hyperparameter search when using one of the synthesis methods from [plenoptic](https://docs.plenoptic.org).

For now, this assumes that you are synthesizing images (which matters because of how they are saved to disk). If this is not the case for you, open an issue and let us know!

- Can refer to previous stuff: model can refer to image, etc
- from scripts, choices will be non-private functions
- Explain about status plot, can be any number, must only require synth object and return figure to save
- add note about UV_PROJECT_ENVIRONMENT and resharing environments
- write how image, initial_image can also accept paths (but this won't show up in help string)

## TODO
- write create_html.py, allow user to specify what image to plot
- update param_questions.yml helps
- use `_message_after_copy` to print out additional info after template is generated
- use ruff on generated files to check for syntax errors? as part of tasks (optional)
- add tests
  - use ruff in tests

## Custom scripts
