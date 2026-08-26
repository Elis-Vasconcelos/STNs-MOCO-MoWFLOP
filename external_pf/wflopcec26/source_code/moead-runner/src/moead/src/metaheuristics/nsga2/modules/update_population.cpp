#include "../../../../headers/global_modules/generate_initial_population/generate_rSolution.h"
#include "../../../../headers/global_modules/dominates.h"
#include "../../../../headers/global_modules/isEqual.h"
#include "../../../../headers/metaheuristics/nsga2/modules/update_population.h"

#include <vector>

void updatePopulation(vector<Solution*>& population) {
  // Loop through each solution in the population
  for (int i = 0; i < population.size(); i++) {
    bool isDominated = false;

    // Check if the solution is dominated by any other solution in the population
    for (int j = 0; j < population.size(); j++) {
      if (i != j && dominates(*population[j], *population[i])) {
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
        if (i != j && isEqual(*population[j], *population[i])) {
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