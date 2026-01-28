# 📚 LectureBot - AI Study Assistant

<div align="center">

**Professional RAG Chatbot for Last-Minute Exam Preparation**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-green.svg)](https://openai.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## 🎯 Overview

LectureBot is a **professional-grade RAG (Retrieval-Augmented Generation) chatbot** built from scratch without framework dependencies like LangChain. This showcases fundamental understanding of RAG architecture, vector embeddings, and LLM integration. Designed to help students efficiently review lecture materials for last-minute exam preparation.

### ✨ Key Features

- **🤖 Intelligent Q&A**: Ask questions and get accurate answers from your lecture materials
- **📄 Multi-Format Support**: PDF, DOCX, TXT, Markdown, and PowerPoint files
- **🔍 Source Citations**: See exactly where each answer comes from in your documents
- **💬 Conversational Memory**: Maintains context across multiple questions
- **⚡ Fast Retrieval**: Powered by FAISS vector database
- **🎨 Modern UI**: Clean, intuitive Streamlit interface
- **📊 Progress Tracking**: Visual feedback during document processing
- **🔧 No Framework Lock-in**: Built with direct API calls for maximum control
- **🗄️ Persistent Storage**: Vector indices and documents saved for quick reloading
- **� User Authentication**: Login/registration system with secure password hashing
- **👥 Multi-User Ready**: Each user gets isolated storage for documents and collections

## 🏗️ Architecture

```
┌─────────────────┐
│  Streamlit UI   │
└────────┬────────┘
         │
    ┌────▼─────────────────────────┐
    │     RAG Engine               │
    │  (Custom Implementation)     │
    │  - Conversation History      │
    │  - Context Building          │
    │  - OpenAI Integration        │
    └────┬─────────────────────────┘
         │
    ┌────▼──────────┐    ┌──────────────┐
    │  Vector Store │◄───┤   Document   │
    │    (FAISS)    │    │  Processor   │
    │               │    │  (Custom)    │
    └────┬──────────┘    └──────────────┘
         │
    ┌────▼──────────┐
    │  OpenAI API   │
    │  - Embeddings │
    │  - Chat       │
    └───────────────┘
```

### 🔑 Technical Highlights

**Built Without LangChain - Pure Python Implementation:**
- ✅ Custom document loaders (PDF, DOCX, PPTX, TXT, MD)
- ✅ Custom text chunking with overlap
- ✅ Direct OpenAI API integration for embeddings
- ✅ Direct FAISS Python library usage
- ✅ Manual conversation history management
- ✅ Custom RAG pipeline implementation
- ✅ Persistent vector storage with pickle serialization
- ✅ User authentication with streamlit-authenticator
- ✅ Secure password hashing with bcrypt
- ✅ User-scoped storage isolation

This demonstrates deep understanding of:
- Vector embeddings and similarity search
- RAG architecture and implementation
- Document processing pipelines
- Conversational AI state management

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LectureBot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup authentication (optional)**
   ```bash
   python setup_auth.py
   ```
   This creates a demo user (username: `demo`, password: `demo123`)

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## 📖 Usage Guide

### 1. Login or Register
- **New users**: Fill out the registration form (username, name, email, password)
- **Existing users**: Enter your username and password
- Your documents and collections are private to your account

### 2. Setup API Key
- Enter your OpenAI API key in the sidebar (🔑 API Configuration section)
- Or set it in the `.env` file before launching

### 2. Upload Documents
- Click "Upload lecture materials" in the sidebar
- Select PDF, DOCX, TXT, MD, or PPTX files
- Multiple files can be uploaded at once

### 3. Process Documents
- Give your collection a name (e.g., "CS101_Finals")
- Click "📥 Process Documents"
- Wait for processing to complete

### 4. Start Asking Questions
- Type your question in the chat input
- Get answers with source citations
- Ask follow-up questions naturally

### 5. Managing Collections
- Use "🔄 Load Existing" to reload previously processed documents
- Use "🗑️ Clear Chat History" to start a fresh conversation

## 💡 Example Questions

- "What are the key concepts from Chapter 3?"
- "Explain the difference between X and Y"
- "Give me a summary of the machine learning algorithms covered"
- "What are the important dates mentioned in the syllabus?"
- "Can you create practice questions for the exam?"

## 🛠️ Configuration

Edit `config.py` or `.env` file to customize:

### Model Settings
```python
LLM_MODEL=gpt-4o-mini              # Language model
EMBEDDING_MODEL=text-embedding-3-small  # Embedding model
LLM_TEMPERATURE=0.3                 # Response creativity (0-1)
MAX_TOKENS=2000                     # Maximum response length
```

### Document Processing
```python
CHUNK_SIZE=1000                     # Size of text chunks
CHUNK_OVERLAP=200                   # Overlap between chunks
MAX_FILE_SIZE_MB=50                 # Maximum file size
```

### Vector Store
```python
VECTOR_STORE_TYPE=faiss             # faiss (default)
TOP_K_RESULTS=5                     # Number of retrieved chunks
```

### Storage
- **Temporary Storage**: Uploaded files stored in `data/uploads/` during processing
- **Persistent Storage**: Vector indices and document metadata saved in `vectorstore/{collection_name}/`
  - `index.faiss`: FAISS vector index for fast similarity search
  - `documents.pkl`: Pickled document chunks with metadata
- **Auto Cleanup**: Uploaded files automatically deleted after processing

## 📁 Project Structure

```
LectureBot/
├── app.py                      # Streamlit application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── auth_config.yaml            # User credentials (hashed passwords)
├── setup_auth.py               # Authentication setup script
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
│
├── core/                      # Core RAG components
│   ├── __init__.py
│   ├── document_processor.py  # Document loading & chunking
│   ├── vector_store.py        # Vector store management
│   └── rag_engine.py          # RAG chain logic
│
├── utils/                     # Utility modules
│   ├── __init__.py
│   └── logger.py              # Logging configuration
│
├── data/                      # Data directory
│   └── uploads/               # Uploaded files (temporary)
│       └── {username}/        #   - User-scoped upload folders
│
├── vectorstore/               # Persistent vector indices
│   └── {username}/            # User-scoped storage
│       └── {collection_name}/ #   - Each collection folder contains:
│           ├── index.faiss    #     - FAISS vector index
│           └── documents.pkl  #     - Pickled document chunks
└── logs/                      # Application logs
```

## 🔧 Advanced Features

### Custom Prompts

Modify the system prompt in [core/rag_engine.py](core/rag_engine.py#L18):

```python
SYSTEM_PROMPT = """Your custom prompt here..."""
```

### Different LLM Models

Support for multiple models:
- OpenAI: GPT-4, GPT-4-Turbo, GPT-4o-mini, GPT-3.5-Turbo
- Configure via `LLM_MODEL` in [config.py](config.py)
- Can be extended to use Anthropic Claude, local models, etc.

### Vector Store Implementation

**FAISS** (Facebook AI Similarity Search):
- ✅ Fast and efficient L2 distance similarity search
- ✅ Lightweight with no external database dependencies
- ✅ Perfect for multi-user applications with session isolation
- ✅ Cross-platform compatible (Windows, Linux, macOS)
- ✅ Persistent storage via pickle serialization
- 📊 Handles thousands of documents efficiently

### Multi-User Authentication & Isolation

Each user has their own secure account with isolated storage:

```
User: alice (logged in)
  └── vectorstore/alice/Finals/index.faiss
  └── data/uploads/alice/lecture.pdf

User: bob (logged in)
  └── vectorstore/bob/Finals/index.faiss  (completely separate!)
  └── data/uploads/bob/lecture.pdf        (no conflict!)
```

**Authentication Features:**
- 🔐 Secure login with bcrypt password hashing
- 📝 In-app user registration
- 🍪 "Remember me" cookies (30 days)
- 👤 Personalized welcome messages
- 🚪 Logout functionality

**How it works:**
- User credentials stored in `auth_config.yaml` with hashed passwords
- Username used as folder name for storage isolation
- Each user's documents and collections are completely private
- Safe for shared deployments (Streamlit Cloud, etc.)

## 📊 Performance Tips

1. **Chunk Size**: Smaller chunks (500-800) for precise answers, larger (1500-2000) for context
2. **Top K Results**: Increase for comprehensive answers, decrease for speed
3. **Temperature**: Lower (0.1-0.3) for factual answers, higher for creative responses
4. **Batch Processing**: Embeddings are processed in batches of 100 to optimize API calls

## 🔒 Security Considerations

- ✅ User authentication with login/registration
- ✅ Passwords hashed with bcrypt (never stored in plain text)
- ✅ API keys stored in `.env` (not committed to git)
- ✅ User data isolated by username
- ✅ File upload size limits enforced
- ✅ Supported file types validated
- ⚠️ For production: Move `auth_config.yaml` to a database
- ⚠️ For production: Add `auth_config.yaml` to `.gitignore`
- ⚠️ Review uploaded documents for sensitive information

## 🐛 Troubleshooting

### Issue: "OpenAI API key not set"
**Solution**: Enter API key in sidebar or add to `.env` file

### Issue: "Vector store not found"
**Solution**: Process documents first before loading existing collection

### Issue: "Error loading document"
**Solution**: Ensure file format is supported and not corrupted

### Issue: Import errors or version conflicts
**Solution**: 
```bash
pip install --upgrade openai faiss-cpu
pip install -r requirements.txt
```

### Issue: "Failed to initialize client: __init__() got an unexpected keyword argument"
**Solution**: Update OpenAI package to latest version (>=1.30.0):
```bash
pip install --upgrade openai
```

## 📚 Dependencies

Core dependencies (no heavy frameworks):
- **OpenAI** (>=1.30.0): Direct API for LLM and embeddings
- **FAISS-CPU**: Efficient vector similarity search
- **Streamlit**: Web interface
- **streamlit-authenticator**: User authentication
- **bcrypt**: Secure password hashing
- **PyPDF2**: PDF processing
- **python-docx**: DOCX processing
- **python-pptx**: PowerPoint processing
- **Loguru**: Logging

**Why No LangChain?**
This project intentionally avoids LangChain to demonstrate:
- Understanding of RAG fundamentals
- Ability to implement from scratch
- Greater control over the pipeline
- Reduced dependencies and complexity
- Better for portfolio projects showcasing core skills

**Why FAISS Instead of ChromaDB?**
- ✅ Simpler installation (no SQLite version conflicts)
- ✅ Lightweight with minimal dependencies
- ✅ Cross-platform compatibility
- ✅ Direct control over vector operations
- ✅ Perfect for learning and portfolios

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Support for more file formats (e.g., HTML, EPUB)
- Advanced search options (MMR, hybrid search)
- Quiz generation features
- Export conversation history
- Multi-language support
- Custom embedding models (local models)
- Batch document processing optimizations

## 📄 License

## 🙏 Acknowledgments

Made with ❤️ for students everywhere

**Happy Studying! 📚✨**
</div>
