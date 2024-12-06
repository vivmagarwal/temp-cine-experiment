# Building a RAG System: A Step-by-Step Guide for Beginners

## Introduction

This guide will help you build a Retrieval Augmented Generation (RAG) system from scratch. We'll use FastAPI for the backend, vanilla JavaScript for the frontend, and Langchain for document processing and AI integration.

## Project Structure

```
langchain-rag/
├── main.py              # FastAPI backend
├── requirements.txt     # Python dependencies
├── .env                # Environment variables
└── static/             # Frontend files
    ├── index.html      # Main webpage
    ├── styles.css      # Styling
    └── script.js       # Frontend logic
```

## Part 1: Setting Up FastAPI Backend

### Understanding FastAPI Basics

FastAPI is a modern Python web framework. Here's how we use it in `main.py`:

```python
from fastapi import FastAPI
app = FastAPI()

# Basic route example
@app.get("/")
async def read_root():
    return {"status": "RAG system is running"}
```

### API Endpoints Explained

1. **Root Endpoint** (`GET /`):
```python
@app.get("/")
async def read_root():
    return {"status": "RAG system is running"}
```
- Purpose: Health check to verify server is running
- Usage: `curl http://localhost:8000/`

2. **Upload Endpoint** (`POST /upload`):
```python
@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    # Process uploaded files
    documents = []
    for file in files:
        docs = await process_file(file)
        documents.extend(docs)
    
    # Split into chunks and store
    splits = text_splitter.split_documents(documents)
    vector_store.add_documents(splits)
    
    return {
        "message": f"Successfully processed {len(files)} files",
        "chunks_created": len(splits)
    }
```
- Purpose: Handles document uploads
- Accepts: Multiple files (PDF, TXT)
- Returns: Processing status and chunk count
- Usage: `curl -F "files=@document.pdf" http://localhost:8000/upload`

3. **Query Endpoint** (`POST /query`):
```python
@app.post("/query")
async def query(question: str = Form(...)):
    result = qa_chain({"query": question})
    return {
        "answer": result["result"],
        "sources": result["source_documents"]
    }
```
- Purpose: Answers questions about uploaded documents
- Accepts: Question text
- Returns: AI-generated answer with source references
- Usage: `curl -X POST -F "question=What is RAG?" http://localhost:8000/query`

### FastAPI Middleware and Static Files

```python
# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")
```

## Part 2: Document Processing with Langchain

### Setting Up Document Processing

1. **Initialize Components**:
```python
def initialize_langchain():
    global embeddings, vector_store, qa_chain
    
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings()
    
    # Setup vector store
    vector_store = Chroma(
        collection_name="rag_collection",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )
    
    # Create QA chain
    llm = ChatOpenAI(temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(
            search_kwargs={"k": 4}
        ),
        return_source_documents=True
    )
```

2. **Process Files**:
```python
async def process_file(file: UploadFile) -> List[Document]:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        
        # Load and process document
        if suffix == '.pdf':
            loader = PyPDFLoader(temp_file.name)
        else:
            loader = TextLoader(temp_file.name)
            
        docs = loader.load()
        
        # Add metadata
        for i, doc in enumerate(docs):
            doc.metadata.update({
                "file_name": file.filename,
                "page_number": i + 1
            })
        
        return docs
```

## Part 3: Frontend Development

### HTML Structure (`static/index.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG System</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <!-- File Upload Section -->
        <div class="upload-section">
            <h2>Upload Documents</h2>
            <div class="file-upload">
                <input type="file" id="fileInput" multiple>
                <button onclick="uploadFiles()">Upload</button>
            </div>
        </div>

        <!-- Query Section -->
        <div class="query-section">
            <h2>Ask Questions</h2>
            <input type="text" id="questionInput">
            <button onclick="askQuestion()">Ask</button>
            <div id="answer"></div>
            <div id="sources"></div>
        </div>
    </div>
    <script src="script.js"></script>
</body>
</html>
```

### JavaScript Implementation (`static/script.js`)

1. **File Upload**:
```javascript
async function uploadFiles() {
    const files = document.getElementById('fileInput').files;
    const formData = new FormData();
    
    for (let file of files) {
        formData.append('files', file);
    }

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        showStatus(result.message, 'success');
    } catch (error) {
        showStatus('Upload failed: ' + error.message, 'error');
    }
}
```

2. **Question Handling**:
```javascript
async function askQuestion() {
    const question = document.getElementById('questionInput').value;
    const formData = new FormData();
    formData.append('question', question);

    try {
        const response = await fetch('/query', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        displayAnswer(result.answer, result.sources);
    } catch (error) {
        showStatus('Query failed: ' + error.message, 'error');
    }
}
```

## Part 4: Step-by-Step Setup Guide

1. **Create Project Structure**:
```bash
mkdir langchain-rag
cd langchain-rag
mkdir static
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set Environment Variables**:
Create `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

4. **Create Backend Files**:
- Copy `main.py` content
- Understand each endpoint and component

5. **Create Frontend Files**:
- Create and populate `static/index.html`
- Create and populate `static/styles.css`
- Create and populate `static/script.js`

6. **Run the Application**:
```bash
uvicorn main:app --reload
```

7. **Access the Application**:
Open `http://localhost:8000/static/index.html`

## Common Issues and Solutions

1. **PDF Processing Fails**:
- Install PDF dependencies: `pip install "unstructured[pdf]"`
- Ensure PDF is text-based, not scanned

2. **CORS Errors**:
- Check CORS middleware configuration
- Verify frontend URL matches allowed origins

3. **Vector Store Errors**:
- Clear `chroma_db` directory if schema changes
- Check embeddings configuration

## Testing the Application

1. **Upload Test**:
```python
# Test file upload
curl -X POST -F "files=@test.pdf" http://localhost:8000/upload
```

2. **Query Test**:
```python
# Test question answering
curl -X POST -F "question=What is RAG?" http://localhost:8000/query
```

## Next Steps for Learning

1. Study FastAPI:
- Read FastAPI documentation
- Understand async/await in Python
- Learn about dependency injection

2. Explore Langchain:
- Study document loaders
- Understand embeddings
- Learn about different chain types

3. Improve Frontend:
- Add error handling
- Implement loading states
- Add file upload progress

4. Enhance Features:
- Add user authentication
- Implement document management
- Add support for more file types
