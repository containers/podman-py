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

- Python 3.6
- [pylint](https://www.pylint.org/)
- [black](https://github.com/psf/black)
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

- Use [black](https://github.com/psf/black) code formatter. If you have tox
  installed, run `tox -e black` to see what changes will be made. You can use
  `tox -e black-format` to update the code formatting prior to committing.
- Pass pylint
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

Again thank you for your interest and participation.
Jhon Honce `<jhonce at redhat dot com>`

Thanks to Carl Tashian, Participatory Politics Foundation for his fine
CONTRIBUTING.md example.
