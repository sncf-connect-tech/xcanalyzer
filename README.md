# XC Analyzer project

This this a project written in Python 3 which lets you analyze Xcode projects giveing you metrics, generating graphs. It helps finding dead code and legacy code from your project.

## Getting started

To start working this this project, git clone the repository, then run:

        ./install.sh

Then activate the Python 3 virtual environment by:

        source venv/bin/activate

## Testing

To launch the tests, activate the ven then type:

        python -m unittest

## Cleanup

To clean the project, runs:

        ./cleanup.sh

## Work in progress

The goals to reach:

- find groups without folder
- find groups relative to project
- find files not used in project
- find files used in several targets
- find files with mismatches between xcode path and file path (See `SampleiOSApp` > `Ghost.swift`)