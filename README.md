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

- .h files without .m
- .m files without .h

- Tree of types that use a starting type

- List unused types

- List
  - view controller types
    - graph of view controllers instanciations
  - view model types
  - service types
  - localizable keys not used

