"""
RAG Engine - Core retrieval-augmented generation logic
"""
from typing import List, Dict, Optional, Callable
from datetime import datetime

from openai import OpenAI

from config import settings
from utils.logger import log
from core.document_processor import Document


class ConversationHistory:
    """Simple conversation history manager"""
    
    def __init__(self, max_history: int = 10):
        self.messages: List[Dict[str, str]] = []
        self.max_history = max_history
    
    def add_message(self, role: str, content: str):
        """Add a message to history"""
        self.messages.append({"role": role, "content": content})
        
        # Keep only recent messages to avoid token limits
        if len(self.messages) > self.max_history * 2:  # *2 because of user+assistant pairs
            self.messages = self.messages[-(self.max_history * 2):]
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages"""
        return self.messages.copy()
    
    def clear(self):
        """Clear history"""
        self.messages = []
    
    def format_for_display(self) -> List[Dict]:
        """Format for UI display"""
        history = []
        for msg in self.messages:
            history.append({
                'role': 'human' if msg['role'] == 'user' else 'ai',
                'content': msg['content']
            })
        return history


class RAGEngine:
    """Retrieval-Augmented Generation Engine for LectureBot"""
    
    SYSTEM_PROMPT = """You are LectureBot, an AI study assistant helping students prepare for exams by reviewing their lecture documents.

Your role:
- Answer questions based ONLY on the provided lecture content
- Provide clear, concise explanations suitable for exam preparation
- Cite specific sections or topics when referencing material
- If information isn't in the lecture materials, clearly state that
- Help students understand concepts, definitions, and relationships
- Suggest related topics they should review

Context from lecture materials:
{context}

Provide a helpful, accurate answer based on the lecture content."""
    
    def __init__(self, retriever: Callable):
        self.retriever = retriever
        self.openai_client = None
        self.history = ConversationHistory()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        if not settings.openai_api_key:
            log.error("OpenAI API key not set")
            raise ValueError("OpenAI API key required")
        
        from openai import OpenAI
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        log.info(f"Initialized OpenAI client with model: {settings.llm_model}")
    
    def _build_context(self, documents: List[Document]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', '')
            page_info = f" (Page {page})" if page else ""
            
            context_parts.append(
                f"[Source {i}: {source}{page_info}]\n{doc.page_content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _create_messages(self, question: str, context: str) -> List[Dict[str, str]]:
        """Create messages for OpenAI API including history"""
        messages = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT.format(context=context)
            }
        ]
        
        # Add conversation history
        history_messages = self.history.get_messages()
        messages.extend(history_messages)
        
        # Add current question
        messages.append({
            "role": "user",
            "content": question
        })
        
        return messages
    
    def ask(
        self,
        question: str,
        return_sources: bool = True
    ) -> Dict:
        """
        Ask a question and get an answer with sources
        
        Returns:
            Dict with 'answer', 'sources', and 'timestamp'
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        log.info(f"Processing question: {question[:100]}...")
        
        try:
            # Retrieve relevant documents
            source_docs = self.retriever(question)
            
            # Build context from retrieved documents
            context = self._build_context(source_docs)
            
            # Create messages with history
            messages = self._create_messages(question, context)
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=settings.llm_temperature,
                max_tokens=settings.max_tokens
            )
            
            answer = response.choices[0].message.content
            
            # Update conversation history
            self.history.add_message("user", question)
            self.history.add_message("assistant", answer)
            
            # Format sources
            sources = []
            if return_sources and source_docs:
                sources = self._format_sources(source_docs)
            
            result = {
                "answer": answer,
                "sources": sources,
                "timestamp": datetime.now().isoformat()
            }
            
            log.info(f"Generated answer with {len(sources)} sources")
            return result
            
        except Exception as e:
            log.error(f"Error generating answer: {str(e)}")
            raise
    
    def _format_sources(self, documents: List[Document]) -> List[Dict]:
        """Format source documents for display"""
        sources = []
        seen = set()
        
        for i, doc in enumerate(documents):
            source_name = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', None)
            chunk_id = doc.metadata.get('chunk_id', i)
            
            # Create unique identifier
            source_id = f"{source_name}_{page}_{chunk_id}"
            
            if source_id not in seen:
                sources.append({
                    'source': source_name,
                    'page': page,
                    'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
                seen.add(source_id)
        
        return sources
    
    def clear_history(self):
        """Clear conversation history"""
        self.history.clear()
        log.info("Cleared conversation history")
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history"""
        return self.history.format_for_display()
