# Hyperparameter Search Template

This [copier](https://copier.readthedocs.io/) template allows for the quick creation of a repo for hyperparameter search when using one of the synthesis methods from [plenoptic](https://docs.plenoptic.org).

For now, this assumes that you are synthesizing images (which matters because of how they are saved to disk). If this is not the case for you, open an issue and let us know!

- Can refer to previous stuff: model can refer to image, etc
- from scripts, choices will be non-private functions

## TODO
write first pass at synthesize.py, write_dispatch.py, create_html.py
  - for create_html.py, allow user to specify what image to plot
  - have a separate synthesize.py that allows for two-stage synthesis
- finish param_questions.yml
- add something about separate (give us path) or default plot (synthesis_status)
  - will always save plot of synthesized image itself
- add flag for animate, in which case we use store_progress and ask for n_frames?
- use `_message_after_copy` to print out additional info after template is generated
- how to handle optimizer/scheduler kwargs? shouldn't do product of them
    - maybe if they enter more than one optimizer, have them do it separately?

## Custom scripts
