# Python Package Newsletter

Automated service that builds a Markdown newsletter summarizing important changes for popular Python packages. It can combine a custom package list with the top packages from PyPI, detect notable releases, and commit the generated newsletter back to the repository via GitHub Actions.

## Features
- Multiple selection modes: custom only, custom + top PyPI, or top PyPI only.
- Pulls release metadata from PyPI and GitHub releases.
- Scores releases for importance based on version bumps and keywords (breaking, deprecation, security).
- Generates Markdown newsletters in `newsletters/` and persists progress in `state.json` to avoid duplicate reporting.
- Scheduled GitHub Actions workflow to run weekly and push updates.

## Configuration
Create a `config.yaml` based on `config.example.yaml`:

```yaml
mode: custom_and_top          # custom_only | custom_and_top | top_only
top_n: 20                     # number of top PyPI packages to include
custom_packages:
  - pandas
  - numpy
  - fastapi
newsletter_output_dir: newsletters
state_file: state.json
since_days: 30                # how far back to look on first run
min_importance_score: 3.0     # minimum score to include a release
```

- **mode**: controls how packages are chosen.
- **top_n**: number of popular packages to pull from the PyPI popularity dataset.
- **custom_packages**: packages you always want tracked.
- **since_days**: window used on first run when no state exists.
- **min_importance_score**: importance threshold for newsletter inclusion.

## Running locally
1. Install dependencies:
   ```bash
   pip install .
   ```
2. Copy the example config:
   ```bash
   cp config.example.yaml config.yaml
   ```
3. Run the pipeline:
   ```bash
   python -m newsletter run-once --config config.yaml
   ```

Set `GITHUB_TOKEN` in your environment to increase GitHub API rate limits and fetch private releases if needed.

## GitHub Actions workflow
The workflow `.github/workflows/newsletter.yml` runs weekly (Monday 08:00 UTC) or on manual dispatch:
- Installs dependencies
- Runs the pipeline
- Commits `newsletters/` and `state.json` if changed using the GitHub Actions token

Adjust the cron schedule or Python version in the workflow as desired.

## How it works
1. **Select packages** using the configured mode. Top packages come from `https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json`.
2. **Fetch releases** from PyPI and GitHub. The code attempts to infer the GitHub repository from PyPI project URLs.
3. **Score importance** using semantic version bumps and keyword detection for breaking changes, deprecations, and security.
4. **Render newsletter** grouped into sections for breaking/major changes, deprecations, security, and other updates.
5. **Update state** to remember the latest processed version per package.

## Repository layout
- `config.example.yaml` – sample configuration.
- `state.json` – persisted state (created/updated by the pipeline).
- `newsletters/` – generated Markdown newsletters (created at runtime).
- `src/newsletter/` – Python source code (clients, filtering, rendering, CLI).
- `.github/workflows/newsletter.yml` – scheduled workflow.

## Troubleshooting
- Missing config or invalid mode will cause the CLI to exit with an error.
- API failures for specific packages are logged; the run continues for remaining packages.
- If you see GitHub API rate-limit warnings, provide a `GITHUB_TOKEN` with sufficient scope.
