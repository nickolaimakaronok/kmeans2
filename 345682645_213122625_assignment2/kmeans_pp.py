import sys
import numpy as np
import pandas as pd
import mykmeanssp


# Constants for Error Messages
ERROR_NUM_CLUSTERS = "Incorrect number of clusters!"
ERROR_MAX_ITER = "Incorrect maximum iteration!"
ERROR_EPS = "Incorrect epsilon!"
ERROR_OCCURRED = "An Error Has Occurred"

MAX_ITER_DEFAULT = 300

def print_error(msg):
    """
    Helper function to print an error message and exit the program immediately.
    We exit with code 1 to indicate failure.
    """
    print(msg)
    sys.exit(1)

def format_row(row):
    """
    Helper function to format a list of floats (a centroid) into a string.
    Each number is formatted to 4 decimal places, separated by commas.
    """
    return ",".join(f"{x:.4f}" for x in row)


def parse_args(argv):

    """
    Read the args from the command line of terminal
    And validates all the value if they are correct or not
    Throws error in case it's incorrect
    """

    # Check if we received the correct number of arguments (filename + 4 or 5 args
    if len(argv) not in (5, 6):
        print_error(ERROR_OCCURRED)
    
    # Parse K (Number of clusters)
    try:
        K = int(argv[1])
    except Exception:
        print_error(ERROR_NUM_CLUSTERS)


    # Parse max_iter (Optional argument)
    # If 6 arguments are provided, max_iter is at index 2
    if len(argv) == 6:
        try:
            max_iter = int(argv[2])
        except Exception:
            print_error(ERROR_MAX_ITER)
        eps_str = argv[3]
        file1 = argv[4]
        file2 = argv[5]
    else:
        # If 5 arguments are provided, max_iter is skipped, so we use the default.
        max_iter = MAX_ITER_DEFAULT
        eps_str = argv[2]
        file1 = argv[3]
        file2 = argv[4]

    # Parse Epsilon (Convergence threshold)
    try:
        eps = float(eps_str)
    except Exception:
        print_error(ERROR_EPS)


    # Logical Validations (Sanity Checks)
    # K must be greater than 1
    if K <= 1:
        print_error(ERROR_NUM_CLUSTERS)
    if max_iter <= 0 or max_iter >= 800:
        print_error(ERROR_MAX_ITER)
    # epsilon cannot be negative    
    if eps < 0:
        print_error(ERROR_EPS)

    return K, max_iter, eps, file1, file2



def load_and_merge(file1: str, file2: str):
    """
    Reads two input files using Pandas.
    Performs an inner join on the first column (Key) and sorts the result.
    Returns:
      keys: A numpy array of the IDs.
      data_points: A numpy array of the coordinates (without the IDs).
    """

    try:
        # Read files as CSVs without a header row
        df1 = pd.read_csv(file1, header=None)
        df2 = pd.read_csv(file2, header=None)
    except Exception:
        print_error(ERROR_OCCURRED)  
      


    try: 
        # Rename the first column to 'key' to allow merging
        df1.rename(columns = {0: 'key'}, inplace = True)
        df2.rename(columns = {0: 'key'}, inplace = True)

        # Perform an inner join: keep only keys present in BOTH files
        merged = pd.merge(df1, df2, on = 'key', how="inner")
        # Sort the data by key (ascending) to ensure consistent order
        merged = merged.sort_values('key', ascending=True)
    except Exception:
        print_error(ERROR_OCCURRED)


    try:
        # Separate the Keys from the Data
        keys = merged["key"].to_numpy(dtype=float)
        # Drop the key column to keep only coordinates
        data_points = merged.drop(columns=["key"]).to_numpy(dtype=float)
    except Exception:
        print_error(ERROR_OCCURRED)   

    return keys, data_points


def kmeans_pp_init(data_points: np.ndarray, K: int, seed: int = 1234):
    """
    Implements the K-Means++ initialization algorithm.
    This selects the initial centroids in a smart way to speed up convergence.
    """

    # Set the seed for reproducibility (so we always get the same result for the same input)
    np.random.seed(seed)
    N = data_points.shape[0]

    chose_idxs = []

    # Choose the first centroid completely at random
    first_idx = np.random.choice(N)
    chose_idxs.append(first_idx)

    # Calculate initial distances from all points to the first centroid
    D = np.sqrt(np.sum((data_points - data_points[first_idx]) ** 2, axis=1))

    # Choose the remaining K-1 centroids
    for i in range(1,K):
        total = D.sum()

        # Calculate probability for each point:
        # Points further away (larger D) have a higher chance of being picked
        if total == 0.0:
            next_idx = np.random.choice(N)
        else:
            probs = D / total
            next_idx = np.random.choice(N, p=probs)

        chose_idxs.append(next_idx)

        # Update distances:
        # For every point, check if the NEW centroid is closer than the previous ones.
        # Keep the minimum distance.
        newD = np.sqrt(np.sum((data_points - data_points[next_idx]) ** 2, axis=1))
        D = np.minimum(D, newD)
        
    # Get the actual coordinates of the chosen points
    init_centroids = data_points[chose_idxs].copy()
    
    return chose_idxs, init_centroids


def main():
    """
    Main execution flow:
    1. Parse arguments.
    2. Load and prepare data.
    3. Run K-Means++ initialization.
    4. Print the keys of the initial centroids.
    5. Run the C extension for the heavy calculations.
    6. Print the final centroids.
    """


    # Get arguments from command line
    K, max_iter, eps, file1, file2 = parse_args(sys.argv)

    # Load data from files
    keys, data_points = load_and_merge(file1, file2)
    N = len(data_points)

    # Validation: K cannot be larger than the number of data points
    if K >= N:
        print_error(ERROR_NUM_CLUSTERS)

    # Run K-Means++ Initialization
    chose_idxs, init_centroids = kmeans_pp_init(data_points, K)
    
    # Print the keys (IDs) of the chosen initial centroids
    print(",".join(str(int(keys[i])) for i in chose_idxs))

    # Call the C module
    # We convert numpy arrays to Python lists because our C module expects lists.
    try:
        final_centroids = mykmeanssp.fit(
            K, max_iter, eps,
            data_points.tolist(),
            init_centroids.tolist()
        )
    except Exception:
        print_error(ERROR_OCCURRED)


    # Print the final results
    # Format each coordinate to 4 decimal places
    for row in final_centroids:
        print(format_row(row))

        


if __name__ == "__main__":
    main()