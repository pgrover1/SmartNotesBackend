#!/usr/bin/env python3
"""
Script to set up AI dependencies and download models for the notes app
"""

import subprocess
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Models to download
MODELS = [
    "facebook/bart-large-cnn",               # for summarization
    "distilbert-base-uncased-finetuned-sst-2-english",  # for sentiment analysis
    "sentence-transformers/all-MiniLM-L6-v2",  # for embeddings
    "facebook/bart-large-mnli",              # for zero-shot classification
]

def install_dependencies():
    """Install required AI dependencies"""
    logger.info("Installing AI dependencies...")
    
    # Dependencies to install
    dependencies = [
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0"
    ]
    
    try:
        # Install dependencies
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + dependencies)
        logger.info("Successfully installed AI dependencies")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def download_models():
    """Download transformer models"""
    logger.info("Downloading models...")
    
    try:
        # Import after installation
        from transformers import AutoTokenizer, AutoModel, pipeline
        
        # Download each model
        for model_name in MODELS:
            logger.info(f"Downloading model: {model_name}")
            
            if "bart" in model_name and "mnli" in model_name:
                # For zero-shot classification
                pipeline("zero-shot-classification", model=model_name)
            elif "bart" in model_name and "cnn" in model_name:
                # For summarization
                pipeline("summarization", model=model_name)
            elif "distilbert" in model_name and "sst-2" in model_name:
                # For sentiment analysis
                pipeline("sentiment-analysis", model=model_name)
            elif "sentence-transformers" in model_name:
                # For embeddings
                pipeline("feature-extraction", model=model_name)
            else:
                # Generic approach
                AutoTokenizer.from_pretrained(model_name)
                AutoModel.from_pretrained(model_name)
            
            logger.info(f"Successfully downloaded model: {model_name}")
        
        logger.info("All models downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to download models: {e}")
        return False

def main():
    """Main function to set up AI environment"""
    logger.info("Starting AI setup...")
    
    # Install dependencies
    if not install_dependencies():
        logger.error("Failed to install dependencies. Exiting.")
        sys.exit(1)
    
    # Download models
    if not download_models():
        logger.error("Failed to download models. Exiting.")
        sys.exit(1)
    
    logger.info("AI setup completed successfully!")

if __name__ == "__main__":
    main()