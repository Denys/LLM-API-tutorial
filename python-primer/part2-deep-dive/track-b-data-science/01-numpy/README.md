# Track B, Section 1: NumPy for Embeddings

**Duration:** 45-60 minutes | **Level:** Intermediate

## Why This Matters for LLM APIs

NumPy enables:
- **Fast vector operations** on embeddings (1000x faster than Python lists)
- **Similarity search** for RAG systems
- **Batch processing** of embedding operations
- **Memory efficiency** for large embedding databases

## Concepts

### Array Basics

```python
import numpy as np

# Create arrays
embedding = np.array([0.1, 0.2, 0.3, 0.4])
embeddings = np.zeros((100, 1536))  # 100 embeddings, 1536 dimensions

# Properties
embedding.shape  # (4,)
embedding.dtype  # float64
embeddings.shape  # (100, 1536)
```

### Vector Operations

```python
# Dot product (similarity)
similarity = np.dot(a, b)

# Cosine similarity
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Euclidean distance
distance = np.linalg.norm(a - b)
```

## Examples

### Embedding Similarity Search

```python
# examples/similarity_search.py
"""Vector similarity search for embeddings."""

import numpy as np
from typing import list


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def cosine_similarity_batch(query: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity between query and all embeddings.

    Args:
        query: Query vector (d,)
        embeddings: Matrix of embeddings (n, d)

    Returns:
        Similarities array (n,)
    """
    # Normalize query
    query_norm = query / np.linalg.norm(query)

    # Normalize all embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings_norm = embeddings / norms

    # Dot product gives cosine similarity
    return np.dot(embeddings_norm, query_norm)


def top_k_similar(
    query: np.ndarray,
    embeddings: np.ndarray,
    k: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    """Find top-k most similar embeddings.

    Returns:
        Tuple of (indices, similarities)
    """
    similarities = cosine_similarity_batch(query, embeddings)
    top_indices = np.argsort(similarities)[-k:][::-1]
    return top_indices, similarities[top_indices]


# Usage
if __name__ == "__main__":
    # Simulate embeddings database
    np.random.seed(42)
    num_docs = 1000
    embedding_dim = 1536

    # Random embeddings (in practice, from embedding API)
    embeddings = np.random.randn(num_docs, embedding_dim)

    # Query embedding
    query = np.random.randn(embedding_dim)

    # Find top 5 similar
    indices, scores = top_k_similar(query, embeddings, k=5)

    print("Top 5 similar documents:")
    for idx, score in zip(indices, scores):
        print(f"  Doc {idx}: similarity = {score:.4f}")
```

### Batch Embedding Processing

```python
# examples/batch_processing.py
"""Efficient batch processing of embeddings."""

import numpy as np


def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """Normalize embeddings to unit length.

    Args:
        embeddings: Shape (n, d)

    Returns:
        Normalized embeddings (n, d)
    """
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms


def mean_pooling(embeddings: np.ndarray, weights: np.ndarray = None) -> np.ndarray:
    """Mean pooling of multiple embeddings.

    Args:
        embeddings: Shape (n, d)
        weights: Optional weights (n,)

    Returns:
        Pooled embedding (d,)
    """
    if weights is not None:
        weights = weights / weights.sum()
        return np.average(embeddings, axis=0, weights=weights)
    return np.mean(embeddings, axis=0)


def pairwise_similarities(embeddings: np.ndarray) -> np.ndarray:
    """Calculate pairwise cosine similarities.

    Args:
        embeddings: Shape (n, d)

    Returns:
        Similarity matrix (n, n)
    """
    normalized = normalize_embeddings(embeddings)
    return np.dot(normalized, normalized.T)


def cluster_centroids(embeddings: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Calculate cluster centroids.

    Args:
        embeddings: Shape (n, d)
        labels: Cluster assignments (n,)

    Returns:
        Centroids (num_clusters, d)
    """
    unique_labels = np.unique(labels)
    centroids = np.zeros((len(unique_labels), embeddings.shape[1]))

    for i, label in enumerate(unique_labels):
        mask = labels == label
        centroids[i] = embeddings[mask].mean(axis=0)

    return centroids


# Usage
if __name__ == "__main__":
    # Sample embeddings
    embeddings = np.random.randn(100, 768)

    # Normalize
    normalized = normalize_embeddings(embeddings)
    print(f"Norms after normalization: {np.linalg.norm(normalized, axis=1)[:5]}")

    # Mean pool first 10
    pooled = mean_pooling(embeddings[:10])
    print(f"Pooled shape: {pooled.shape}")

    # Pairwise similarities
    sim_matrix = pairwise_similarities(embeddings[:5])
    print(f"Similarity matrix:\n{sim_matrix}")
```

