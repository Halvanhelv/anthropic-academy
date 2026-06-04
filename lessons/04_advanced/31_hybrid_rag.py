from dotenv import load_dotenv
load_dotenv()

import re
import math
from collections import Counter
import voyageai

vo_client = voyageai.Client()


# --- Chunking ---
def chunk_by_section(document_text):
    return re.split(r"\n## ", document_text)


# --- Embedding ---
def generate_embedding(chunks, model="voyage-3-large", input_type="query"):
    is_list = isinstance(chunks, list)
    inp = chunks if is_list else [chunks]
    result = vo_client.embed(inp, model=model, input_type=input_type)
    return result.embeddings if is_list else result.embeddings[0]


# --- VectorIndex (semantic search) ---
class VectorIndex:
    def __init__(self, embedding_fn=None):
        self.vectors = []
        self.documents = []
        self._vector_dim = None
        self._embedding_fn = embedding_fn

    def add_document(self, document):
        vector = self._embedding_fn(document["content"])
        self.add_vector(vector, document)

    def add_documents(self, documents):
        contents = [d["content"] for d in documents]
        vectors = self._embedding_fn(contents)
        for vector, doc in zip(vectors, documents):
            self.add_vector(vector, doc)

    def add_vector(self, vector, document):
        if not self.vectors:
            self._vector_dim = len(vector)
        self.vectors.append(list(vector))
        self.documents.append(document)

    def search(self, query, k=1):
        if isinstance(query, str):
            query_vector = self._embedding_fn(query)
        else:
            query_vector = query
        distances = []
        for i, stored in enumerate(self.vectors):
            dot = sum(a * b for a, b in zip(query_vector, stored))
            mag1 = math.sqrt(sum(x * x for x in query_vector))
            mag2 = math.sqrt(sum(x * x for x in stored))
            sim = dot / (mag1 * mag2) if mag1 and mag2 else 0
            distances.append((1.0 - sim, self.documents[i]))
        distances.sort(key=lambda x: x[0])
        return [(doc, dist) for dist, doc in distances[:k]]


# --- BM25Index (lexical search) ---
class BM25Index:
    def __init__(self, k1=1.5, b=0.75):
        self.documents = []
        self._corpus_tokens = []
        self._doc_len = []
        self._doc_freqs = {}
        self._idf = {}
        self._index_built = False
        self.k1, self.b = k1, b

    def _tokenize(self, text):
        return [t for t in re.split(r"\W+", text.lower()) if t]

    def add_document(self, document):
        tokens = self._tokenize(document["content"])
        self.documents.append(document)
        self._corpus_tokens.append(tokens)
        self._doc_len.append(len(tokens))
        seen = set()
        for t in tokens:
            if t not in seen:
                self._doc_freqs[t] = self._doc_freqs.get(t, 0) + 1
                seen.add(t)
        self._index_built = False

    def add_documents(self, documents):
        for doc in documents:
            self.add_document(doc)

    def _build_index(self):
        N = len(self.documents)
        self._avg_doc_len = sum(self._doc_len) / N if N else 0
        self._idf = {t: math.log(((N - f + 0.5) / (f + 0.5)) + 1) for t, f in self._doc_freqs.items()}
        self._index_built = True

    def search(self, query, k=1, norm_factor=0.1):
        if not self._index_built:
            self._build_index()
        tokens = self._tokenize(query)
        raw = []
        for i in range(len(self.documents)):
            score = 0.0
            counts = Counter(self._corpus_tokens[i])
            dl = self._doc_len[i]
            for t in tokens:
                if t not in self._idf:
                    continue
                tf = counts.get(t, 0)
                score += (self._idf[t] * tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (dl / self._avg_doc_len)) + 1e-9)
            if score > 1e-9:
                raw.append((score, self.documents[i]))
        raw.sort(key=lambda x: x[0], reverse=True)
        results = [(d, math.exp(-norm_factor * s)) for s, d in raw[:k]]
        results.sort(key=lambda x: x[1])
        return results


# --- Retriever (hybrid search with RRF) ---
class Retriever:
    def __init__(self, *indexes):
        self._indexes = list(indexes)

    def add_document(self, document):
        for index in self._indexes:
            index.add_document(document)

    def add_documents(self, documents):
        for index in self._indexes:
            index.add_documents(documents)

    def search(self, query_text, k=1, k_rrf=60):
        all_results = [index.search(query_text, k=k * 5) for index in self._indexes]

        doc_ranks = {}
        for idx, results in enumerate(all_results):
            for rank, (doc, _) in enumerate(results):
                doc_id = id(doc)
                if doc_id not in doc_ranks:
                    doc_ranks[doc_id] = {"doc": doc, "ranks": [float("inf")] * len(self._indexes)}
                doc_ranks[doc_id]["ranks"][idx] = rank + 1

        scored = []
        for info in doc_ranks.values():
            rrf = sum(1.0 / (k_rrf + r) for r in info["ranks"] if r != float("inf"))
            if rrf > 0:
                scored.append((info["doc"], rrf))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


# ============================================
# HYBRID RAG PIPELINE
# ============================================

# Load and chunk
with open("report.md", "r") as f:
    text = f.read()
chunks = chunk_by_section(text)
print(f"{len(chunks)} chunks")

# Create indexes
vector_index = VectorIndex(embedding_fn=generate_embedding)
bm25_index = BM25Index()
retriever = Retriever(bm25_index, vector_index)

# Add all chunks (one API call for embeddings)
print("Indexing chunks...")
retriever.add_documents([{"content": chunk} for chunk in chunks])
print("Done.\n")

# Search
queries = [
    "What happened with INC-2023-Q4-011?",
    "What did the software engineering department do?",
    "Tell me about XDR-471 syndrome",
]

for query in queries:
    print(f"Query: '{query}'")
    results = retriever.search(query, k=3)
    for doc, score in results:
        first_line = doc["content"].strip().split("\n")[0][:80]
        print(f"  RRF={score:.4f}: {first_line}")
    print()
