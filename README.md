# IdleReload
Python IDLE extension to reload the currently opened file from disk contents.

[![Tests](https://github.com/CoolCat467/idlereload/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/CoolCat467/idlereload/actions/workflows/tests.yml)
<!-- BADGIE TIME -->

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![code style: black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

<!-- END BADGIE TIME -->

## What does this extension do?
This IDLE extension allows you to reload the currently open file from disk
contents. For example, say you have run an auto-formatter like black on
your code, but you still have an IDLE window open. Regularly, you would
have to close the window and re-open the file to see the changes. This
extension allows you to reload the file's contents from what is saved
on disk without restarting IDLE.

## Installation (Without root permissions)
1) Go to terminal and install with the following command:
```console
pip install idlereload[user]
```

2) Run configuration update/check commands:
```console
idleuserextend; idlereload
```

You should see the following output:
`Config should be good! Config should be good!`.

3) Open IDLE, go to `Options` -> `Configure IDLE` -> `Extensions`.
If everything went well, alongside `ZzDummy` there should be and
option called `idlereload`. This is where you can configure how
idlereload works.

## Installation (Legacy, needs root permission)
1) Go to terminal and install with the following command:
```console
pip install idlereload
```

2) Run configuration update/check commands:
```console
idlereload
```

You will likely see a message saying
`idlereload not in system registered extensions!`. Run the command
it tells you to add idlereload to your system's IDLE extension config file.

3) Run command `idlereload` again after modifying the system extension
configuration file. This time, you should see the following output:
`Config should be good!`.
4) Open IDLE, go to `Options` -> `Configure IDLE` -> `Extensions`.
If everything went well, alongside `ZzDummy` there should be and
option called `idlereload`. This is where you can configure how
idlereload works.


### Future Work
Maybe add support for asynchronously checking if we need to reload and
display a header message like code context that disk version has changed.
