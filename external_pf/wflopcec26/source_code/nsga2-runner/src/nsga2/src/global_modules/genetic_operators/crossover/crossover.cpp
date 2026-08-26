#include "../../../../headers/global_modules/generate_initial_population/population.h"
#include "../../../../headers/global_modules/genetic_operators/crossover.h"
#include <cstdlib>
#include <vector>
#include <iostream>

/*The goal of the crossover is: randomly select a position in zone i (rand_int) and copy all the turbines
from 0 to rand_int from parent_solutionA to the offspring solution (offspring_solution).

Then, for each position in parent_solutionB that is not zero (i.e. has a turbine) and that turbine
has not already been added to the offspring, we add that turbine to the offspring.

PS: THIS IS DONE FOR ALL ZONES i SUCH AS i < num_zones.*/

extern vector<int> turbines_per_zone;
extern string algorithm;
extern string instance;

//Function to find the index of a turbine (searching for its id) within of a vector of turbines in zone i.
int find_turbine(vector<Turbine> &vec, int value){
  for(int i = 0; i < vec.size(); i++){
    if(vec[i].id == value){
      return i;
    }
  }
  return -1;
}

// Function to check if a turbine_id is in the grid vector of the offspring solution
bool InOffspring(int turbine_index, const vector<int> &grid) {
  return grid[turbine_index] != 0;
}

void crossoverAux(Solution &parent_solutionA, Solution &parent_solutionB, Solution &offspring_solution, int zone){
  offspring_solution.grid[zone].resize(parent_solutionA.grid[zone].size(), 0);

  int rand_int = rand() % parent_solutionA.grid[zone].size();
  int index = -1;
  int lastIndex = 0;
  int id_new = fixd.size();
  Turbine turbina;

  // First part of crossover with parent_solutionA
  for(int i = 0; i <= rand_int; i++){
    if(parent_solutionA.grid[zone][i] != 0){
      offspring_solution.grid[zone][i] = id_new;
      index = find_turbine(parent_solutionA.turbines[zone], parent_solutionA.grid[zone][i]);
      turbina = parent_solutionA.turbines[zone][index];
      turbina.id = id_new;
      offspring_solution.turbines[zone].push_back(turbina);
      id_new++;
    }

  }

  // Second part of crossover with parent_solutionB
  
  for(int i = parent_solutionB.grid[zone].size() - 1; i >= 0; i--){
    if(parent_solutionB.grid[zone][i] != 0){

      if(offspring_solution.turbines[zone].size() >= turbines_per_zone[zone]){
        return;
      }

      if(parent_solutionB.grid[zone][i] != 0){

        if(InOffspring(i, offspring_solution.grid[zone])){
          continue;
        }

        offspring_solution.grid[zone][i] = id_new;
        index = find_turbine(parent_solutionB.turbines[zone], parent_solutionB.grid[zone][i]);
        turbina = parent_solutionB.turbines[zone][index];
        turbina.id = id_new;
        offspring_solution.turbines[zone].push_back(turbina);
        id_new++;
      }

    }
  }
}

Solution crossover(Solution &parent_solutionA, Solution &parent_solutionB){

  Solution offspring_solution;
  offspring_solution.grid.resize(num_zones);
  offspring_solution.turbines.resize(num_zones);

  for(int j = 0; j < num_zones; j++){
    crossoverAux(parent_solutionA, parent_solutionB, offspring_solution, j);
  }

  calculate_cost(offspring_solution);
  calculate_power(offspring_solution);

  Solution * sol = new Solution(offspring_solution);
  pareto->addSol(sol);

  delete sol;

  countRevalue++;

  if(countRevalue % 100000 == 0){
    string path = instance + "_" + algorithm + "_" + to_string(countRevalue) + ".txt";
    pareto->printAllSolutions(root_folder + path);

    if(countRevalue >= stop_criteria){
      pareto->printAllSolutionsLayout(root_folder + instance + "_" + algorithm + "_layout.txt");
    }
  }

  return offspring_solution;
}