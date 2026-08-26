#include <utility>
#include <vector>
#include <iostream>
#include "../../../headers/metafeatures/decomposition_based/weight_vectors_metafeatures.h"

using namespace std;

// This function generates a vector of weight pairs (w1, w2) for a given population size.
vector<pair<double, double>> build_weight_vector_metafeatures(int population_size){
  vector<pair<double, double>> weight_vectors;

  if(population_size == 1){
    // If the population size is 1, only one weight vector (0.5, 0.5) is created.
    weight_vectors.push_back(make_pair(0.5, 0.5));
  }
  else{
    double step = 1.0 / (population_size - 1); // Calculates the step size based on the population size.
    for (int i = 0; i < population_size; ++i) {
      double w1 = step * i; // Calculates the first weight w1.
      double w2 = 1.0 - w1; // Calculates the second weight w2, ensuring that w1 + w2 = 1.
      weight_vectors.push_back(make_pair(w1, w2)); // Adds the pair (w1, w2) to the vector.
    }
  } 

  return weight_vectors; // Returns the vector of weight pairs.
}