#include <iostream>
#include <ctime> 
#include <cstdlib>
#include <utility> 
#include <random>
#include "../../modules/headers/population.h"
#include "../../modules/headers/generate_rSolution.h"
#include "../../modules/headers/mutation.h"
#include "../../modules/headers/crossover.h"
#include "../../modules/headers/binary_tournament.h"
#include "../../modules/headers/crowding_distance.h"
#include "../../modules/headers/non_dominated_sorting.h"

#include "../../modules/headers/dominates.h"
#include "../../headers/utils/isEqual.h"
#include "../../modules/headers/nsga2.h"

using namespace std;

void updatePopulation(vector<Solution>& population) {
  // Loop through each solution in the population
  for (int i = 0; i < population.size(); i++) {
    bool isDominated = false;

    // Check if the solution is dominated by any other solution in the population
    for (int j = 0; j < population.size(); j++) {
      if (i != j && dominates(population[j], population[i])) {
        isDominated = true;
        // If the solution is dominated, remove it and adjust the index
        population.erase(population.begin() + i);
        i--;
        break;
      }
    }

    // If the solution has not been dominated, check if there are copies of it
    if (!isDominated) {
      vector<int> copies;
      for (int j = 0; j < population.size(); j++) {
        if (i != j && isEqual(population[j], population[i])) {
          copies.push_back(j);
        }
      }

      // Removes back-to-front copies to avoid indexing issues
      if (!copies.empty()) {
        for (int k = copies.size() - 1; k >= 0; k--) {
          population.erase(population.begin() + copies[k]);
        }
      }
    }
  }
}

vector<Solution> nsga2(vector<Solution>& population){

  //Initializing the random number generator 
  default_random_engine re{(unsigned)time(nullptr)};
  uniform_real_distribution<double> dist(0.0, 1.0);

  //NGSAII paramets 
  int size_population = population.size(); //Size of the population
  double cross_prob = 0.8;
  double mutation_prob = 0.4;
  int max_generations = 3;

  cout << endl;
  cout << "------------INITIAL POPULATION ------------ " << endl;
  for(auto& i : population){
    cout << "<" << i.fitness.first << ", " << i.fitness.second << ">" << endl;
  }
  cout << "------------------------------------------- " << endl << endl;

  cout << "SIZE OF INITIAL POPULATION: " << population.size() << endl << endl;

  int generation = 0;

  while(generation < max_generations){

    cout << "======================= GENERATION: " << generation << "=======================" << endl << endl;

    vector<Solution> offspring_population;

    for(int i = 0; i < size_population; i++){
      //Parent selection
      pair<Solution, Solution> parents = binary_tournament(population);
  
      //Crossover
      Solution child1, child2;
      double k = dist(re);

      if(k < cross_prob){
        child1 = crossover(parents.first, parents.second);
        child2 = crossover(parents.second, parents.first);
      }
      else{
        child1 = parents.first;
        child2 = parents.second;
      }

      offspring_population.push_back(child1);
      offspring_population.push_back(child2);

      //Mutation
      k = dist(re);

      if(k < mutation_prob){
        mutation(child1);
        mutation(child2);
      }

      offspring_population.push_back(child1);
      offspring_population.push_back(child2);
    }

    //Mergin 'population' (size: N) + 'offspring_population' (size: 4N) = 'total_population' (size: 5N)
    //Adding the offspring_population at the end of the 'population' in 'total_population'
    vector<Solution> total_population = population;
    total_population.insert(total_population.end(), offspring_population.begin(), offspring_population.end()); 
    cout << "SIZE OF TOTAL POPULATION: " << total_population.size() << endl << endl;

    //Non dominated sorting
    vector<vector<Solution>> fronts = non_dominated_sorting(total_population);

    cout << "========================== FRONTS ==========================" << endl << endl;
    for(int i = 0; i < fronts.size(); i++){
      cout << "----------------------- FRONT: "<< i << " -----------------------" << endl;
      for(int j = 0; j < fronts[i].size(); j++){
        cout << "<" << fronts[i][j].fitness.first << ", " << fronts[i][j].fitness.second << ">"<< endl;
      }
    } cout << endl;

    population.clear(); //Cleaning the population to generates the next generation
    
    int k = 0;
    for (auto& front : fronts) {
      if (population.size() + front.size() <= size_population) {
        // Add the entire front if it fits in the population
        cout << "ADDING THE WHOLE FRONT " << k << endl;
        for (auto& solution : front) {
          population.push_back(solution);
        }
      } 
      else {
        // If the front doesn't fit all the way, sort by crowding distance and add the missing solutions
        auto front_sorted = crowding_distance(front);
        cout << "ADDING PART OF FRONT " << k << " (crowding distance)" << endl;
        
        // Calculate how many solutions are missing to complete the population
        int remaining_spots = size_population - population.size();
        
        // Add missing solutions
        for (int i = 0; i < remaining_spots; i++) {
          population.push_back(front_sorted[i]);
        }
        
        // The population is complete, we can exit the loop
        break;
      }
      k++;
    }

    generation++;
  }


  updatePopulation(population);
  
  cout << endl;
  cout << "------------FINAL POPULATION ------------ " << endl;
  for(auto& i : population){
    cout << "<" << i.fitness.first << ", " << i.fitness.second << ">" << endl;
  }
  cout << "------------------------------------------- " << endl << endl;

  cout << "SIZE OF FINAL POPULATION: " << population.size() << endl << endl;
  
  return population;
}