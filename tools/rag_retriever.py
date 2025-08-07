from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
import json
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

class JobRetriever:
    def __init__(self, json_path="data/jobs.json", rebuild_db=False):
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        if rebuild_db or not os.path.exists("data/embeddings/chroma_db"): 
            self.db = self._initialize_db(json_path)
        else:
            self.db = Chroma(
                persist_directory="data/embeddings/chroma_db",
                embedding_function=self.embedding_model
            )
        
    def _initialize_db(self, json_path):
        if os.path.exists("data/embeddings/chroma_db"):
            shutil.rmtree("data/embeddings/chroma_db")
            
        if not os.path.exists("data/embeddings"):
            os.makedirs("data/embeddings")
            
        with open(json_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
            
        docs = []
        for job in jobs:
            content = f"""Title: {job['title']}
Location: {job['location']}
job_url: {job['job_url']}
Department: {job['department']}
Type: {job['job_type']}
Workplace Type: {job['workplace_type']}
Job URL: {job['job_url']}
Summary: {job['job_summary']}
Responsibilities: {job['key_responsibilities']}
Requirements: {job['requirements']}"""
            docs.append(Document(page_content=content, metadata={"job_id": job["job_id"]}))
            
        db = Chroma.from_documents(
            docs,
            self.embedding_model,
            persist_directory="data/embeddings/chroma_db"
        )
        return db

    def _calculate_similarity(self, text1, text2):
        """Simple similarity check based on common words"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split()) 
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0
        
    def retrieve(self, query: str, k: int = 5):
        candidates = self.db.similarity_search_with_score(query, k=k*2)
        filtered_docs = []
        for doc, score in candidates:
            is_similar = False
            for existing_doc, _ in filtered_docs:
                if self._calculate_similarity(doc.page_content, existing_doc.page_content) > 0.8:
                    is_similar = True
                    break
            if not is_similar:
                filtered_docs.append((doc, score))
            if len(filtered_docs) >= k:
                break
                
        return [doc for doc, _ in filtered_docs]