---

## Exercises

### Simple: Basic Vector Operations

**Task:** Implement functions for:
1. Euclidean distance between two vectors
2. Manhattan distance
3. Dot product similarity

```python
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])
print(euclidean_distance(a, b))  # 5.196...
print(manhattan_distance(a, b))   # 9
print(dot_similarity(a, b))       # 32
```

<details>
<summary>Solution</summary>

```python
import numpy as np

def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    return np.linalg.norm(a - b)

def manhattan_distance(a: np.ndarray, b: np.ndarray) -> float:
    return np.sum(np.abs(a - b))

def dot_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b)
```
</details>

---

### Intermediate: KNN Search

**Task:** Implement k-nearest neighbors search:
1. Calculate distances from query to all points
2. Return indices of k nearest
3. Support both cosine and euclidean distance

<details>
<summary>Solution</summary>

```python
import numpy as np

def knn_search(
    query: np.ndarray,
    data: np.ndarray,
    k: int = 5,
    metric: str = "cosine"
) -> tuple[np.ndarray, np.ndarray]:
    """K-nearest neighbors search."""
    if metric == "cosine":
        # Cosine similarity (higher = closer)
        query_norm = query / np.linalg.norm(query)
        data_norm = data / np.linalg.norm(data, axis=1, keepdims=True)
        distances = 1 - np.dot(data_norm, query_norm)  # Convert to distance
    elif metric == "euclidean":
        distances = np.linalg.norm(data - query, axis=1)
    else:
        raise ValueError(f"Unknown metric: {metric}")

    indices = np.argsort(distances)[:k]
    return indices, distances[indices]
```
</details>

---

### Advanced: Embedding Index with HNSW-like Structure

**Task:** Build a simple approximate nearest neighbor index:
1. Partition embeddings into clusters
2. Search only relevant clusters
3. Benchmark against brute force

<details>
<summary>Solution</summary>

```python
import numpy as np
from sklearn.cluster import KMeans

class SimpleANNIndex:
    """Simple approximate nearest neighbor index."""

    def __init__(self, n_clusters: int = 10):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.embeddings = None
        self.cluster_assignments = None

    def build(self, embeddings: np.ndarray):
        """Build index from embeddings."""
        self.embeddings = embeddings
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
        self.cluster_assignments = self.kmeans.fit_predict(embeddings)

    def search(self, query: np.ndarray, k: int = 5, n_probe: int = 3) -> tuple:
        """Search for k nearest neighbors."""
        # Find nearest clusters
        cluster_distances = np.linalg.norm(
            self.kmeans.cluster_centers_ - query, axis=1
        )
        nearest_clusters = np.argsort(cluster_distances)[:n_probe]

        # Search within those clusters
        candidates = []
        for cluster_id in nearest_clusters:
            mask = self.cluster_assignments == cluster_id
            indices = np.where(mask)[0]
            candidates.extend(indices)

        # Exact search among candidates
        candidate_embeddings = self.embeddings[candidates]
        similarities = np.dot(candidate_embeddings, query) / (
            np.linalg.norm(candidate_embeddings, axis=1) * np.linalg.norm(query)
        )

        top_k = np.argsort(similarities)[-k:][::-1]
        return np.array(candidates)[top_k], similarities[top_k]
```
</details>

---

## Pro Tips

### 1. Use Float32 for Embeddings

```python
embeddings = embeddings.astype(np.float32)  # Half the memory
```

### 2. Vectorize Everything

```python
# Bad - Python loop
similarities = []
for emb in embeddings:
    sim = np.dot(query, emb)
    similarities.append(sim)

# Good - Vectorized
similarities = np.dot(embeddings, query)
```

### 3. Memory-Mapped Arrays for Large Data

```python
# Save to disk
np.save("embeddings.npy", embeddings)

# Memory-map for large files
embeddings = np.load("embeddings.npy", mmap_mode='r')
```

### 4. Batch Operations

```python
# Process in batches to avoid memory issues
batch_size = 1000
results = []
for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    results.append(process(batch))
```

---

## Next Section

[Section 2: Pandas for Analytics →](../02-pandas/)
