# Testing

## Golden template regression tests

Run the standard-library test suite without installing dependencies:

```sh
python -m unittest discover -s .baseline/tests -v
```

It checks:

- the workspace and every catalogue profile recommend Copilot Chat, not the
  deprecated separate Copilot extension, without duplicate recommendations;
- a fresh bootstrap of every profile emits those recommendations and passes
  `local-doctor`;
- managed live workflows match their catalogue copies;
- action pins and release comments agree across live and catalogue workflows.

The golden template runs these tests in its required `baseline` CI check.
Generated projects skip this template-only step and retain their own test suite.
The template tests stay under `.baseline/tests/` rather than the generated
Python profile's `tests/` directory.

## Project-specific tests

Document the project test pyramid, commands, fixtures, external dependencies, coverage expectations, and how to run integration/e2e checks.
