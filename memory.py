from config import VECTOR_DB_COLLECTION, MAX_MEMORY_RESULTS

class NarrativeMemory:
    def __init__(self):
        self.chroma_available = False
        self.fallback_history = []
        try:
            import chromadb
            self.client = chromadb.Client()
            self.collection = self.client.get_or_create_collection(name=VECTOR_DB_COLLECTION)
            self.chroma_available = True
        except Exception:
            self.chroma_available = False

    def add_memory(self, turn: int, action: str, result: str):
        text = f"Turn {turn} | Action: {action} | Result: {result}"
        if self.chroma_available:
            try:
                self.collection.add(
                    documents=[text],
                    metadatas=[{"turn": turn}],
                    ids=[f"turn_{turn}"]
                )
                return
            except Exception:
                pass
        self.fallback_history.append(text)

    def retrieve_context(self, current_action: str, top_k: int = MAX_MEMORY_RESULTS) -> str:
        if self.chroma_available:
            try:
                count = self.collection.count()
                if count > 0:
                    results = self.collection.query(
                        query_texts=[current_action],
                        n_results=min(top_k, count)
                    )
                    memories = results.get("documents", [[]])[0]
                    if memories:
                        return "\n".join([f"- {m}" for m in memories])
            except Exception:
                pass
                
        if self.fallback_history:
            recent = self.fallback_history[-top_k:]
            return "\n".join([f"- {m}" for m in recent])
            
        return "No previous memories recorded."