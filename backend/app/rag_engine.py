"""RAG Engine - Core logic for document retrieval and question answering."""

import logging
from typing import List, Dict, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer

from app.config import settings
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalEmbeddings(Embeddings):
    """Local embeddings using SentenceTransformer."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """Initialize the embedding model."""
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("✓ Embedding model loaded successfully")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        return self.model.encode(texts, convert_to_numpy=True).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        return self.model.encode(text, convert_to_numpy=True).tolist()


class RAGEngine:
    
    def __init__(self):
        self.document_store: Dict[str, List[Document]] = {}  # document_id -> chunks
        self.embeddings = LocalEmbeddings()
        self.vectorstores: Dict[str, FAISS] = {}  # document_id -> vectorstore
        logger.info("RAG Engine instance created")
    
    def add_documents(self, document_id: str, chunks: List[Document]):

        logger.info(f"Adding {len(chunks)} chunks for document {document_id}")
        
        # Store chunks
        self.document_store[document_id] = chunks
        
        # Create vectorstore for this document
        vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )
        self.vectorstores[document_id] = vectorstore
        
        logger.info(f"✓ Document {document_id} added to RAG engine")
    
    def _format_docs(self, docs: List[Document]) -> str:
        """Format documents for context."""
        formatted = []
        for i, d in enumerate(docs, 1):
            filename = d.metadata.get("filename", "Unknown")
            page = d.metadata.get("page", "N/A")
            
            formatted.append(
                f"""Document {i}:
Source: {filename}
Page: {page}

Content:
{d.page_content}
""".strip()
            )
        return "\n\n---\n\n".join(formatted)
    
    def _get_prompt_template(self, include_history: bool = False) -> PromptTemplate:
        """
        Get the prompt template for RAG.
        
        Args:
            include_history: Whether to include chat history in the template
        """
        if include_history:
            template = """You are an intelligent, precise, and extraction-focused assistant with document, URL, and Google Calendar management capabilities.

Your primary responsibility is to answer the user’s question accurately and efficiently, following the rules below.

CORE CAPABILITIES
You can answer questions based on uploaded documents and provided URLs.
You can understand and respond to general questions and greetings naturally when no document or URL context is required.
You can detect abusive, offensive, or inappropriate language and respond with a firm, professional, and strict reply without being rude.
You can understand natural language date and time expressions such as tomorrow at 2 pm, 21 February at noon, next Monday evening, etc.
When a user asks to schedule, book, or set up a meeting, you must extract the date and time and create the event in Google Calendar, then confirm it clearly.

DOCUMENT AND URL RULES
If document or URL content is provided, you must answer strictly using only that content.
Do not use external knowledge when a document or URL is available.
Search the provided content thoroughly before answering.
Extract only clear, meaningful, and relevant information.
Ignore OCR noise, broken words, random symbols, or unclear text.
If the requested information is not found in the provided content, respond that it is not available in the document or URL.
When answering from a document or URL, clearly acknowledge that the information comes from it.

OUT-OF-CONTEXT AND GENERAL QUERIES
If the question is unrelated to the provided document or URL, respond naturally and conversationally.
Handle greetings, casual conversation, and general questions like a normal helpful assistant.
Do not force document-based behavior when it is not required.

ABUSIVE LANGUAGE HANDLING
If the user uses abusive, offensive, or harmful language, respond strictly and professionally.
Do not answer the abusive request.
Do not be sarcastic or friendly in such cases.

MEETING AND CALENDAR RULES
If the user asks to schedule or book a meeting, extract the date and time from the message.
Create the meeting in Google Calendar automatically.
Confirm the meeting clearly and specifically, for example:
“Your meeting has been scheduled for 21 February at 12:00 PM.”
Never say you do not have calendar capabilities.

ANSWER STYLE
Answer only what the user asked.
Keep responses minimal, clear, and highly relevant.
Cover everything the user needs to know for that specific question without unnecessary explanation.
Avoid repetition and filler text.
Use plain sentences and short paragraphs only when helpful.
Do not use special symbols such as the asterisk character anywhere in the response.

