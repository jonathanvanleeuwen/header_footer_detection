# header_footer_detection
A Python library with modern CI/CD setup.

## Features
* Automated testing on PR using GitHub Actions
* Pre-commit hooks for code quality (ruff, isort, trailing whitespace, etc.)
* Semantic release using GitHub Actions
* Automatic code coverage report in README
* Automatic wheel build and GitHub Release publishing
* Modern Python packaging with pyproject.toml

*Notes*
Workflows trigger when a branch is merged into main!
To install, please follow all the instructions in this readme.
The workflows require a PAT set as secret (see further down for instructions)
See the notes on how to create semantic releases at the bottom of the README.

If you followed all the steps, whenever a PR is merged into `main`, the workflows are triggered and should:
* Run pre-commit checks (fail fast on code quality issues)
* Ensure that tests pass (before merge)
* Create a code coverage report and commit that to the bottom of the README
* Create a semantic release (if you follow the semantic release pattern) and automatically update the version number of your code
* Build a wheel and publish it as a GitHub Release asset


# Installation

## Option 1: Install from Private GitHub Release (Recommended)
Since this is a private repository, you need to authenticate with a GitHub Personal Access Token (PAT).

### Configure git credentials (more secure, recommended)
This method doesn't expose your token in command history:

```bash
# Store credentials in git (one-time setup)
git config --global credential.helper store

# Then install normally - git will prompt for credentials once
pip install "git+https://github.com/jonathanvanleeuwen/header_footer_detection.git@VERSION"
# When prompted: username = your GitHub username, password = your PAT
```

### Step 1: Create a Personal Access Token (one-time setup)

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Give it a descriptive name (e.g., `header_footer_detection-install`)
4. Select the **`repo`** scope (required for private repositories)
5. Click **"Generate token"**
6. **Copy the token immediately** - you won't be able to see it again!

### Step 2: Install the package

```bash
# Replace YOUR_TOKEN with your actual token and VERSION with the desired version (e.g., v1.0.0)
pip install "git+https://YOUR_TOKEN@github.com/jonathanvanleeuwen/header_footer_detection.git@VERSION"

# Install the latest version (main branch):
pip install "git+https://YOUR_TOKEN@github.com/jonathanvanleeuwen/header_footer_detection.git"
```

### Using uv (faster alternative to pip)

```bash
uv pip install "git+https://YOUR_TOKEN@github.com/jonathanvanleeuwen/header_footer_detection.git@v1.0.0"
```

## Option 2: Install from Wheel File in Repository

The latest wheel files are also committed to the `dist/` directory in the repository. After cloning:

```bash
# Clone the repository first
git clone https://github.com/jonathanvanleeuwen/header_footer_detection.git

# Install the wheel file directly
pip install header_footer_detection/dist/header_footer_detection-1.0.0-py3-none-any.whl
```

> **Note:** Replace the version number with the actual version in the `dist/` directory.

## Option 3: Install from Source (Clone Repository)

```bash
# Clone the repository
git clone https://github.com/jonathanvanleeuwen/header_footer_detection.git
cd header_footer_detection

# Install using pip
pip install .

# Or install in editable/development mode with dev dependencies
pip install -e ".[dev]"
```

## Option 4: Add to requirements.txt or pyproject.toml

**In requirements.txt:**

```txt
header_footer_detection @ git+https://github.com/jonathanvanleeuwen/header_footer_detection.git@v1.0.0
```

**In pyproject.toml (for projects using PEP 621):**

```toml
[project]
dependencies = [
    "header_footer_detection @ git+https://github.com/jonathanvanleeuwen/header_footer_detection.git@v1.0.0",
]
```

## Building a Wheel File Locally

```bash
pip install build
python -m build --wheel
# The wheel will be created in the dist/ directory
```


# Development Setup

1. Create new virtual environment
   ```bash
   python -m venv .venv
   ```
2. Activate the environment and install library with dev dependencies
   ```bash
   pip install -e ".[dev]"
   ```
3. Install pre-commit hooks
   ```bash
   pip install pre-commit
   pre-commit install
   ```
4. Run pre-commit on all files to ensure everything is properly set up
   ```bash
   pre-commit run --all-files
   ```
5. Check proper install by running tests
   ```bash
   pytest
   ```


# GitHub Repository Setup

Complete these steps in order to enable the CI/CD pipeline.

## Step 1: Create the Release Token (PAT)

