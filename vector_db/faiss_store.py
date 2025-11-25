"""
FAISS Vector Store - Local storage with OpenAI embeddings
For portfolio and fund metadata embeddings
"""
import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Optional
from openai import OpenAI
import config

class LocalVectorStore:
    def __init__(self, store_path='./data/vector_store'):
        self.store_path = store_path
        self.index_file = f"{store_path}/faiss.index"
        self.metadata_file = f"{store_path}/metadata.pkl"
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.embedding_model = "text-embedding-3-small"  # 1536 dimensions
        self.dimension = 1536
        
        # Create directory
        os.makedirs(store_path, exist_ok=True)
        
        # Load or create index
        self.index = None
        self.metadata = []
        self.load()
    
    def load(self):
        """Load existing FAISS index and metadata"""
        if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
            self.index = faiss.read_index(self.index_file)
            with open(self.metadata_file, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"✓ Loaded FAISS index with {self.index.ntotal} vectors")
        else:
            # Create new index (1536 dimensions for text-embedding-3-small)
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            print("✓ Created new FAISS index with OpenAI embeddings")
    
    def save(self):
        """Save FAISS index and metadata to disk"""
        faiss.write_index(self.index, self.index_file)
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)
        print(f"✓ Saved FAISS index with {self.index.ntotal} vectors")
    
    def add_texts(self, texts: List[str], metadatas: List[Dict]):
        """Add texts to vector store using OpenAI embeddings"""
        if not texts:
            return
        
        # Generate embeddings using OpenAI
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        
        # Extract embeddings
        embeddings = [item.embedding for item in response.data]
        
        # Add to FAISS index
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Store metadata
        self.metadata.extend(metadatas)
        
        # Save to disk
        self.save()
        print(f"✓ Added {len(texts)} texts with OpenAI embeddings")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar texts using OpenAI embeddings"""
        if self.index.ntotal == 0:
            return []
        
        # Embed query using OpenAI
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=[query]
        )
        query_embedding = response.data[0].embedding
        
        # Search FAISS
        distances, indices = self.index.search(
            np.array([query_embedding]).astype('float32'), 
            min(k, self.index.ntotal)
        )
        
        # Return results with metadata
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                results.append({
                    'metadata': self.metadata[idx],
                    'score': float(distances[0][i])
                })
        
        return results
    
    def clear(self):
        """Clear all vectors"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        self.save()


# Convenience functions
def index_portfolio(portfolio_data: Dict):
    """Index portfolio holdings for Q&A"""
    store = LocalVectorStore()
    
    texts = []
    metadatas = []
    
    # Index each holding
    for holding in portfolio_data.get('holdings', []):
        text = f"{holding['scheme_name']} - {holding['amc']} - Type: {holding['type']} - Current Value: ₹{holding['current_value']:,.0f} - Units: {holding['units']:.2f}"
        
        texts.append(text)
        metadatas.append({
            'type': 'holding',
            'scheme_name': holding['scheme_name'],
            'folio': holding['folio_number'],
            'data': holding
        })
    
    # Add portfolio summary
    summary_text = f"Total portfolio value: ₹{portfolio_data['total_value']:,.0f}, Total invested: ₹{portfolio_data['total_invested']:,.0f}, Total gain: ₹{portfolio_data['total_gain']:,.0f}"
    texts.append(summary_text)
    metadatas.append({
        'type': 'summary',
        'data': portfolio_data
    })
    
    store.add_texts(texts, metadatas)
    print(f"✓ Indexed {len(texts)} items")


if __name__ == "__main__":
    # Test
    store = LocalVectorStore()
    
    # Add sample data
    texts = ["HDFC Flexi Cap Fund", "ICICI Large Cap Fund", "SBI Small Cap Fund"]
    metadatas = [{'fund': t} for t in texts]
    
    store.add_texts(texts, metadatas)
    
    # Search
    results = store.search("flexi cap fund", k=2)
    print(f"Search results: {results}")
