# Contributing

Thanks for helping improve Chordbook.

## Ground Rules

- Keep changes focused and small.
- Preserve spacing/alignment behavior for chord text.
- Do not commit private song libraries, credentials, or local DB files.

## Development Setup

See [INSTALL.md](INSTALL.md) for environment setup.

## Suggested Workflow

1. Create a branch from `main`.
2. Make your change with tests or verification notes.
3. Run a local sanity check:

```bash
python -m compileall app wsgi.py
```

4. Update docs when behavior changes.
5. Open a pull request with a clear summary and screenshots for UI changes.

## Pull Request Checklist

- [ ] Change is scoped and documented.
- [ ] No secrets or private library content committed.
- [ ] Routes/behavior remain legacy-compatible where expected.
- [ ] Chord text alignment remains intact.

## Reporting Bugs

Please include:

- expected behavior
- actual behavior
- reproduction steps
- route/URL used
- relevant logs (redacted)
