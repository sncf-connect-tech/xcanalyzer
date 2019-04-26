# XC Analyzer project

This this a project written in Python 3 which lets you analyze Xcode projects giveing you metrics, generating graphs. It helps finding dead code and legacy code from your project.

## Getting started

To start working this this project, git clone the repository, then run:

        ./install.sh

Then activate the Python 3 virtual environment by:

        source venv/bin/activate

## Testing

To launch the tests, activate the venv then type:

        python -m unittest

## Cleanup

To clean the project, runs:

        ./cleanup.sh

## Work in progress

The goals to reach:

- List obj-c types:
  - .h files from target
  - .h files from project
  - enum
  - global constants
  - protocols

- .h files not present in header files

- .h files without .m
- .m files without .h

- Proportion of types Swift vs Obj-C

- List
  - view controller types
  - view model types
  - service types