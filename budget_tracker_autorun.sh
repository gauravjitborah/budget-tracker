#!/bin/bash

#Logging the time
LOG_DATETIME="$(date +'%Y-%m-%d %H:%M:%S')"

# Define the path to the virtual environment
VENV_PATH="/Users/gauravjitborah/budget-tracker/virtualEnv"

# Create the virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo "$LOG_DATETIME : Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

# Activate the virtual environment
echo "$LOG_DATETIME : Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Install required Python packages
#pip install -r /Users/gauravjitborah/budget-tracker/requirements.txt

# Run your Python script
echo "$LOG_DATETIME : Running Python script..."
python /Users/gauravjitborah/budget-tracker/tracker-exporter-v8.py

# Deactivate the virtual environment
echo "$LOG_DATETIME : Deactivating virtual environment..."
deactivate