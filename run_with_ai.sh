#!/bin/bash

# Script to run the application with AI features enabled

# Checking if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    # Set up AI features
    echo "Setting up AI features..."
    python setup_ai.py
else
    # Activate virtual environment
    source venv/bin/activate
fi

# Make sure database is initialized
if [ ! -f "notes_app.db" ]; then
    echo "Initializing database..."
    python initialize_db.py
fi

# Set environment variable to enable AI features
export ENABLE_AI_FEATURES=true

# Run the application
echo "Starting application with AI features enabled..."
python run.py