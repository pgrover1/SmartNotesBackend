# Notes API Backend with MongoDB Support

A FastAPI backend for a notes application with AI-powered features and MongoDB integration.

## Features

- RESTful API for notes management (CRUD operations)
- Category management for notes
- Database flexibility:
  - MongoDB as primary database
  - SQLAlchemy/SQL database fallback
- AI-powered features (on-demand):
  - Note summarization for content with more than 200 words
  - Sentiment analysis of note content (positive/neutral/negative)
  - Category suggestions based on note content
  - Natural language queries for searching notes

## AI Features

### On-Demand Summarization
The backend provides an endpoint to generate concise summaries for notes using OpenAI's GPT-4o model. Summaries are only generated for notes with more than 200 words, as shorter notes don't benefit from summarization. Access this feature via the `/notes/{note_id}/summarize` endpoint.

### Sentiment Analysis
Notes can be analyzed to determine their emotional tone (Positive, Neutral, or Negative) using OpenAI's GPT-4o model. This is available through the dedicated `/notes/{note_id}/sentiment` endpoint.

### Category Suggestion
The system can suggest appropriate categories for notes based on their content using:
1. Zero-shot classification with OpenAI's GPT-4o model
2. Semantic similarity (as a fallback method)

Category suggestions are available on-demand through the `/notes/{note_id}/suggest-category` endpoint.

## Technology Stack

- **Framework**: FastAPI
- **Database**: MongoDB with PyMongo
- **AI Integration**: OpenAI API with GPT-4o
- **Testing**: Pytest
- **Documentation**: Swagger UI/ReDoc (automatic)

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
git clone https://github.com/pgrover1/SmartNotesBackend
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

This script will:
1. Set up and initialize the MongoDB collections
2. Add default categories if none exist

**Note:** For AI features to work, you need to provide an OpenAI API key in your `.env` file:

```
OPENAI_API_KEY=your_api_key_here
```

If you prefer to run without AI features, you can disable them in your `.env` file:

```
ENABLE_AI_FEATURES=false
```

When AI features are disabled, AI-powered endpoints will return appropriate fallbacks:
- Summarization: Returns a message that summarization isn't available
- Sentiment Analysis: Always returns "Neutral"
- Category Suggestion: Returns "Uncategorized" as the default category

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
