import sys
import numpy as np
import pandas as pd
import mykmeanssp

ERROR_NUM_CLUSTERS = "Incorrect number of clusters!"
ERROR_MAX_ITER = "Incorrect maximum iteration!"
ERROR_EPS = "Incorrect epsilon!"
ERROR_OCCURRED = "An Error Has Occurred"

MAX_ITER_DEFAULT = 300

def print_error(msg):
    print(msg)
    sys.exit(1)

def format_row(row):
    return ",".join(f"{x:.4f}" for x in row)




def parse_args(argv):

    """
    Read the args from the command line of terminal
    And validates all the value if they are correct or not
    Throws error in case it's incorrect
    """

    if len(argv) not in (5, 6):
        print_error(ERROR_OCCURRED)
    
    # K
    try:
        K = int(argv[1])
    except Exception:
        print_error(ERROR_NUM_CLUSTERS)


    # iter is optional
    if len(argv) == 6:
        try:
            max_iter = int(argv[2])
        except Exception:
            print_error(ERROR_MAX_ITER)
        eps_str = argv[3]
        file1 = argv[4]
        file2 = argv[5]
    else:
        max_iter = MAX_ITER_DEFAULT
        eps_str = argv[2]
        file1 = argv[3]
        file2 = argv[4]

    # eps
    try:
        eps = float(eps_str)
    except Exception:
        print_error(ERROR_EPS)

     

    # validations (adjust if your HW requires different constraints)
    if K <= 1:
        print_error(ERROR_NUM_CLUSTERS)
    if max_iter <= 0 or max_iter >= 800:
        print_error(ERROR_MAX_ITER)
    if eps < 0:
        print_error(ERROR_EPS)
   


    return K, max_iter, eps, file1, file2



def load_and_merge(file1: str, file2: str):
    """
    Read file1 and file2 with pandas, inner-join on key column (col 0),
    sort by key.
    Return: (keys, X)
      keys: numpy array shape (N,) of ints
      X: numpy array shape (N, dim) of floats (WITHOUT keys column)
    """

    try:
        df1 = pd.read_csv(file1, header=None)
        df2 = pd.read_csv(file2, header=None)
    except Exception:
        print_error(ERROR_OCCURRED)  
      


    try: 
        df1.rename(columns = {0: 'key'}, inplace = True)
        df2.rename(columns = {0: 'key'}, inplace = True)

        merged = pd.merge(df1, df2, on = 'key', how="inner")
        merged = merged.sort_values('key', ascending=True)
    except Exception:
        print_error(ERROR_OCCURRED)


    try:
        keys = merged["key"].to_numpy(dtype=float)
        data_points = merged.drop(columns=["key"]).to_numpy(dtype=float)
    except Exception:
        print_error(ERROR_OCCURRED)   

    return keys, data_points


def kmeans_pp_init(data_points: np.ndarray, K: int, seed: int = 1234):
    """
    Perform k-means++ initialization in Python.
    Return: (chose_idxs, init_centroids)
      chose_idxs: list of indices in [0..N-1]
      init_centroids: numpy array shape (K, dim)
    """
    np.random.seed(seed)
    N = data_points.shape[0]

    chose_idxs = []

    first_idx = np.random.choice(N)
    chose_idxs.append(first_idx)

    D = np.sqrt(np.sum((data_points - data_points[first_idx]) ** 2, axis=1))

    for i in range(1,K):
        total = D.sum()
        if total == 0.0:
            next_idx = np.random.choice(N)
        else:
            probs = D / total
            next_idx = np.random.choice(N, p=probs)

        chose_idxs.append(next_idx)

        # update D to be min distance to any chosen centroid
        newD = np.sqrt(np.sum((data_points - data_points[next_idx]) ** 2, axis=1))
        D = np.minimum(D, newD)
        
    init_centroids = data_points[chose_idxs].copy()
    return chose_idxs, init_centroids




def run_kmeans_c(K: int, max_iter: int, eps: float, X: np.ndarray, init_centroids: np.ndarray):
    """
    Call the C extension (mykmeanssp.fit).
    Return: final_centroids as list[list[float]] or numpy array.
    """
    pass


def main():
    """
    1) parse args
    2) load+merge+sort
    3) kmeans++ init
    4) print chosen keys
    5) run C kmeans
    6) print final centroids
    
    """
    K, max_iter, eps, file1, file2 = parse_args(sys.argv)
    keys, data_points = load_and_merge(file1, file2)
    N = len(data_points)

    if K >= N:
        print_error(ERROR_NUM_CLUSTERS)

    chose_idxs, init_centroids = kmeans_pp_init(data_points, K)
    
    print(",".join(str(int(keys[i])) for i in chose_idxs))

    
    try:
        final_centroids = mykmeanssp.fit(
            K, max_iter, eps,
            data_points.tolist(),
            init_centroids.tolist()
        )
    except Exception:
        print_error(ERROR_OCCURRED)


    # print final centroids (each row with 4 decimals)
    for row in final_centroids:
        print(format_row(row))

        


if __name__ == "__main__":
    main()