from dotenv import load_dotenv
load_dotenv()

import re
import voyageai

client = voyageai.Client()


# --- Chunking (from previous lesson) ---
def chunk_by_section(document_text):
    pattern = r"\n## "
    return re.split(pattern, document_text)


# --- Embedding generation ---
def generate_embedding(text, model="voyage-3-large", input_type="query"):
    result = client.embed([text], model=model, input_type=input_type)
    return result.embeddings[0]


# === Load and chunk document ===
with open("report.md", "r") as f:
    text = f.read()

chunks = chunk_by_section(text)
print(f"Document chunked into {len(chunks)} sections")

# === Generate embedding for first chunk ===
print(f"\nGenerating embedding for chunk 0: '{chunks[0].strip()[:60]}...'")
embedding = generate_embedding(chunks[0])
print(f"Embedding dimensions: {len(embedding)}")
print(f"First 10 values: {embedding[:10]}")
print(f"Value range: [{min(embedding):.4f}, {max(embedding):.4f}]")

# === Generate embedding for a query ===
query = "What risk factors does this company have?"
print(f"\nQuery: '{query}'")
query_embedding = generate_embedding(query, input_type="query")
print(f"Query embedding dimensions: {len(query_embedding)}")
print(f"First 10 values: {query_embedding[:10]}")
