from dotenv import load_dotenv
load_dotenv()

import re
import math
import time
import voyageai

client = voyageai.Client()


# --- Chunking ---
def chunk_by_section(document_text):
    pattern = r"\n## "
    return re.split(pattern, document_text)


# --- Embedding (handles single string or list) ---
def generate_embedding(chunks, model="voyage-3-large", input_type="query"):
    is_list = isinstance(chunks, list)
    inp = chunks if is_list else [chunks]
    result = client.embed(inp, model=model, input_type=input_type)
    return result.embeddings if is_list else result.embeddings[0]


# --- Vector Database ---
class VectorIndex:
    def __init__(self, distance_metric="cosine"):
        self.vectors = []
        self.documents = []
        self._vector_dim = None
        self._distance_metric = distance_metric

    def add_vector(self, vector, document):
        if not self.vectors:
            self._vector_dim = len(vector)
        self.vectors.append(list(vector))
        self.documents.append(document)

    def search(self, query_vector, k=1):
        if not self.vectors:
            return []
        distances = []
        for i, stored in enumerate(self.vectors):
            dist = self._cosine_distance(query_vector, stored)
            distances.append((dist, self.documents[i]))
        distances.sort(key=lambda x: x[0])
        return [(doc, dist) for dist, doc in distances[:k]]

    def _cosine_distance(self, vec1, vec2):
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(x * x for x in vec1))
        mag2 = math.sqrt(sum(x * x for x in vec2))
        if mag1 == 0 or mag2 == 0:
            return 1.0
        similarity = dot / (mag1 * mag2)
        similarity = max(-1.0, min(1.0, similarity))
        return 1.0 - similarity

    def __len__(self):
        return len(self.vectors)

    def __repr__(self):
        return f"VectorIndex(count={len(self)}, dim={self._vector_dim})"


# ============================================
# FULL RAG PIPELINE
# ============================================

# Step 1: Load and chunk document
print("Step 1: Chunking document...")
with open("report.md", "r") as f:
    text = f.read()
chunks = chunk_by_section(text)
print(f"  {len(chunks)} chunks created")

# Step 2: Generate embeddings for all chunks
print("Step 2: Generating embeddings...")
embeddings = generate_embedding(chunks, input_type="document")
print(f"  {len(embeddings)} embeddings, {len(embeddings[0])} dimensions each")

# Step 3: Store in vector database
print("Step 3: Storing in vector index...")
store = VectorIndex()
for embedding, chunk in zip(embeddings, chunks):
    store.add_vector(embedding, {"content": chunk})
print(f"  {store}")

# === PREPROCESSING DONE. Now wait for user query. ===
print("\n--- Preprocessing complete. Ready for queries. ---\n")

# Step 4: User asks a question
queries = [
    "What did the software engineering department do last year?",
    "What risk factors does this company have?",
    "Tell me about the pharmaceutical research",
]

for i, query in enumerate(queries):
    if i > 0:
        time.sleep(25)
    print(f"Query: '{query}'")

    # Step 4: Embed the query
    query_embedding = generate_embedding(query, input_type="query")

    # Step 5: Search for top 2 most relevant chunks
    results = store.search(query_embedding, k=2)

    for i, (doc, distance) in enumerate(results):
        first_line = doc["content"].strip().split("\n")[0][:80]
        print(f"  #{i+1} (distance={distance:.4f}): {first_line}")
    print()
