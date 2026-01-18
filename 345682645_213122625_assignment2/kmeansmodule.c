#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <stdlib.h>
#include <math.h>
#include <stdio.h>

/*declaration of structs*/
struct vector;
struct cord;

/*declaration of functions*/
double compute_distance(const struct vector *v1, const struct vector *v2, int dim); 
int find_closest_centroid(const struct vector *centroids, const struct vector *vectorX, int K, int dim);
struct vector *add_coordinates_from_other_vector(struct vector *v1, struct vector *v2, int dim);
struct vector *initialize_sum_vectors(int K, int dim);
void divide_vector_by_scalar(struct vector *v, int scalar);
void free_vector_list(struct vector *head_vec); 
void zero_out_vector(struct vector *v);

void free_cords_list(struct cord *head_c);
struct vector* python_to_c_list(PyObject *py_list, int *N, int *dim);
static PyObject* fit(PyObject *self, PyObject *args);
PyMODINIT_FUNC PyInit_mykmeanssp(void);






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



/* Frees all memory allocated for the coordinates */
 void free_cords_list(struct cord *head_c) {
    struct cord *curr;
    struct cord *temp;

    curr = head_c;
    while (curr != NULL) {
        temp = curr;
        curr = curr->next;
        free(temp);
    }
}


/*
 * Converts a Python list of lists (e.g., [[1.0, 2.0], ...]) into a C linked list.
 * * Args:
 * py_list: Pointer to the Python list object.
 * N: Pointer to store the number of vectors found.
 * dim: Pointer to store the dimension of the vectors.
 * * Returns:
 * Pointer to the head of the new C linked list.
 */
struct vector* python_to_c_list(PyObject *py_list, int *N, int *dim) {

    struct vector *head, *curr, *new_vec;
    struct cord *head_c, *curr_c, *new_c;
    PyObject *item, *val;
    Py_ssize_t n, d;
    Py_ssize_t i, j;

    head = NULL;
    curr = NULL;
    n = PyList_Size(py_list);

    *N = (int)n; /* Store number of points */

    for (i = 0; i < n; i++) {
        item = PyList_GetItem(py_list, i);  /* Get the inner list (vector) */
        d = PyList_Size(item);
        *dim = (int)d; /* Store dimension */

        /* Malloc memory for a vector */
        new_vec = malloc(sizeof(struct vector));
        
        /* Check for memory allocation failure */
        if (new_vec == NULL) {
            free_vector_list(head);      /* Clean everything we collected before */
            PyErr_NoMemory();            /* We tell Python there is a mistake: MemoryError */
            return NULL;
        }
        
        new_vec->next = NULL;
        new_vec->cords = NULL; /* We initialiize to be null */

        head_c = NULL;
        curr_c = NULL;

        /* Inner loop: Extract coordinates from Python list */
        for (j = 0; j < d; j++) {
            val = PyList_GetItem(item, j);
            
            new_c = malloc(sizeof(struct cord));
            
            /* protection from MALLOC NULL (inside the loop) */
            if (new_c == NULL) {
                free(new_c);   
                free_cords_list(head_c); /* Clean the cooardinate of current vector */
                free(new_vec);           /* Clean the current vector */
                free_vector_list(head);  /* Clean all the list */
                PyErr_NoMemory();        /* Send the error to Python */
                return NULL;
            }

           /* Convert Python float to C double */


            new_c->value = PyFloat_AsDouble(val);

            /* Check if conversion failed (e.g., item was not a number) */
            if (PyErr_Occurred()) {
                free_cords_list(head_c);
                free(new_vec);
                free_vector_list(head);
                return NULL;
            }

            new_c->next = NULL;
            
            /* Append vector to the main list */
            if (head_c == NULL) { head_c = new_c; curr_c = new_c; }
            else { curr_c->next = new_c; curr_c = curr_c->next; }
        }
        new_vec->cords = head_c;

        if (head == NULL) { head = new_vec; curr = head; }
        else { curr->next = new_vec; curr = curr->next; }
    }
    return head;
}

/*
 * Main K-means algorithm implementation callable from Python.
 * Expected Python args: (K, iter, epsilon, data_list, centroid_list)
 */

