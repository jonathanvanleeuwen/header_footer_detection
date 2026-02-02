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
4. Check proper install by running tests
   ```bash
   pytest
   ```


# Protect your main branch
To ensure that only accepted code is put on main, make sure that all changes to main happen using a PR and at least 1
reviewer.
You also want to ensure that no tests are allowed to fail when merging

## Branch Protection
### Ensure branch protection for PRs
In the repo on github go to:
* Settings -> Branches and click "add rule"
* Enable:
  * Require a pull request before merging
    * Require approvals (set the number of required reviewers)
  * Require status checks to pass before merging
    * Require branches to be up to date before merging
  * Require conversation resolution before merging

### Ensure workflow protection
this is not entirely fool proof and secure, but better than nothing, in the repo on github go to:
* Settings -> Actions -> General
* Enable:
  * Allow [owner], and select non-[owner], actions and reusable workflows
* In "Allow specified actions and reusable workflows" add the following string:
  * actions/checkout@v4,
actions/setup-python@v5,
relekang/python-semantic-release@master,
MishaKav/pytest-coverage-comment@main,
actions-js/push@master,
softprops/action-gh-release@v2,

## Create a semantic release PAT and Secrets for the workflow actions
For the semantic release to be able to push new version to the protected branch you need to
create a PAT with the proper permissions and save the pat as a secret in the repo.

### Create PAT
* Click Top right image -> settings
* Developer settings
* Personal access tokens -> Tokens (classic)
* Generate new token -> generate new token (classic)

Settings:
* Note: Semantic release
* Enable:
  * Repo (and all the repo options)
  * workflow
  * admin:repo_hook
* Generate token

Now copy the token (you need this in the next step)

### Create secret
Go to your repo, then:
* Settings -> Secrets -> Actions
* New repository secret
  * Name: SEM_RELEASE
  * Secret: [Your copied PAT token]

The name needs to be the same, as this is what is used in ".github\workflows\semantic-release.yml"


# Semantic release
https://python-semantic-release.readthedocs.io/en/latest/

The workflows are triggered when you merge into main!!

When committing use the following format for your commit message:
* patch:
  `fix: commit message`
* minor:
  `feat: commit message`
* major/breaking (add the breaking change on the third line of the message):
    ```
    feat: commit message

    BREAKING CHANGE: commit message
    ```

# Coverage report
<!-- Pytest Coverage Comment:Begin -->
<!-- Pytest Coverage Comment:End -->
