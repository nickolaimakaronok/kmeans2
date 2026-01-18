import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.cluster import KMeans

def main():

    # Load the Iris Dataset
    # The iris dataset contains 150 samples, each with 4 features 
    # (sepal length, sepal width, petal length, petal width).
    iris = load_iris()
    data = iris.data
    
    # List to store the inertia (Sum of Squared Errors) for each k
    inertia_values = []
    
    # Define the range of k (clusters) from 1 to 10
    k_range = range(1, 11)

    
    for k in k_range:
        # Initialize the KMeans model with the specific parameters required:
        # - n_clusters: The current k
        # - init='k-means++': Smart initialization for centroids
        # - random_state=0: Ensures deterministic results (reproducibility)
        kmeans_model = KMeans(n_clusters=k, init='k-means++', random_state=0)
        
        # Fit the model to the data
        kmeans_model.fit(data)
        
        # Append the inertia value (sum of squared distances of samples 
        # to their closest cluster center) to the list.
        inertia_values.append(kmeans_model.inertia_)

    #  Visualize the Results (The Elbow Method)
    plt.figure(figsize=(10, 6))
    
    # Plot the inertia values against the number of clusters
    # 'o-': plots points with a connecting line
    plt.plot(k_range, inertia_values, 'o-', linewidth=2, markersize=8)
    
    # Labeling the axes and the title
    plt.title('Elbow Method for Optimal k (Iris Dataset)', fontsize=16)
    plt.xlabel('Number of Clusters (k)', fontsize=14)
    plt.ylabel('Inertia (Sum of Squared Distances)', fontsize=14)
    
    # Set x-axis ticks to display integers from 1 to 10
    plt.xticks(k_range)
    
    # Add a grid for better readability
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save the figure to a file named 'elbow.png'
    output_filename = 'elbow.png'
    plt.savefig(output_filename)
    
    print(f"Graph saved successfully as '{output_filename}'.")

if __name__ == "__main__":
    main()