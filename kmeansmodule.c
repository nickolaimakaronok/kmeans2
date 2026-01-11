#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <stdlib.h>
#include <math.h>
#define _GNU_SOURCE 
#include <stdio.h>

#define ERROR_NUM_CLUSTERS "Incorrect number of clusters!"
#define ERROR_MAX_ITER "Incorrect maximum iteration!"
#define ERROR_OCCURED "An Error Has Occurred"
#define MAX_ITER_DEFAULT 400  /* Default maximum iterations */ 
#define EPS 0.001

/*declaration of structs*/
struct vector;
struct cord;

/*declaration of functions*/
int isInteger(char *str);
double compute_distance(const struct vector *v1, const struct vector *v2, int dim); 
int find_dim(const struct vector *vec);
struct vector *initialize_centroids(const struct vector *head_vec, int K, int dim);
int find_closest_centroid(const struct vector *centroids, const struct vector *vectorX, int K, int dim);
struct vector *add_coordinates_from_other_vector(struct vector *v1, struct vector *v2, int dim);
struct vector *initialize_sum_vectors(int K, int dim);
void divide_vector_by_scalar(struct vector *v, int scalar);
void free_vector_list(struct vector *head_vec); 
void zero_out_vector(struct vector *v);

/*implementations of structs*/
struct cord
{
    double value;
    struct cord *next; /* Points to the next dimension/coordinate in the vector */
};
struct vector
{
    struct vector *next; /* Points to the next data point (vector) in the list */
    struct cord *cords; /* Points to the head of the coordinates list for this vector */
};


/* Frees all memory allocated for the vectors and their internal coordinate lists */
void free_vector_list(struct vector *head_vec) {
    struct vector *curr_vec = head_vec;
    struct vector *next_vec;
    struct cord *curr_c, *next_c;

    while (curr_vec != NULL) {
        curr_c = curr_vec->cords;
        while (curr_c != NULL) {
            next_c = curr_c->next;
            free(curr_c);
            curr_c = next_c;
        }
        next_vec = curr_vec->next;
        free(curr_vec);
        curr_vec = next_vec;
    }
}

/* Resets all coordinates of a given vector to 0.0*/
void zero_out_vector(struct vector *v) {
    struct cord *c = v->cords;

    while (c != NULL) {
        c->value = 0.0;
        c = c->next;
    }
}


/*
 * Adds the coordinate values of vector v2 to vector v1.
 * v1 is modified in place (accumulating the sum), while v2 remains unchanged.
 */
struct vector *add_coordinates_from_other_vector(struct vector *v1, struct vector *v2, int dim) {
    struct cord *curr_cord1 = v1->cords;
    const struct cord *curr_cord2 = v2->cords;
    int i;

    for (i = 0; i < dim; i++) {
        /* Add the value from the second vector to the first */
        curr_cord1->value += curr_cord2->value;

        /* Move to the next coordinate */
        curr_cord1 = curr_cord1->next;
        curr_cord2 = curr_cord2->next;
    }

    return v1; /* Return the modified vector (useful for chaining) */
}

/*
 * Divides every coordinate in vector v by a scalar integer.
 * This is used in the Update Step to calculate the average (mean) of a cluster.
 */
void divide_vector_by_scalar(struct vector *v, int scalar) {
    struct cord *c = v->cords;
    while(c != NULL) {
        c->value /= scalar;
        c = c->next;
    }
}


/*
 * Allocates memory for K vectors, initialized to zero.
 * These vectors serve as accumulators for calculating new centroids during iterations.
 * Returns a pointer to the head of the list, or NULL if allocation fails.
 */
struct vector *initialize_sum_vectors(int K, int dim) {
    struct vector *head_v=NULL, *curr_v=NULL, *new_v;
    struct cord *head_c, *curr_c;
    int i,j;

    for(i = 0; i<K; i++) {
        new_v = malloc(sizeof(struct vector));
        if(new_v == NULL) {
            free_vector_list(head_v);
            return NULL;
        }

        new_v->next = NULL;

        head_c = malloc(sizeof(struct cord));
        if(head_c == NULL) {
            free(new_v);
            free_vector_list(head_v);
            return NULL;
        }
        curr_c = head_c;

        for(j = 0; j<dim; j++) {
            curr_c->value = 0.0;
            if(j<dim-1) {
                curr_c->next = malloc(sizeof(struct cord));

                if(curr_c->next == NULL) {
                    new_v->cords = head_c;
                    if(head_v == NULL) {
                        head_v = new_v;
                    } else {
                        curr_v->next = new_v;
                    }
                     free_vector_list(head_v);
                     return NULL;
                }

                curr_c = curr_c->next;
            } else {
                curr_c->next = NULL;
            }

        }

       new_v->cords = head_c;

       if(head_v == NULL) {
          head_v = new_v;
          curr_v = head_v;
       } else {
          curr_v->next = new_v;
          curr_v = curr_v->next;
       }

    }
    return head_v;
}


