import numpy as np
from typing import List
import google.generativeai as genai

class RAGEngine:
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.chunks = []
        self.embeddings = []
        self.embedding_model = 'models/text-embedding-004'
    
    def chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def embed_text(self, text: str) -> np.ndarray:
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return np.array(result['embedding'])
        except Exception as e:
            # Fallback to simple word-based embedding if API fails
            words = text.lower().split()
            embedding = np.zeros(768)
            for i, word in enumerate(words[:100]):
                embedding[i % 768] += hash(word) % 100
            return embedding / (np.linalg.norm(embedding) + 1e-8)
    
    def index_documents(self, documents: List[str]):
        self.chunks = []
        self.embeddings = []
        
        for doc in documents:
            doc_chunks = self.chunk_text(doc)
            for chunk in doc_chunks:
                self.chunks.append(chunk)
                embedding = self.embed_text(chunk)
                self.embeddings.append(embedding)
    
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
    
    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        if not self.chunks:
            return []
        
        # Embed query
        query_embedding = self.embed_text(query)
        
        # Calculate similarities
        similarities = []
        for i, chunk_embedding in enumerate(self.embeddings):
            sim = self.cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((sim, i))
        
        # Sort and get top-k
        similarities.sort(reverse=True)
        top_indices = [idx for _, idx in similarities[:top_k]]
        
        return [self.chunks[i] for i in top_indices]
    
    def retrieve_all_chunks(self) -> List[str]:
        return self.chunks
    
    def get_chunk_count(self) -> int:
        return len(self.chunks)
    
    def should_use_rag(self, min_chunks: int = 8) -> bool:
        """Determine if RAG retrieval is beneficial
        
        For small documents (< 8 chunks), using all content is better than RAG.
        RAG is beneficial when documents are large and retrieval reduces noise.
        """
        return len(self.chunks) >= min_chunks