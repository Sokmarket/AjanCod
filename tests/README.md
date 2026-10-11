# Test suite

Run from the repository root:

```bash
python -m unittest discover -s tests -v
python -m compileall -q aegis tests
```

The suite uses standard-library `unittest`. Network tests are mocked/not performed, and screen permission tests deliberately avoid capturing an actual desktop. The tests do not claim to validate remote providers, the Android screen capture mechanism, or container-grade isolation.
