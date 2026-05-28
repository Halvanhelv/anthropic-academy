import re


# --- Strategy 1: Size-based chunking ---
def chunk_by_char(text, chunk_size=150, chunk_overlap=20):
    chunks = []
    start_idx = 0
    while start_idx < len(text):
        end_idx = min(start_idx + chunk_size, len(text))
        chunks.append(text[start_idx:end_idx])
        start_idx = end_idx - chunk_overlap if end_idx < len(text) else len(text)
    return chunks


# --- Strategy 2: Sentence-based chunking ---
def chunk_by_sentence(text, max_sentences_per_chunk=5, overlap_sentences=1):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    start_idx = 0
    while start_idx < len(sentences):
        end_idx = min(start_idx + max_sentences_per_chunk, len(sentences))
        chunks.append(" ".join(sentences[start_idx:end_idx]))
        start_idx += max_sentences_per_chunk - overlap_sentences
        if start_idx < 0:
            start_idx = 0
    return chunks


# --- Strategy 3: Structure-based chunking (Markdown sections) ---
def chunk_by_section(document_text):
    pattern = r"\n## "
    return re.split(pattern, document_text)


# === Load document ===
with open("report.md", "r") as f:
    text = f.read()

print(f"Document length: {len(text)} characters")
print()

# === Test 1: Size-based ===
print("=" * 60)
print("Strategy 1: Size-based (150 chars, 20 overlap)")
print("=" * 60)
chunks = chunk_by_char(text, chunk_size=150, chunk_overlap=20)
print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks[:3]):
    print(f"\n--- Chunk {i+1} ({len(chunk)} chars) ---")
    print(chunk)

# === Test 2: Sentence-based ===
print("\n" + "=" * 60)
print("Strategy 2: Sentence-based (5 sentences, 1 overlap)")
print("=" * 60)
chunks = chunk_by_sentence(text, max_sentences_per_chunk=5, overlap_sentences=1)
print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks[:3]):
    print(f"\n--- Chunk {i+1} ({len(chunk)} chars) ---")
    print(chunk[:200] + "...")

# === Test 3: Structure-based ===
print("\n" + "=" * 60)
print("Strategy 3: Structure-based (Markdown ## sections)")
print("=" * 60)
chunks = chunk_by_section(text)
print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks):
    first_line = chunk.strip().split("\n")[0]
    print(f"  Chunk {i+1}: {first_line[:80]}  ({len(chunk)} chars)")
