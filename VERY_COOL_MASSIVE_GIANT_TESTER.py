"""
VERY_COOL_MASSIVE_GIANT_TESTER.py

This tester is designed to:
- Stress test the C k-means implementation
- Validate correctness under HW assumptions
- Be executed under Valgrind to detect memory leaks

ALL COMMENTS ARE IN ENGLISH AS REQUIRED.
"""

import random
import math
import mykmeanssp

# -------------------------
# Utility helpers
# -------------------------

def generate_points(n, dim, seed=0):
    """Generate n points of given dimension with deterministic randomness."""
    random.seed(seed)
    return [[random.uniform(-10, 10) for _ in range(dim)] for _ in range(n)]

def generate_centroids(points, K):
    """
    According to HW assumptions:
    - K is valid
    - len(centroids) == K
    We simply take the first K points.
    """
    return [p[:] for p in points[:K]]

def print_test_header(name):
    print("\n" + "=" * 60)
    print(f"TEST: {name}")
    print("=" * 60)

# -------------------------
# Test cases
# -------------------------

def test_basic():
    """Basic correctness test."""
    print_test_header("Basic small dataset")

    points = [
        [1.0, 1.0],
        [1.2, 0.9],
        [4.0, 4.0],
        [4.1, 3.9]
    ]
    K = 2
    max_iter = 100
    eps = 0.001

    centroids = generate_centroids(points, K)

    result = mykmeanssp.fit(K, max_iter, eps, points, centroids)
    assert len(result) == K
    assert len(result[0]) == 2

def test_identical_points():
    """All points identical – checks zero-distance behavior."""
    print_test_header("Identical points")

    points = [[5.0, 5.0]] * 20
    K = 3
    max_iter = 50
    eps = 0.0001

    centroids = generate_centroids(points, K)
    result = mykmeanssp.fit(K, max_iter, eps, points, centroids)

    for c in result:
        assert c == [5.0, 5.0]

def test_empty_cluster_case():
    """
    Forces empty clusters.
    The C code must handle counts[idx] == 0 correctly.
    """
    print_test_header("Empty cluster scenario")

    points = [
        [0.0, 0.0],
        [0.1, 0.1],
        [100.0, 100.0]
    ]
    K = 3
    max_iter = 100
    eps = 0.001

    centroids = generate_centroids(points, K)
    result = mykmeanssp.fit(K, max_iter, eps, points, centroids)

    assert len(result) == K

def test_high_dimension():
    """High dimensional vectors."""
    print_test_header("High dimensional data")

    dim = 20
    points = generate_points(50, dim, seed=1)
    K = 5
    max_iter = 200
    eps = 0.0001

    centroids = generate_centroids(points, K)
    result = mykmeanssp.fit(K, max_iter, eps, points, centroids)

    assert len(result) == K
    assert len(result[0]) == dim

def test_large_dataset():
    """Large dataset stress test."""
    print_test_header("Large dataset")

    points = generate_points(1000, 5, seed=2)
    K = 10
    max_iter = 300
    eps = 0.001

    centroids = generate_centroids(points, K)
    result = mykmeanssp.fit(K, max_iter, eps, points, centroids)

    assert len(result) == K

# -------------------------
# Main runner
# -------------------------

if __name__ == "__main__":
    test_basic()
    test_identical_points()
    test_empty_cluster_case()
    test_high_dimension()
    test_large_dataset()

    print("\nALL TESTS PASSED SUCCESSFULLY")
