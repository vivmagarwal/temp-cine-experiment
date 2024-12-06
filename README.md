# Langchain RAG System

A Retrieval Augmented Generation (RAG) system built with FastAPI, Langchain, and OpenAI, featuring a user-friendly web interface.

## Features

- Upload and process PDF and text documents
- Ask questions about your documents
- Get AI-generated answers with source references
- Clean and intuitive user interface
- Efficient document chunking and retrieval
- Support for multiple file uploads

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd langchain-rag
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
```bash
# Create a .env file (this will be ignored by git)
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your-api-key-here
```

5. Run the application:
```bash
uvicorn main:app --reload
```

6. Open in your browser:
```
http://localhost:8000/static/index.html
```

## Documentation

For detailed information about the system architecture, implementation details, and a step-by-step guide for beginners, please see our [Development Guide](develop.md).

## System Requirements

- Python 3.10 or higher
- OpenAI API key
- Modern web browser
- Internet connection for API access

## Project Structure

```
langchain-rag/
├── main.py              # FastAPI backend
├── requirements.txt     # Python dependencies
├── .env.example        # Example environment variables
├── .gitignore          # Git ignore configuration
├── develop.md          # Detailed development guide
└── static/             # Frontend files
    ├── index.html      # Main webpage
    ├── styles.css      # Styling
    └── script.js       # Frontend logic
```

## Development Notes

### Environment Variables
- The `.env` file contains sensitive information and is not tracked by git
- Use `.env.example` as a template to create your own `.env` file
- Never commit API keys or sensitive data to version control

### Git Configuration
- `.gitignore` is set up to exclude:
  - Environment files (.env)
  - Python cache files
  - Virtual environment directories
  - Vector store data (chroma_db/)
  - System and IDE files
  - Logs

### Best Practices
1. Always use a virtual environment
2. Keep sensitive data in .env file
3. Update .env.example when adding new environment variables
4. Regularly update dependencies in requirements.txt

## License

MIT License - feel free to use this project for learning and development.
