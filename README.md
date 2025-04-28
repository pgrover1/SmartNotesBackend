# Notes API Backend with MongoDB Support

A FastAPI backend for a notes application with AI-powered features and MongoDB integration.

## Features

- RESTful API for notes management (CRUD operations)
- Category management for notes
- Database flexibility:
  - MongoDB support
  - SQLAlchemy/SQL database fallback
- AI-powered features:
  - Automatic note summarization for longer notes
  - Sentiment analysis of note content
  - Category suggestion based on note content
  - Natural language queries for searching notes
  - Automatic categorization of notes

## AI Features

### Automatic Summarization
The backend generates concise summaries for longer notes using the BART-large-CNN model from Facebook. When a note is created or updated, if its content is longer than 200 characters, the system will automatically generate a summary.

### Sentiment Analysis
Each note's content is analyzed to determine its emotional tone (Positive, Negative, or Neutral) using DistilBERT fine-tuned on the SST-2 dataset. The sentiment is stored with the note and returned in API responses.

### Automatic Categorization
The system can automatically suggest and assign categories to notes based on their content using:
1. Zero-shot classification with BART-large-MNLI model
2. Semantic similarity with sentence embeddings (fallback method)

Autocategorization happens in two ways:
- When creating a note without specifying categories
- Through a dedicated endpoint that can categorize all uncategorized notes

### Natural Language Queries
Users can search for notes using natural language queries like "Find my meeting notes from last Monday" or "Show me all notes about programming in the Work category". The system extracts search parameters from these natural language inputs.

## Technology Stack

- **Framework**: FastAPI
- **Database Options**: 
  - MongoDB with PyMongo
  - SQLAlchemy with SQLite/PostgreSQL
- **AI Models**: Hugging Face Transformers
  - Summarization: facebook/bart-large-cnn
  - Sentiment Analysis: distilbert-base-uncased-finetuned-sst-2-english
  - Embeddings: sentence-transformers/all-MiniLM-L6-v2
  - Zero-shot Classification: facebook/bart-large-mnli
- **Testing**: Pytest

## Project Structure

```
app/
├── api/               - API routes and endpoints
├── core/              - Core application settings
├── db/                - Database configuration
├── models/            - SQLAlchemy database models
├── repositories/      - Data access layer
├── schemas/           - Pydantic models for data validation
├── services/          - Business logic layer
│   └── ai.py          - AI-powered features
└── tests/             - Test cases
    ├── integration/   - API integration tests
    └── unit/          - Unit tests
```

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/notes-api.git
cd notes-api
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install basic dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit the `.env` file to configure the database:

```
# For MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=notes_app
USE_MONGODB=true

# For SQL database
DATABASE_URL=sqlite:///./notes_app.db
USE_MONGODB=false
```

5. Initialize the database:

```bash
python initialize_db.py
```

### Setting up AI Features (Optional)

To enable the AI-powered features, run the setup script:

```bash
python setup_ai.py
```

This script will:
1. Install the necessary AI dependencies (transformers, torch, etc.)
2. Download the required AI models from Hugging Face

**Note:** The AI models require approximately 2-3GB of disk space. For faster startup, models are cached locally after the first download.

If you prefer to run without AI features, you can disable them in your `.env` file:

```
ENABLE_AI_FEATURES=false
```

When AI features are disabled, the app will use simple fallback implementations:
- Summarization: Returns the first 100 characters of the text
- Sentiment Analysis: Always returns "Neutral"
- Category Suggestion: No automatic suggestions

### Running the Application

Start the development server:

```bash
python run.py
```

The API will be available at http://localhost:8000

### API Documentation

FastAPI automatically generates API documentation with Swagger UI and ReDoc:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```

## Deployment

The application can be deployed to any platform that supports Python applications.

### Example: Deploying to Render

1. Create a new Web Service in Render
2. Connect your GitHub repository
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from your .env file

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