The workflow needs a Personal Access Token to push to the protected `main` branch.

### Create a Fine-Grained PAT (Recommended - More Secure)

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens](https://github.com/settings/tokens?type=beta)
2. Click **"Generate new token"**
3. Configure the token:
   - **Token name:** `RELEASE_TOKEN_HEADER_FOOTER_DETECTION` (or similar descriptive name)
   - **Expiration:** Choose an appropriate duration (recommend 90 days, set a reminder to rotate)
   - **Repository access:** Select "Only select repositories" → choose this repository
   - **Permissions:**
     - **Contents:** Read and write (for pushing commits and tags)
     - **Metadata:** Read-only (automatically selected)
4. Click **"Generate token"**
5. **Copy the token immediately** - you won't see it again!

### Alternative: Classic PAT (Simpler but Broader Access)

If fine-grained tokens don't work for your use case:

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Configure:
   - **Note:** `RELEASE_TOKEN_HEADER_FOOTER_DETECTION`
   - **Expiration:** Set an appropriate duration
   - **Scopes:** Select `repo` (full control of private repositories)
4. Click **"Generate token"** and copy it

## Step 2: Add the Token as a Repository Secret

1. Go to your repository on GitHub
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **"New repository secret"**
4. Configure:
   - **Name:** `RELEASE_TOKEN`
   - **Secret:** Paste your copied PAT
5. Click **"Add secret"**

## Step 3: Configure Branch Protection with Rulesets

GitHub Rulesets provide modern, flexible branch protection. The PAT allows the workflow to bypass these rules while humans must go through PRs.

1. Go to your repository → **Settings → Rules → Rulesets**
2. Click **"New ruleset"** → **"New branch ruleset"**
3. Configure the ruleset:
   - **Ruleset name:** `Protect main`
   - **Enforcement status:** Active
   - **Target branches:** Click "Add target" → "Include by pattern" → enter `main`

4. Enable these rules:
   - ✅ **Restrict deletions** - Prevent branch deletion
   - ✅ **Require a pull request before merging**
     - Required approvals: `1` (or more)
     - ✅ Dismiss stale pull request approvals when new commits are pushed
     - ✅ Require conversation resolution before merging
   - ✅ **Require status checks to pass**
     - ✅ Require branches to be up to date before merging
     - Add status checks: `test` (from python-app.yml), `lint` (from python-app.yml)
   - ✅ **Block force pushes**

5. Click **"Create"**


## Security Model

This setup provides security through multiple layers:

| Protection | What it prevents |
|------------|------------------|
| **CODEOWNERS** | Requires your approval for any workflow changes |
| **Required PRs** | No direct pushes to main (humans must use PRs) |
| **Required reviews** | At least one approval needed for every change |
| **Status checks** | Tests must pass before merge |
| **PAT as secret** | Token only accessible to workflows, not forks |

**Why is the PAT safe?**
- The PAT is stored as a secret, never exposed in logs (GitHub auto-masks it)
- Forks cannot access repository secrets
- Any attempt to modify workflows to steal the PAT requires your explicit approval via CODEOWNERS
- The PAT can only push; it cannot change branch protection rules


# Semantic Release

https://python-semantic-release.readthedocs.io/en/latest/

The workflows are triggered when you merge into main!

When committing, use the following format for your commit message:

**Patch release** (1.0.0 → 1.0.1):
```
fix: your commit message
```

**Minor release** (1.0.0 → 1.1.0):
```
feat: your commit message
```

**Major/breaking release** (1.0.0 → 2.0.0):
```
feat: your commit message

BREAKING CHANGE: description of breaking change
```


# Coverage Report
<!-- Pytest Coverage Comment:Begin -->
<a href="https://github.com/jonathanvanleeuwen/header_footer_detection/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-100%25-brightgreen.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th></tr><tbody><tr><td colspan="4"><b>src/header_footer_detection</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/header_footer_detection/blob/main/src/header_footer_detection/__init__.py">__init__.py</a></td><td>1</td><td>0</td><td>100%</td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/header_footer_detection/blob/main/src/header_footer_detection/basic_function.py">basic_function.py</a></td><td>4</td><td>0</td><td>100%</td></tr><tr><td><b>TOTAL</b></td><td><b>5</b></td><td><b>0</b></td><td><b>100%</b></td></tr></tbody></table></details>
<!-- Pytest Coverage Comment:End -->
