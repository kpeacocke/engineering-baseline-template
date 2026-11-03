# Testing

## Golden template regression tests

Install the pinned YAML parser, then run the unittest suite:

```sh
python -m pip install -r .baseline/tests/requirements.txt
python -m unittest discover -s .baseline/tests -v
```

It checks:

- the workspace and every catalogue profile recommend Copilot Chat, not the
  deprecated separate Copilot extension, without duplicate recommendations;
- a fresh bootstrap of every profile emits those recommendations and passes
  `local-doctor`;
- managed live workflows match their catalogue copies;
- action pins and release comments agree across live and catalogue workflows,
  including named steps;
- each Dependabot configuration covers every workflow directory once, groups
  action updates by dependency name and preserves Python dependency updates;
- the version, manifest, installed state and changelog agree.

Negative fixtures reject missing or duplicate directories, absent grouping,
root-only configurations, malformed YAML and mismatched action pins in named steps.

The golden template runs these tests in its required `baseline` CI check.
Generated projects skip this template-only step and retain their own test suite.
The template tests stay under `.baseline/tests/` rather than the generated
Python profile's `tests/` directory.

## Project-specific tests

Document the project test pyramid, commands, fixtures, external dependencies, coverage expectations, and how to run integration/e2e checks.
