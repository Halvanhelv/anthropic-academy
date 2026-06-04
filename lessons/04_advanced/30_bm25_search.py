import re
import math
from collections import Counter


# --- Chunking ---
def chunk_by_section(document_text):
    return re.split(r"\n## ", document_text)


# --- BM25 Index ---
class BM25Index:
    def __init__(self, k1=1.5, b=0.75):
        self.documents = []
        self._corpus_tokens = []
        self._doc_len = []
        self._doc_freqs = {}
        self._avg_doc_len = 0.0
        self._idf = {}
        self._index_built = False
        self.k1 = k1
        self.b = b

    def _tokenize(self, text):
        tokens = re.split(r"\W+", text.lower())
        return [t for t in tokens if t]

    def add_document(self, document):
        content = document["content"]
        doc_tokens = self._tokenize(content)
        self.documents.append(document)
        self._corpus_tokens.append(doc_tokens)
        self._doc_len.append(len(doc_tokens))
        seen = set()
        for token in doc_tokens:
            if token not in seen:
                self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1
                seen.add(token)
        self._index_built = False

    def _build_index(self):
        N = len(self.documents)
        self._avg_doc_len = sum(self._doc_len) / N if N else 0
        self._idf = {}
        for term, freq in self._doc_freqs.items():
            self._idf[term] = math.log(((N - freq + 0.5) / (freq + 0.5)) + 1)
        self._index_built = True

    def _score(self, query_tokens, doc_index):
        score = 0.0
        doc_counts = Counter(self._corpus_tokens[doc_index])
        doc_len = self._doc_len[doc_index]
        for token in query_tokens:
            if token not in self._idf:
                continue
            idf = self._idf[token]
            tf = doc_counts.get(token, 0)
            numerator = idf * tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self._avg_doc_len))
            score += numerator / (denominator + 1e-9)
        return score

    def search(self, query_text, k=1, norm_factor=0.1):
        if not self._index_built:
            self._build_index()
        query_tokens = self._tokenize(query_text)
        raw_scores = []
        for i in range(len(self.documents)):
            raw = self._score(query_tokens, i)
            if raw > 1e-9:
                raw_scores.append((raw, self.documents[i]))
        raw_scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for raw, doc in raw_scores[:k]:
            normalized = math.exp(-norm_factor * raw)
            results.append((doc, normalized))
        results.sort(key=lambda x: x[1])
        return results


# ============================================
# BM25 LEXICAL SEARCH
# ============================================

# Step 1: Chunk
with open("report.md", "r") as f:
    text = f.read()
chunks = chunk_by_section(text)

# Step 2: Add to BM25 store
store = BM25Index()
for chunk in chunks:
    store.add_document({"content": chunk})
print(f"BM25 index: {len(store.documents)} documents")

# Step 3: Search
queries = [
    "What happened with INC-2023-Q4-011?",
    "What did the software engineering department do?",
    "Tell me about XDR-471 syndrome",
]

for query in queries:
    print(f"\nQuery: '{query}'")
    results = store.search(query, k=3)
    for doc, distance in results:
        first_line = doc["content"].strip().split("\n")[0][:80]
        print(f"  distance={distance:.4f}: {first_line}")
