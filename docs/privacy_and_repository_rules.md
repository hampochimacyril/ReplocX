# Privacy and Repository Rules

## Required Repository Posture

This application, its datasets, and generated artifacts must remain private.

- Never create a public repository.
- Never publish raw analytical data, licensed data, credentials, tokens, or API keys.
- Never push until the exact private GitHub repository URL is confirmed with the owner,
  **Chima Cyril Hampo**.
- Confirm whether the target is a new private repository or a branch and folder inside
  an existing private repository.
- Use a scoped branch such as `feature/location-representation-explorer`.
- Open a draft pull request only after a private push is confirmed.

## Commit Scope

Commit the application folder and intentionally modified documentation only. The
application `.gitignore` excludes common local artifacts, credentials, raw data,
archives, spreadsheets, manifests with absolute paths, and test output.

Before committing:

```bash
git status --short
git diff --cached --stat
git diff --cached -- .env
```

Review every staged path. Do not add `04_Analysis/location_selection/data/raw/`.

## Environment Variables

Use `.env.example` as documentation. Store real local values in `.env`, which is
ignored. This application does not require credentials for local use.

## Screenshots

Screenshots for a private draft pull request are allowed only after reviewing them for
restricted data, local filesystem paths, and identifying details.

