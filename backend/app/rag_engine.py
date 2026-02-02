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
            template = """You are a helpful, precise, and context-aware assistant.

Your task is to answer the user's question using the conversation history, provided context, and uploaded document content.

CONVERSATION HISTORY:
{chat_history}

INSTRUCTIONS:
- Use the conversation history to maintain context and remember previously shared information
- Use the given context and uploaded document content to provide accurate answers
- Extract ONLY information that is clearly readable, meaningful, and relevant
- Ignore OCR noise, garbled text, broken words, random symbols, or unreadable fragments
- Do NOT repeat raw OCR output
- Do NOT describe what the document contains unless explicitly asked
- Do NOT list topics unless the user explicitly asks to list topics
- Do NOT add assumptions or inferred meaning
- If the answer cannot be clearly derived from readable content, say the information is not available
- Remember previous information shared in the conversation (like user's name, preferences, etc.)
- Reference previous context when relevant to the current question

ANSWER RULES:
- Answer ONLY the user's question
- Keep answers short, direct, and meaningful
- Preserve key factual information without distortion
- Avoid repetition
- Do NOT use the '*' symbol anywhere in the answer

Context:
{context}

Uploaded Document Content:
{document_content}

User Question:
{input}

Answer:
"""
            
            return PromptTemplate(
                input_variables=["chat_history", "context", "document_content", "input"],
                template=template
            )
        else:
            template = """You are a helpful, precise, and extraction-focused assistant.

Your task is to answer the user's question strictly using the provided context and uploaded document content.

INSTRUCTIONS:
- Use ONLY the given context and uploaded document content
- Extract ONLY information that is clearly readable, meaningful, and relevant
- Ignore OCR noise, garbled text, broken words, random symbols, or unreadable fragments
- Do NOT repeat raw OCR output
- Do NOT describe what the document contains unless explicitly asked
- Do NOT list topics unless the user explicitly asks to list topics
- Do NOT use external knowledge
- Do NOT add assumptions or inferred meaning
- If the answer cannot be clearly derived from readable content, say the information is not available

OCR CLEANUP RULES:
- Discard text with spelling corruption, random capitalization, broken sentences, or layout artifacts
- Use only well-formed sentences or clearly identifiable facts
- If OCR quality is poor and no reliable information can be extracted, respond clearly that the document content is unclear or insufficient
- Never echo noisy OCR text in the final answer

DOCUMENT HANDLING RULES:
- Use only the minimal portion of the document required to answer the question
- Do NOT summarize the entire document
- Do NOT invent missing data
- If multiple parts of the document conflict due to OCR errors, ignore them

ANSWER RULES:
- Answer ONLY the user's question
- Keep answers short, direct, and meaningful
- Preserve key factual information without distortion
- Avoid repetition
- Do NOT use the '*' symbol anywhere in the answer

FORMATTING GUIDELINES:
- Plain sentences preferred
- Use short paragraphs or numbered points only if it improves clarity
- No headings unless absolutely necessary

SPECIAL BEHAVIOR FOR OUT-OF-CONTEXT OR CASUAL QUESTIONS:
- If the question is unrelated to the document or context, reply with a short natural response only

Context:
{context}

Uploaded Document Content:
{document_content}

User Question:
{input}

Answer:
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
        session_id: Optional[str] = None
    ) -> Dict:

        logger.info(f"Processing question with {provider}/{model}")
        logger.info(f"Question: {question[:100]}...")
        logger.info(f"Document IDs: {document_ids}, URL: {url}")
        
        # Determine sources
        has_documents = False
        has_url = False
        all_docs = []
        source_type = "document"
        
        # Process document_ids if provided
        if document_ids:
            search_ids = [did for did in document_ids if did in self.vectorstores]
            if not search_ids:
                logger.error(f"None of the requested document IDs found in vectorstores")
                logger.error(f"Requested: {document_ids}, Available: {list(self.vectorstores.keys())}")
                return {
                    "answer": "Error: The specified documents are not loaded in the system. Please upload documents first or check if they were successfully processed.",
                    "sources": [],
                    "provider": provider,
                    "model": model
                }
            if search_ids:
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
                url_docs = crawler.process_url(url, chunk_size=1000)
                all_docs.extend(url_docs)
                logger.info(f"✓ Retrieved {len(url_docs)} chunks from URL")
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
        
        if session_id:
            try:
                from app.memory_manager import get_memory_manager
                memory_manager = get_memory_manager()
                chat_history_str = memory_manager.get_chat_history(session_id)
                has_history = bool(chat_history_str.strip())
                
                if has_history:
                    logger.info(f"[*] Using chat history from session {session_id}")
                    logger.debug(f"Chat history preview: {chat_history_str[:200]}...")
            except Exception as e:
                logger.warning(f"Could not retrieve chat history: {e}")
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
            response = rag_chain.invoke(question)
            answer_text = response.content if hasattr(response, 'content') else str(response)
            # Sanitise output: remove asterisks and backticks and non-printable control chars
            try:
                # remove backticks and asterisks
                answer_text = re.sub(r"[`*]", "", answer_text)
                # remove other non-printable chars except newline and tab
                answer_text = "".join(ch for ch in answer_text if ch.isprintable() or ch in "\n\t")
                # collapse multiple blank lines
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
