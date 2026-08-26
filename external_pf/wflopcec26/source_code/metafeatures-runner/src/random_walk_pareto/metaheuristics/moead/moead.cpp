#include <utility>
#include <vector>
#include <iostream>
#include <ctime> 
#include <algorithm>
#include <random>
#include "../../modules/headers/population.h"
#include "../../modules/headers/generate_rSolution.h"
#include "../../modules/headers/generate_weight_vectors.h"
#include "../../modules/headers/generate_neighborhood.h"
#include "../../modules/headers/get_best_z_point.h"
#include "../../modules/headers/tchebycheff.h"
// #include "../../modules/headers/mutation.h"
#include "../../modules/headers/mutation2.h"
#include "../../modules/headers/crossover.h"


#include "../../modules/headers/dominates.h"
#include "../../headers/utils/isEqual.h"

#include "../../modules/headers/updateEP.h"

using namespace std;

vector<Solution> moead(vector<Solution>& population){

  //Initializing the random number generator 
  random_device rd;
  mt19937 gen(rd());

  //MOAED parameters 
  int size_population = population.size();
  double input_cross_prob = 0.9;
  double input_mutation_prob = 0.1;
  int number_of_neighbors = 150;
  int max_generations = 500;

  // Step 1.1: Initialize EP (External Population)
  //The EP vector will contain only the non-dominated and not equal solutions from the initial population
  vector<Solution> EP;
  for(auto& sol : population){
    updateEP(EP, sol);
  }

  //Building the lambda vector, ie, the vector of weights to each subproblem i
  vector<pair<double, double>> lambda_vector = build_weight_vector(size_population); 

  //Step 1.2: Building the neighborhood (B) of each lambda vector i (or each subproblem i)
  vector<vector<int>> neighborhood = build_neighborhood(number_of_neighbors, lambda_vector, size_population);
  
  //Step 1.4: z_point
  pair<double, double> z_point = get_best_z_point(population);

  /*Step 1.3: tch_vector = vector with the value of tchebycheff function to each subproblem (weight vector) i 
  Each index i of tch_vector (to reference the lambda vector i, neighborhood i of a subproblem i) contains the TCH of the subproblem i*/
  vector<double> tch_vector(size_population);

  for(int i = 0; i < tch_vector.size(); i++){
    tch_vector[i] = calculate_gte(population[i].fitness, lambda_vector[i], z_point);
  }
  
  //Step 2: Update

  int generation = 0;

  while (generation < max_generations) {

    Solution child1, child2;

    for (int i = 0; i < size_population; i++) {

      // Step 2.1: Reproduction
      // Randomly select two indices k and l from the neighborhood B(i)
      uniform_int_distribution<> dis(0, number_of_neighbors - 1);
      int k = neighborhood[i][dis(gen)];
      int l = neighborhood[i][dis(gen)];

      while (k == l) {
        l = neighborhood[i][dis(gen)];
      }

      Solution parentA = population[k];
      Solution parentB = population[l];
      child1 = parentA;
      child2 = parentB;

      // Generate new solution y using genetic operators

      //Crossover

      if((static_cast<double>(rand()) / RAND_MAX) < input_cross_prob){ 
        child1 = crossover(parentA, parentB);
        child2 = crossover(parentB, parentA);
      }
      else{
        mutation2(child1, input_mutation_prob, EP);
        mutation2(child2, input_mutation_prob, EP);
      }

      updateEP(EP, child1);
      updateEP(EP, child2);
      
      // Step 2.3: Update of z point
      for(const auto& sol : EP){
        z_point.first = max(z_point.first, sol.fitness.first);
        z_point.second = max(z_point.second, sol.fitness.second);
      }

      // Step 2.4: Neighboring solutions update
      for (int j : neighborhood[i]) {
        double child1_tch = calculate_gte(child1.fitness, lambda_vector[j], z_point);
        double sol1_pop = calculate_gte(population[j].fitness, lambda_vector[j], z_point);
        if (child1_tch <= sol1_pop) {
          population[j] = child1;
        }
        
        double child2_tch = calculate_gte(child2.fitness, lambda_vector[j], z_point);
        double sol2_pop = calculate_gte(population[j].fitness, lambda_vector[j], z_point);
        if (child2_tch <= sol2_pop) {
          population[j] = child2;
        }
      }
    }
    generation++;
  }

  for(auto& i : EP){
    cout << i.fitness.first * (-1) << " " << i.fitness.second << endl;
  }
  
  cout << endl;

  return EP;
}