# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Release checklist

- [ ] Verify `FLASK_SECRET_KEY` is configured in deployment.
- [ ] Confirm no private song library content is included in release artifacts.
- [ ] Run CI and ensure all checks pass.
- [ ] Update version tag and release notes.

### Added

- In-browser upload and edit workflow for chord text files.
- Self-hosted editor integration with Emacs keymap support.
- Size limits and safer file validation for content writes.
- Google OAuth login via Authlib (`/login/google`, `/authorize/google`).
- Automatic schema migration adds `google_id` column to the user table on first startup.
- `.env`-based configuration with `python-dotenv` (explicit path so WSGI working directory does not matter).

### Changed

- README rewritten as project and route documentation.
- Installation/setup moved to INSTALL.md.
- Authentication migrated from username/password to Google OAuth.

### Fixed

- Filename normalization regression that appended `.txt` to existing non-`.txt` file names.