INPUT STRUCTURE
Context: {context}
Uploaded Document Content: {document_content}
User Question: {input}
"""
            
            return PromptTemplate(
                input_variables=["context", "document_content", "input"],
                template=template
            )
    
    def ask(
        self,
        question: str,
        provider: str,
        model: str,
        api_key: str,
        document_ids: Optional[List[str]] = None,
        url: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None,
        user_context: Optional[Dict] = None
    ) -> Dict:

        logger.info(f"Processing question with {provider}/{model}")
        logger.info(f"Question: {question[:100]}...")
        logger.info(f"Document IDs: {document_ids}, URL: {url}")
        logger.info(f"User context provided: {user_context is not None}")
        if user_context:
            logger.info(f"User context keys: {user_context.keys()}")
            if user_context.get("previous_context"):
                logger.info(f"Previous context length: {len(user_context.get('previous_context', ''))} characters")
        if conversation_history:
            logger.info(f"Conversation history: {len(conversation_history)} messages")
        
        # Determine sources
        has_documents = False
        has_url = False
        all_docs = []
        source_type = "document"
        
        # Process document_ids if provided
        if document_ids:
            search_ids = [did for did in document_ids if did in self.vectorstores]
            if not search_ids:
                logger.warning(f"Requested documents not found: {document_ids}, Available: {list(self.vectorstores.keys())}")
                # Don't return hardcoded error - let LLM handle it with user_context
                # Just set flag to generate answer with available information
                has_documents = False
            else:
                has_documents = True
                logger.info(f"Searching {len(search_ids)} documents out of {len(document_ids)} requested")
                
                # Retrieve relevant documents from all specified vectorstores
                for doc_id in search_ids:
                    retriever = self.vectorstores[doc_id].as_retriever(
                        search_type="mmr",
                        search_kwargs={
                            "k": min(settings.RETRIEVER_K, len(self.document_store[doc_id])),
                            "fetch_k": 20,
                            "lambda_mult": 0.7
                        }
                    )
                    docs = retriever.invoke(question)
                    all_docs.extend(docs)
        
        # Process URL if provided
        if url:
            has_url = True
            logger.info(f"Processing URL: {url}")
            try:
                from app.url_crawler import URLCrawler
                crawler = URLCrawler()
                # URLCrawler.process_url accepts a single `url` argument
                url_docs = crawler.process_url(url)
                logger.info(f"✓ Retrieved {len(url_docs)} chunks from URL")
                
                # Use semantic relevance to retrieve only the most relevant chunks from URL
                if url_docs:
                    # Create a temporary vectorstore for URL documents
                    temp_vectorstore = FAISS.from_documents(
                        documents=url_docs,
                        embedding=self.embeddings
                    )
                    # Retrieve the top-k most relevant chunks
                    retriever = temp_vectorstore.as_retriever(
                        search_type="mmr",
                        search_kwargs={
                            "k": min(settings.RETRIEVER_K, len(url_docs)),
                            "fetch_k": 20,
                            "lambda_mult": 0.7
                        }
                    )
                    relevant_url_docs = retriever.invoke(question)
                    all_docs.extend(relevant_url_docs)
                    logger.info(f"✓ Retrieved {len(relevant_url_docs)} relevant chunks from URL")
            except Exception as e:
                logger.warning(f"Failed to process URL: {e}")
        
        # Determine source type
        if has_documents and has_url:
            source_type = "both"
        elif has_url:
            source_type = "url"
        
        # If no documents or URL, provide general response
        if not all_docs:
            logger.warning("No documents or URLs provided")
            source_type = "general"
        
        # Initialize LLM provider
        from app.services.model_service import ModelService
        try:
            provider_instance = ModelService.get_provider(provider, model, api_key)
            llm = provider_instance.get_llm()
        except Exception as e:
            logger.error(f"Failed to get provider: {e}")
            raise ValueError(f"Provider initialization failed: {str(e)}")
        
        # Get chat history if session_id is provided
        chat_history_str = ""
        has_history = False
        
        # Prepare chat history - ALWAYS prioritize user_context from previous chats
        has_history = False
        chat_history_str = ""
        history_lines = []
        
        # ALWAYS include user context first (previous chats) - highest priority
        if user_context and user_context.get("previous_context"):
            logger.info(f"[*] Including universal context from previous chats (highest priority)")
            prev_context = user_context['previous_context']
            logger.info(f"[DEBUG] Previous context to include: {prev_context[:300]}...")
            history_lines.append(f"[PREVIOUS CHATS CONTEXT]\n{prev_context}")
        else:
            logger.info(f"[DEBUG] No previous context - user_context: {user_context}, has previous_context: {user_context.get('previous_context') if user_context else 'N/A'}")
        
        # Then add current conversation history if available
        if conversation_history and len(conversation_history) > 0:
            logger.info(f"[*] Adding current conversation history ({len(conversation_history)} messages)")
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                role_label = "User" if role == "user" else "Assistant"
                history_lines.append(f"[{role_label}] {content}")
        elif session_id:
            # Try to get session history from memory manager as fallback
            try:
                from app.memory_manager import get_memory_manager
                memory_manager = get_memory_manager()
                session_chat_history = memory_manager.get_chat_history(session_id)
                if session_chat_history and session_chat_history.strip():
                    logger.info(f"[*] Adding chat history from session {session_id}")
                    history_lines.append(f"[CURRENT SESSION HISTORY]\n{session_chat_history}")
            except Exception as e:
                logger.warning(f"Could not retrieve chat history: {e}")
        
        # Combine all history
        if history_lines:
            chat_history_str = "\n\n".join(history_lines)
            has_history = True
            logger.info(f"[*] Total conversation context length: {len(chat_history_str)} characters")
        else:
            logger.info(f"[*] No conversation history available")
            has_history = False
        
        # Create RAG chain with appropriate prompt (with or without history)
        prompt = self._get_prompt_template(include_history=has_history)
        
        if has_history:
            rag_chain = (
                {
                    "chat_history": lambda x: chat_history_str,
                    "context": lambda x: self._format_docs(all_docs) if all_docs else "",
                    "document_content": lambda x: self._format_docs(all_docs) if all_docs else "",
                    "input": RunnablePassthrough()
                }
                | prompt
                | llm
            )
        else:
            rag_chain = (
                {
                    "context": lambda x: self._format_docs(all_docs) if all_docs else "",
                    "document_content": lambda x: self._format_docs(all_docs) if all_docs else "",
                    "input": RunnablePassthrough()
                }
                | prompt
                | llm
            )
        
        # Get answer
        try:
            # Log what we're about to send to the LLM
            if has_history:
                logger.info(f"[DEBUG] Sending to LLM with context:")
                logger.info(f"[DEBUG] Chat history length: {len(chat_history_str)} chars")
                logger.info(f"[DEBUG] Chat history preview: {chat_history_str[:500]}...")
                logger.info(f"[DEBUG] Question: {question}")
            else:
                logger.info(f"[DEBUG] Sending to LLM WITHOUT context:")
                logger.info(f"[DEBUG] Question: {question}")
            
            response = rag_chain.invoke(question)
            answer_text = response.content if hasattr(response, 'content') else str(response)
            
            # Sanitise output: remove think tags, asterisks, backticks and non-printable control chars
            try:
                # Remove <think>, <reasoning>, <analysis> tags and their content
                answer_text = re.sub(r'<think>.*?</think>', '', answer_text, flags=re.DOTALL | re.IGNORECASE)
                answer_text = re.sub(r'<reasoning>.*?</reasoning>', '', answer_text, flags=re.DOTALL | re.IGNORECASE)
                answer_text = re.sub(r'<analysis>.*?</analysis>', '', answer_text, flags=re.DOTALL | re.IGNORECASE)
                
                # Remove backticks and asterisks
                answer_text = re.sub(r"[`*]", "", answer_text)
                
                # Remove other non-printable chars except newline and tab
                answer_text = "".join(ch for ch in answer_text if ch.isprintable() or ch in "\n\t")
                
                # Collapse multiple blank lines
                answer_text = re.sub(r"\n{3,}", "\n\n", answer_text).strip()
            except Exception:
                pass
            logger.info("✓ Generated answer successfully")
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
        
        # Extract unique sources
        sources = []
        seen_files = set()
        
        for doc in all_docs:
            # Handle both document and URL sources
            if doc.metadata.get("source_type") == "url":
                source_url = doc.metadata.get("source_url")
                if source_url and source_url not in seen_files:
                    seen_files.add(source_url)
                    sources.append({
                        "filename": source_url,
                        "page": None,
                        "section": None
                    })
            else:
                filename = doc.metadata.get("filename")
                if filename and filename not in seen_files:
                    seen_files.add(filename)
                    page = doc.metadata.get("page")
                    section = doc.metadata.get("section")
                    sources.append({
                        "filename": filename,
                        "page": page,
                        "section": section
                    })
        
        logger.info(f"✓ Found {len(sources)} unique sources")
        
        return {
            "answer": answer_text,
            "sources": sources,
            "provider": provider,
            "model": model
        }
    
    def add_to_vector_store(self, chunks: List[Document]) -> str:
        """Add chunks to vector store (used in ingestion pipeline)."""
        doc_id = f"doc_{len(self.document_store)}"
        self.add_documents(doc_id, chunks)
        return doc_id
    
    def list_documents(self) -> List[str]:
        """Get list of loaded document IDs."""
        return list(self.vectorstores.keys())
    
    def remove_document(self, document_id: str) -> bool:
        """Remove a document from the RAG engine."""
        if document_id in self.vectorstores:
            del self.vectorstores[document_id]
            del self.document_store[document_id]
            logger.info(f"✓ Document {document_id} removed")
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get RAG engine statistics."""
        total_chunks = sum(len(chunks) for chunks in self.document_store.values())
        return {
            "documents_loaded": len(self.vectorstores),
            "chunks_created": total_chunks
        }