/*
 * Creates a deep copy of the first K vectors from the input list to serve as initial centroids.
 * Returns the head of the new centroid list, or NULL on failure.
 */
struct vector *initialize_centroids(const struct vector *head_vec, int K, int dim) {
    struct vector *head_centroid=NULL, *curr_centroid=NULL, *new_centroid;
    const struct vector *source_v = head_vec;
    struct cord *head_cord, *curr_cord;
    const struct cord *source_c;
    int i,j;
    
    for(i=0; i<K && source_v != NULL;i++) {
        new_centroid = malloc(sizeof(struct vector));
        if(new_centroid == NULL) {
            free_vector_list(head_centroid);
            return NULL;
        }
        new_centroid->next = NULL;
        source_c = source_v->cords;
        head_cord = malloc(sizeof(struct cord));
        if(head_cord == NULL) {
            free(new_centroid);
            free_vector_list(head_centroid);
            return NULL;
        }
        curr_cord = head_cord;

        for(j=0; j<dim; j++) {
            curr_cord->value = source_c->value;
            source_c = source_c->next;
            
            if(j <dim -1) {
                curr_cord->next = malloc(sizeof(struct cord));
                if(curr_cord->next == NULL) {
                    new_centroid->cords = head_cord;
                    
                    if(head_centroid == NULL) {
                        head_centroid = new_centroid;
                    } else {
                        curr_centroid->next = new_centroid;
                    }

                    free_vector_list(head_centroid);
                    return NULL;
                }
                curr_cord = curr_cord->next;

            } else {
                curr_cord->next = NULL;
            }
        }

           new_centroid->cords = head_cord;
           
           if(head_centroid == NULL) {
            head_centroid = new_centroid;
            curr_centroid = head_centroid;
           } else {
            curr_centroid->next = new_centroid;
            curr_centroid = curr_centroid->next;
           }

        source_v = source_v->next;   
    }
    return head_centroid;
}



/*
 * Calculates the Euclidean distance between two vectors (points). 
 * It iterates through the coordinates, sums the squared differences, 
 * and returns the square root of that sum.
 */
double compute_distance(const struct vector *v1, const struct vector *v2, int dim) {
    double diff;
    double cord_val1, cord_val2;
    double distance;
    struct cord *curr_cord1, *curr_cord2;
    int i;
    double sum_dist = 0.0;
    curr_cord1 = v1->cords;
    curr_cord2 = v2->cords;
    
    for(i = 0; i<dim; i++) {

        if (curr_cord1 == NULL || curr_cord2 == NULL) {
            return 0.0; 
        }

        cord_val1 = (*curr_cord1).value;
        cord_val2 = (*curr_cord2).value;
        diff = cord_val1 - cord_val2;
        sum_dist += diff * diff;
        curr_cord1 = curr_cord1->next;
        curr_cord2 = curr_cord2->next;
    }
    distance = sqrt(sum_dist);
    return distance;
}


/*
 * Determines the dimensionality (number of coordinates) of a vector 
 * by counting the length of its coordinate linked list.
 */
int find_dim(const struct vector *vec)
{
    int dim = 0;
    const struct cord *c;

    if (vec == NULL) {
        return 0;
    }

    c = vec->cords;
    while (c != NULL) {
        dim++;
        c = c->next;
    }

    return dim;
}

/*
 * Validates if a string represents a positive integer.
 * Returns 1 if valid, 0 otherwise.
 */
int isInteger(char *str) {

    if (str == NULL || *str == '\0') {
        return 0; 
    }
    
    while (*str) {
        if (*str < '0' || *str > '9') {
            return 0; 
        }
        str++;
    }
    return 1; 
}

/*
 * Iterates through all centroids to find the one closest to vectorX.
 * Returns the index (0 to K-1) of the closest centroid.
 */
int find_closest_centroid(const struct vector *centroids, const struct vector *vectorX, int K, int dim) {
    int min_index = 0;
    int i;
    const struct vector *curr_centroid = centroids;
    double distance, min_distance;
    min_distance = compute_distance(curr_centroid, vectorX, dim);
    curr_centroid = curr_centroid->next;
    for(i = 1; i<K; i++) {
        distance = compute_distance(curr_centroid, vectorX, dim);
        if(distance<min_distance) {
            min_distance = distance;
            min_index = i;
        }
        curr_centroid = curr_centroid->next;
    }
    return min_index;
}

