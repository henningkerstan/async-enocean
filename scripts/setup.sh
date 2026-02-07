#!/usr/bin/env bash
# Setup the Python virtual environment and install dependencies

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up virtual environment in $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment"
source "$VENV_DIR/bin/activate"

echo "Upgrading pip"
python3 -m pip install --upgrade pip

echo "Installing required packages"

if [ -f "pyproject.toml" ]; then
    pip install -e .
fi

echo "Installing pre-commit & setting up git hooks"
pip install pre-commit
pre-commit install

echo "Setup complete. To activate the virtual environment at a later time, run 'source $VENV_DIR/bin/activate'. To deactivate, run 'deactivate'."