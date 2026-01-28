"""
Vector Store Management
Handles embedding and retrieval from vector databases using FAISS
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import pickle
import numpy as np

import faiss
from openai import OpenAI

from config import settings, VECTORSTORE_DIR, get_user_vectorstore_dir
from utils.logger import log
from core.document_processor import Document


class VectorStoreManager:
    """Manage vector store operations using FAISS directly"""
    
    def __init__(self, session_id: str = None):
        self.index = None
        self.documents = []
        self.openai_client = None
        self.collection_name = None
        self.session_id = session_id  # For user-scoped storage
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        if not settings.openai_api_key:
            log.warning("OpenAI API key not set. Embeddings will not work.")
            return
        
        try:
            # Initialize OpenAI - using the modern client approach
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            log.info("Initialized OpenAI client")
            
        except Exception as e:
            log.error(f"Failed to initialize client: {str(e)}")
            raise
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            log.error(f"Error getting embedding: {str(e)}")
            raise
    
    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        try:
            response = self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            log.error(f"Error getting batch embeddings: {str(e)}")
            raise
    
    def create_vectorstore(
        self,
        documents: List[Document],
        collection_name: str = "lecture_docs"
    ):
        """Create a new FAISS vector store from documents"""
        if not self.openai_client:
            raise ValueError("Client not initialized. Please set OPENAI_API_KEY")
        
        if not documents:
            raise ValueError("No documents provided")
        
        log.info(f"Creating FAISS vector store with {len(documents)} documents")
        
        try:
            self.documents = documents
            self.collection_name = collection_name
            
            # Get embeddings in batches
            texts = [doc.page_content for doc in documents]
            all_embeddings = []
            
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                log.info(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                embeddings = self._get_embeddings_batch(batch_texts)
                all_embeddings.extend(embeddings)
            
            # Convert to numpy array
            embeddings_array = np.array(all_embeddings).astype('float32')
            dimension = embeddings_array.shape[1]
            
            # Create FAISS index
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings_array)
            
            # Save to disk
            self._save_index(collection_name)
            
            log.info(f"Created FAISS index with {len(documents)} vectors")
            
        except Exception as e:
            log.error(f"Error creating vector store: {str(e)}")
            raise
    
    def _get_vectorstore_dir(self) -> Path:
        """Get the appropriate vectorstore directory based on session"""
        if self.session_id:
            return get_user_vectorstore_dir(self.session_id)
        return VECTORSTORE_DIR
    
    def _save_index(self, collection_name: str):
        """Save FAISS index and documents to disk"""
        base_dir = self._get_vectorstore_dir()
        index_dir = base_dir / collection_name
        index_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_path = index_dir / "index.faiss"
        faiss.write_index(self.index, str(index_path))
        
        # Save documents
        docs_path = index_dir / "documents.pkl"
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)
        
        log.info(f"Saved FAISS index to {index_dir}")
    
    def load_vectorstore(
        self,
        collection_name: str = "lecture_docs"
    ) -> bool:
        """Load existing FAISS vector store"""
        if not self.openai_client:
            raise ValueError("Client not initialized. Please set OPENAI_API_KEY")
        
        try:
            base_dir = self._get_vectorstore_dir()
            index_dir = base_dir / collection_name
            index_path = index_dir / "index.faiss"
            docs_path = index_dir / "documents.pkl"
            
            if not index_path.exists() or not docs_path.exists():
                log.warning(f"Vector store '{collection_name}' not found")
                return None
            
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Load documents
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)
            
            self.collection_name = collection_name
            log.info(f"Loaded FAISS index with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            log.warning(f"Error loading vector store: {str(e)}")
            return None
    
    def add_documents(self, documents: List[Document]):
        """Add documents to existing vector store"""
        if not self.index:
            raise ValueError("Vector store not initialized")
        
        log.info(f"Adding {len(documents)} documents to vector store")
        
        # Get embeddings
        texts = [doc.page_content for doc in documents]
        embeddings = self._get_embeddings_batch(texts)
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Add to index
        self.index.add(embeddings_array)
        self.documents.extend(documents)
        
        # Save updated index
        if self.collection_name:
            self._save_index(self.collection_name)
        
        log.info(f"Added {len(documents)} documents to index")
    
    def similarity_search(
        self,
        query: str,
        k: int = settings.top_k_results
    ) -> List[Document]:
        """Search for similar documents"""
        if not self.index:
            raise ValueError("Vector store not initialized")
        
        log.debug(f"Searching for: {query[:100]}...")
        
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            query_vector = np.array([query_embedding]).astype('float32')
            
            # Search
            distances, indices = self.index.search(query_vector, min(k, len(self.documents)))
            
            # Get corresponding documents
            results = []
            for idx in indices[0]:
                if idx < len(self.documents) and idx >= 0:
                    results.append(self.documents[idx])
            
            log.debug(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            log.error(f"Error during search: {str(e)}")
            raise
    
    def get_retriever(self, **kwargs):
        """Get a retriever function for the vector store"""
        k = kwargs.get("k", settings.top_k_results)
        
        def retriever(query: str) -> List[Document]:
            return self.similarity_search(query, k=k)
        
        return retriever

