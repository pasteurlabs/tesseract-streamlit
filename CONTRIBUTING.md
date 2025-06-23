# Contributing to Tesseract Streamlit

Tesseract Streamlit is an open-source project and, as such, we welcome contributions
from developers, engineers, scientists, and end-users in general. Contributions
are what make the open source community such an amazing place to learn,
inspire, and create. Any contributions you make are greatly appreciated.


## Code of Conduct

Ensure your contributions adhere to the [Code of Conduct](CODE_OF_CONDUCT.md).


## Feedback

Constructive feedback is very welcome. We are interested in hearing from you!

In the case things aren't working as expected, or the documentation is lacking,
please [file a bug
report](https://github.com/pasteurlabs/tesseract-streamlit/issues/new?template=BUG-REPORT.yml).

In the case you want to suggest a new feature, please file a new [feature
request](https://github.com/pasteurlabs/tesseract-streamlit/issues/new?template=FEATURE-REQUEST.yml).
In particular, we recommend you open an issue before contributing code in a
pull request. This allows all parties to talk things over before jumping into
action, and increase the likelihood of pull requests getting merged.

In case you have general questions or feedback, need support from the
community, or have a cool demo to share, start a thread in our [Discourse
Forum](https://si-tesseract.discourse.group/). We use GitHub Issues for bug
reports and feature requests only.


## Documentation

Tesseract Streamlit documentation is kept under the `docs/` directory of the repository,
written in Markdown and using Sphinx to generate the final HTMLs. Fixes and
enhancements to the documentation should be submitted as pull requests, we
treat the same as code contributions.

To build the documentation locally, install the documentation dependencies in
addition to the project itself, then run `make html`:

```console
$ . venv/bin/activate
$ pip install -e .[dev]
$ pip install -r docs/requirements.txt
$ cd docs
$ make html
```

The resulting HTMLs are in `docs/build/html/`.

Contributions in the form of tutorials, examples, demos, blog posts (including
those posted elsewhere already) are best highlighted and celebrated in the
[Discourse Forum](https://si-tesseract.discourse.group/).


## Code

Tesseract Streamlit is developed under the [Apache 2.0](LICENSE) license. By contributing
to the Tesseract Streamlit project you agree that your code contributions are governed by
this license. We require you to sign our [Contributor License
Agreement](https://github.com/pasteurlabs/pasteur-oss-cla/blob/main/README.md)
to state so.

Package source code is kept under the `tesseract_streamlit/` directory, which
has the following structure:

```
__init__.py
_version.py
cli.py
parse.py
templates
└── template.j2
```

`__init__.py` is used solely for exporting the public API, including the
version of `tesseract-streamlit`.
`_version.py` handles versioning logic, and should generally be left alone.

There are three files of interest for Tesseract Streamlit:

1. `parse.py`: provides routines and data structures to parse and extract the
   relevant information for the Streamlit web UI
2. `templates/template.j2`: Jinja template which takes an injection of
   Tesseract OpenAPI Specification data, formatted in `parse.py`, and produces
   a Streamlit web-app
3. `cli.py`: calls routines from `parse.py`, injects the result into
   `templates/template.j2`, and provides a CLI entrypoint via `click` for users

These three files comprise the functionality of `tesseract-streamlit`.

### Local development setup

Make sure you have [Docker installed](https://docs.docker.com/engine/install/)
on your machine and you can run `docker` commands via your user. After that,
clone the repository, install the dependencies, and setup pre-commit hooks:

```console
$ git clone git@github.com:pasteurlabs/tesseract-streamlit.git
$ cd tesseract-streamlit
$ python -m venv venv
$ . venv/bin/activate
$ pip install -e ".[dev]"
$ pre-commit install
```

### Tests

This project uses the pytest framework for all tests. New code should be
covered by new or existing tests.

To run the tests simply run `pytest` in the root of the project. This will run
the entire test suite, including the end-to-end tests that take quite a while
to finish. Instead, you can run the tests separately:

```console
$ pytest --skip-endtoend
$ pytest --always-run-endtoend tests/endtoend_tests
```

### GitHub workflow

This project uses Git for version control and follows a GitHub workflow. To
contribute follow these steps:

1. Fork the project via the GitHub UI.
1. Clone your fork to your machine.
1. Add an upstream remote: `git remote add upstream git@github.com:pasteurlabs/tesseract-streamlit.git`.
1. Create a new branch for your code contribution: `git switch --create my_branch`.
1. Implement your changes.
1. Commit and push to your fork: `git push --set-upstream origin my_branch`.
1. [Open a Pull Request](https://github.com/pasteurlabs/tesseract-streamlit/pulls) with
   your changes.

It is a good practice to merge often from `main` to keep your code up to
date with latest development and minimize merge conflicts:

```console
git fetch upstream
git switch my_branch
git merge upstream/main
```

### Commit and pull request messages guidelines

We follow the [Conventional
Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for all
commits that reach the `main` branch. Each commit is crafted from a pull
request that is squash-merged. The commit title and message comes from the pull
request title and message, respectively. As such, they should be structured
following the specfication.

The title consists of a _type_, and optional _scope_, and a short
_description_: `type[(scope)]: description`. The types we use are:
- `chore`: for changes that affect the build system, external dependencies, or
  general housekeeping.
- `ci`: for changes in the CI.
- `doc`: for documentation only changes.
- `feat`: for a new feature.
- `fix`: for fixing a bug.
- `perf`: for a code change that improves performance.
- `refactor`: for a code change that neither adds a feature nor fixes a bug.
- `security`: for a change that fixes a security issue.
- `test`: for adding new tests or fixing existing ones.

The scopes we use are:
- `cli`: for changes that affect CLI.
- `parse`: for changes that affect the UDF or OAS parsing routines.
- `example`: for changes in the examples.
- `deps`: for changes in the dependencies.

In case there are breaking changes in your code, this should be indicated in
the message either by appending an exclamation mark (`!`) after the type/scope
or by adding a `BREAKING CHANGE:` trailer to the message.


## Versioning

The Tesseract Streamlit project follows [semantic versioning](https://semver.org).


## Release process
(code owners only)

Releases are done via GitHub Actions, which automatically build the release
artifacts and publish them to the [GitHub Releases](https://github.com/pasteurlabs/tesseract-streamlit/releases) page. To create a new release, follow these steps:

1. Make sure the code is in a good state, all tests pass, and the documentation is up to date.
2. Trigger a new release action through the [GitHub UI](https://github.com/pasteurlabs/tesseract-streamlit/actions/workflows/release.yml). This opens a new pull request with the release notes and the version number.
3. Add any additional release notes to the pull request message. They will automatically be included at the top of the release notes.
4. In the meantime, you can add more commits to `main` (and update the release branch) which will trigger re-generation of the changelog and release notes.
5. Once the pull request is ready, merge it into `main`.
6. GitHub Actions will then automatically release the new version. Verify that the release artifacts are correctly built and published.
7. Make an announcement in the [Discourse Forum](https://si-tesseract.discourse.group/) and on social media, if applicable.
