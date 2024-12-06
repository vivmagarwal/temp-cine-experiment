import os
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
import chromadb
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.docstore.document import Document
import tempfile
import asyncio
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize global variables
embeddings = None
vector_store = None
qa_chain = None

def initialize_langchain():
    global embeddings, vector_store, qa_chain
    
    try:
        # Initialize embeddings
        embeddings = OpenAIEmbeddings()
        
        # Initialize vector store
        vector_store = Chroma(
            collection_name="rag_collection",
            embedding_function=embeddings,
            persist_directory="./chroma_db"
        )
        
        # Initialize QA chain with specific prompt
        llm = ChatOpenAI(temperature=0)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(
                search_kwargs={"k": 4},  # Increase number of chunks retrieved
                search_type="mmr"  # Use MMR for better diversity in retrieved chunks
            ),
            return_source_documents=True,
            verbose=True
        )
        logger.info("Langchain components initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Langchain components: {str(e)}")
        raise

@app.on_event("startup")
async def startup_event():
    initialize_langchain()

async def process_file(file: UploadFile) -> List[Document]:
    try:
        # Create a temporary file with the original extension
        suffix = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            
            logger.info(f"Processing file: {file.filename}")
            
            # Choose appropriate loader based on file type
            if suffix == '.pdf':
                loader = PyPDFLoader(temp_file.name)
                # PyPDFLoader automatically splits by pages
                docs = loader.load()
                logger.info(f"Extracted {len(docs)} pages from PDF")
                
                # Log the first few characters of each page for verification
                for i, doc in enumerate(docs):
                    preview = doc.page_content[:100].replace('\n', ' ')
                    logger.info(f"Page {i+1} preview: {preview}...")
            else:
                loader = TextLoader(temp_file.name)
                docs = loader.load()
            
            # Add file metadata
            for i, doc in enumerate(docs):
                doc.metadata.update({
                    "file_name": file.filename,
                    "file_type": suffix[1:],
                    "page_number": i + 1,
                    "total_pages": len(docs)
                })
            
            # Clean up
            os.unlink(temp_file.name)
            
            logger.info(f"Successfully processed file: {file.filename}")
            return docs
            
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file {file.filename}: {str(e)}")

@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    try:
        documents = []
        for file in files:
            # Process each file with a timeout
            try:
                docs = await asyncio.wait_for(process_file(file), timeout=120)  # Increased timeout to 120 seconds
                documents.extend(docs)
            except asyncio.TimeoutError:
                raise HTTPException(status_code=408, detail=f"Processing timeout for file: {file.filename}")
        
        if not documents:
            raise HTTPException(status_code=400, detail="No documents were successfully processed")
        
        logger.info(f"Splitting documents into chunks")
        # Split documents with specific configuration for better chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Smaller chunk size for better context
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        splits = text_splitter.split_documents(documents)
        
        logger.info(f"Adding {len(splits)} chunks to vector store")
        # Add to vector store
        vector_store.add_documents(splits)
        
        # Log a preview of the first few chunks
        for i, split in enumerate(splits[:3]):
            preview = split.page_content[:100].replace('\n', ' ')
            logger.info(f"Chunk {i+1} preview: {preview}...")
        
        return {
            "message": f"Successfully processed {len(files)} files",
            "chunks_created": len(splits),
            "total_pages": len(documents)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in upload_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query(question: str = Form(...)):
    try:
        if not qa_chain:
            raise HTTPException(status_code=500, detail="System not initialized")
        
        logger.info(f"Processing query: {question}")
        
        # Add specific instructions to the question
        enhanced_question = f"""Based on the provided document content, {question}
        If the answer is not directly found in the documents, please say so instead of making up information."""
        
        result = qa_chain({"query": enhanced_question})
        
        # Extract source information including metadata
        sources = []
        for doc in result["source_documents"]:
            source_info = {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            sources.append(source_info)
        
        logger.info("Query processed successfully")
        logger.info(f"Answer preview: {result['result'][:100]}...")
        
        return {
            "answer": result["result"],
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    return {"status": "RAG system is running"}
