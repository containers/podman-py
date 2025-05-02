# How to contribute

Thank you in your interest in the podman-py project.  We need your help to make
it successful.

You may also want to look at:

- [podman](https://github.com/containers/podman)
- [podman Reference](https://podman.readthedocs.io/en/latest/Reference.html)

## Reporting Issues

Before reporting an issue, check our backlog of open issues to see if someone
else has already reported it. If so, feel free to add your scenario, or
additional information, to the discussion. Or simply "subscribe" to it to be
notified when it is updated.

If you find a new issue with the project we'd love to hear about it! The most
important aspect of a bug report is that it includes enough information for us
to reproduce it. So, please include as much detail as possible and try to
remove the extra stuff that doesn't really relate to the issue itself. The
easier it is for us to reproduce it, the faster it'll be fixed!

Please don't include any private/sensitive information in your issue!

## Tools we use

- Python >= 3.9
- [pre-commit](https://pre-commit.com/)
- [ruff](https://docs.astral.sh/ruff/)
- [tox](https://tox.readthedocs.io/en/latest/)
- You may need to use [virtualenv](https://virtualenv.pypa.io/en/latest/) to
  support Python 3.6

## Testing

Depending on the size of your PR we will expect at a minimum unit tests.
Code will not be merged if unit test coverage drops below 85%.
Integration tests would be required for large changes (TBD).

Run unit tests and get coverage report:

```
pip install tox
tox -e coverage
```

#### Advanced testing

Always prefer to run `tox` directly, even when you want to run a specific test or scenario.
Instead of running `pytest` directly, you should run:

```
tox -e py -- podman/tests/integration/test_container_create.py -k test_container_directory_volume_mount
```

If you'd like to test against a specific `tox` environment you can do:

```
tox -e py12 -- podman/tests/integration/test_container_create.py -k test_container_directory_volume_mount
```

Pass pytest options after `--`.

#### Testing future features

Since `podman-py` follows stable releases of `podman`, tests are thought to be run against
libpod's versions that are commonly installed in the distributions. Tests can be versioned,
but preferably they should not. Occasionally, upstream can diverge and have features that
are not included in a specific version of libpod, or that will be included eventually.
To run a test against such changes, you need to have
[podman-next](https://copr.fedorainfracloud.org/coprs/rhcontainerbot/podman-next) installed.
Then, you need to mark the test as `@pytest.mark.pnext`. Marked tests willbe excluded from the
runs, unless you pass `--pnext` as a cli option.
Preferably, this should be a rare case and it's better to use this marker as a temporary solution,
with the goal of removing the marker within few PRs.

To run these tests use:

```
tox -e py -- --pnext -m pnext podman/tests/integration/test_container_create.py -k test_container_mounts_without_rw_as_default
```

The option `--pnext` **enables** the tests with the `pnext` pytest marker, and `-m pnext` will run
the marked tests **only**.

## Submitting changes

- Create a github pull request (PR)
- We expect a short summary followed by a longer description of why you are
  making these change(s).
- Include the header `Signed-off-by: Git Hub User <user@github.com>` in your PR
  description/commit message with your name.
  - Setting `user.name` and `user.email` in your git configs allows you to then
    use `git commit -s`. Let git do the work of signing your commits.

## Where to find other contributors

- For general questions and discussion, please use the IRC #podman channel on
  irc.libera.chat.
- For discussions around issues/bugs and features, you can use the
  GitHub [issues](https://github.com/containers/podman-py/issues) and
  [PRs](https://github.com/containers/podman-py/pulls) tracking system.

## Coding conventions

- Formatting and linting are incorporated using [ruff](https://docs.astral.sh/ruff/).
- If you use [pre-commit](https://pre-commit.com/) the checks will run automatically when you commit some changes
- If you prefer to run the ckecks with pre-commit, use `pre-commit run -a` to run the pre-commit checks for you.
- If you'd like to see what's happening with the checks you can run the [linter](https://docs.astral.sh/ruff/linter/)
  and [formatter](https://docs.astral.sh/ruff/formatter/) separately with `ruff check --diff` and `ruff format --diff`
- Checks need to pass pylint
  - exceptions are possible, but you will need to make a good argument
- Use spaces not tabs for indentation
- This is open source software. Consider the people who will read your code,
  and make it look nice for them. It's sort of like driving a car: Perhaps
  you love doing donuts when you're alone, but with passengers the goal is to
  make the ride as smooth as possible.
- Use Google style python [docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
  - A general exception is made for kwargs where we use the Sphinx extension of adding a section
      "Keyword Arguments" and documenting the accepted keyword arguments, their type and usage.
      Example: kwarg1 (int): Description of kwarg1

Again, thank you for your interest and participation.
Jhon Honce `<jhonce at redhat dot com>`

Thanks to Carl Tashian, Participatory Politics Foundation for his fine
CONTRIBUTING.md example.