static PyObject* fit(PyObject *self, PyObject *args) {
    /* Variable Declarations (ANSI C style - all at top) */
    struct vector *curr_sum;
    struct vector *curr_cent;
    struct vector *head_data;
    struct vector *head_centroids;
    struct vector *sum_head;
    struct vector *curr_vec;
    struct vector *target_sum;
    struct cord *src;
    struct cord *dst;
    struct cord *cent_c;
    struct cord *sum_c;
    struct cord *c;
    int K, iter;
    double epsilon;
    int closest_idx;
    PyObject *data_list, *centroid_list_py;
    PyObject *result_list;
    PyObject *py_vec;
    int *counts;
    int N, dim;
    int i, j;
    int idx;
    int iteration, converged;

    /*  Parse arguments from Python */
    if(!PyArg_ParseTuple(args, "iidOO", &K, &iter, &epsilon, &data_list, &centroid_list_py)) {
        return NULL;
    }

    /*  Convert Python lists to C linked lists */
    head_data = python_to_c_list(data_list, &N, &dim);
    if (!head_data) return NULL;

    /* Convert Python initial centroids list to C linked list */
    head_centroids = python_to_c_list(centroid_list_py, &K, &dim);
    if (!head_centroids) {
        free_vector_list(head_data);
        return NULL;
    }

    /* Initialize helping structures (accumulators) */
    sum_head = initialize_sum_vectors(K, dim);

    if (sum_head == NULL) {
        free_vector_list(head_data);
        free_vector_list(head_centroids);
        PyErr_NoMemory();
        return NULL;
    }

    /* Initialize array to count points in each cluster */
    counts = calloc(K, sizeof(int));

    if (counts == NULL) {
        free_vector_list(head_data);
        free_vector_list(head_centroids);
        free_vector_list(sum_head);
        PyErr_NoMemory();
        return NULL;
    }

    iteration = 0;
    converged = 0;

    /* MAIN K-MEANS LOOP */
    while (iteration < iter && !converged) {
        
        /* Reset accumulators for the new iteration */
        curr_sum = sum_head;
        while(curr_sum != NULL) {
            zero_out_vector(curr_sum);
            curr_sum = curr_sum->next;
        }
        /* Reset counts */
        for(i = 0; i < K; i++) counts[i] = 0;

        /* Assignment Step: assign each point to the closest centroid */
        curr_vec = head_data;
        while(curr_vec != NULL) {
            closest_idx = find_closest_centroid(head_centroids, curr_vec, K, dim);
            counts[closest_idx]++;

            /* Find the corresponding sum vector */
            target_sum = sum_head;
            for(i = 0; i < closest_idx; i++) target_sum = target_sum->next;

            /* Add current point's coordinates to the cluster sum */
            add_coordinates_from_other_vector(target_sum, curr_vec, dim);
            
            curr_vec = curr_vec->next;
        }

        /* Update Step: calculate new centroids */
        converged = 1;
        curr_cent = head_centroids;
        curr_sum = sum_head;
        idx = 0;

        while(curr_cent != NULL) {
            
            /* HANDLING EMPTY CLUSTERS */
            if (counts[idx] == 0) {
                /* If a cluster is empty, copy coordinates from the FIRST data point */
                src = head_data->cords; 
                dst = curr_cent->cords;
                
                while(src != NULL && dst != NULL) {
                    dst->value = src->value; 
                    src = src->next;
                    dst = dst->next;
                }
                /* If we forced a centroid move, convergence is not reached */
                converged = 0; 
            } 
            else {
                /* Normal case: calculate the mean (sum / count) */
                divide_vector_by_scalar(curr_sum, counts[idx]);
                
                /* Check convergence: distance between old and new position */
                if (compute_distance(curr_cent, curr_sum, dim) >= epsilon) {
                    converged = 0;
                }

                /* Update centroid coordinates */
                cent_c = curr_cent->cords;
                sum_c = curr_sum->cords;
                while(cent_c != NULL) {
                    cent_c->value = sum_c->value;
                    cent_c = cent_c->next;
                    sum_c = sum_c->next;
                }
            }
            
            curr_cent = curr_cent->next;
            curr_sum = curr_sum->next;
            idx++;
        }
        iteration++;
    }

    /* Convert result back to Python list */
    result_list = PyList_New(K);
    curr_cent = head_centroids;
    for (i = 0; i < K; i++) {
        py_vec = PyList_New(dim);
        c = curr_cent->cords;
        for (j = 0; j < dim; j++) {
            PyList_SetItem(py_vec, j, PyFloat_FromDouble(c->value));
            c = c->next;
        }
        PyList_SetItem(result_list, i, py_vec);
        curr_cent = curr_cent->next;
    }

    /* Memory Cleanup */
    free_vector_list(head_data);
    free_vector_list(head_centroids);
    free_vector_list(sum_head);
    free(counts);

    return result_list;
}


/* MODULE REGISTRATION CODE */

/* Method definitions table: maps Python method names to C functions */
static PyMethodDef mykmeanssp_methods[] = {
    {
        "fit",                   /* The name of the method as seen in Python */
        (PyCFunction) fit,       /* The actual C function to be called */
        METH_VARARGS,            /* Flags indicating the function accepts positional arguments */
        "Run K-means clustering" /* Function documentation (docstring) */
    },
    {NULL, NULL, 0, NULL}        /* Sentinel value to mark the end of the array */
};

/* Module definition structure */
static struct PyModuleDef mykmeanssp_module = {
    PyModuleDef_HEAD_INIT,
    "mykmeanssp",             /* Module name (must match the name in setup.py) */
    "C extension for K-means",/* Module documentation string */
    -1,                       /* Size of per-interpreter state (using -1 for global state) */
    mykmeanssp_methods        /* Reference to the method table defined above */
};

/* Module initialization function: called when 'import mykmeanssp' is executed */
PyMODINIT_FUNC PyInit_mykmeanssp(void) {
    PyObject *m;
    m = PyModule_Create(&mykmeanssp_module);
    if (!m) {
        return NULL; /* Return NULL to signal an initialization error */
    }
    return m;
}



    

