# Retained initial failures

- `python314-default-start-method.log`: the initial real Docker run had one failed CPU throttling probe. Python 3.14's forkserver default could not import the function defined in `python -c`; child processes did not perform the intended load. The corrected test explicitly selects fork, requires three successful child exits and then requires actual kernel throttling. All 16 final real Docker tests pass; production worker code does not use multiprocessing.
- `missing-checkout-pythonpath.log`: an incorrectly invoked coordination unit command omitted the sibling checkout PYTHONPATH and failed four module imports. The documented checkout configuration passes all 20 tests. This is an invocation failure, not evidence against the worker.

Neither failure is counted as a successful verification. Final logs are separate.
