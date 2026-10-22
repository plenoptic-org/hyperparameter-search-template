# Hyperparameter Search Template

This [copier](https://copier.readthedocs.io/) template allows for the quick creation of a repo for hyperparameter search when using one of the synthesis methods from [plenoptic](https://docs.plenoptic.org).

For now, this assumes that you are synthesizing images (which matters because of how they are saved to disk). If this is not the case for you, open an issue and let us know!

- Can refer to previous stuff: model can refer to image, etc
- from scripts, choices will be non-private functions
- Explain about status plot, can be any number, must only require synth object and return figure to save
- add note UV_PROJECT_ENVIRONMENT and resharing environments

## TODO
write first pass at synthesize.py, write_dispatch.py, create_html.py
  - for create_html.py, allow user to specify what image to plot
  - have a separate synthesize.py that allows for two-stage synthesis
- update param_questions.yml helps
- use `_message_after_copy` to print out additional info after template is generated
- how to handle optimizer/scheduler kwargs? shouldn't do product of them
    - maybe if they enter more than one optimizer, have them do it separately?

## Custom scripts
