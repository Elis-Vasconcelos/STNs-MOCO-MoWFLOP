#include <vector>
#include <utility>
#include <iostream>
#include <cmath>
#include <algorithm> 
#include "../../../../headers/metaheuristics/moead/modules/generate_neighborhood.h"
using namespace std;

//Function to calculate the Euclidean distance between two weight vectors
double euclidean_distance(pair<double, double>& a, pair<double, double>& b) {
  return sqrt(pow(a.first - b.first, 2) + pow(a.second - b.second, 2));
}

vector<vector<int>> build_neighborhood(int number_of_neighbors, vector<pair<double, double>>& lambda_vector, int size_population){

  /*Contains all the indices of the neighbors of a given lambda vector i.
  Ex: for the lambda vector (subproblem) i, there is a vector of neighbors, i.e. a vector of neighbors of indices j*/
  vector<vector<int>> neighborhood(size_population);

  //The number of neighbors cannot be greater than the population size minus 1.
  if (number_of_neighbors > size_population - 1) {
    throw runtime_error("ERROR - MOEAD: generate_neighbood ==> The number of neighbors cannot be greater than the population size minus 1.");
  }

  //Building the neighborhood of a lambda vector (subproblem) i by fingind the 't' nearest neighbors of i. t = number_of_neighbors
  // For each weight vector i
  for (int i = 0; i < lambda_vector.size(); i++) {
    vector<pair<double, int>> distances; 

    // Calculate the distance from the weight vector i to all other vectors
    for (int j = 0; j < lambda_vector.size(); j++) {
      if (i != j) {  // Avoid calculating the distance from a vector to itself
        double distance = euclidean_distance(lambda_vector[i], lambda_vector[j]);
        distances.push_back(make_pair(distance, j));
      }
    }

    // Sort based on the distance (shortest distance first)
    sort(distances.begin(), distances.end());

    // Get the T nearest neighbors and save the indices
    for (int t = 0; t < number_of_neighbors; t++) {
      neighborhood[i].push_back(distances[t].second); 
    }
  }  

  return neighborhood;
}