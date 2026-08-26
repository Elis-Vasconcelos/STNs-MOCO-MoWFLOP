#include "../../../../headers/metaheuristics/comolsd/modules/local_search.h"
#include "../../../../headers/metaheuristics/comolsd/modules/build_neighborhood_decision_space.h"
#include "../../../../headers/global_modules/genetic_operators/mutation.h"

using namespace std;

void local_search(vector<Solution>& population,
                  const vector<pair<double, double>>& weight_vectors,
                  const pair<double, double>& reference_point,
                  int number_of_neighbors,
                  function<double(const pair<double, double>&,
                                  const pair<double, double>&,
                                  const pair<double, double>&)> aggregation_function) {

    int size_population = population.size();
    vector<bool> isSearched(size_population, false);

    bool all_searched = false;

    while (!all_searched) {
        all_searched = true;

        for (int i = 0; i < size_population; ++i) {
            if (isSearched[i]) continue;

            isSearched[i] = true;
            all_searched = false;

            // Generate the neighbors of x^i in the decision space
            vector<Solution> neighbors = build_neighborhood_decision_space(population[i], number_of_neighbors);

            // For each neighbor y ∈ N(x^i)
            for (const Solution& y : neighbors) { //N(x) neighborhood exploration

                // For each subproblem j (λ^j)
                for (int j = 0; j < size_population; ++j) {

                    double g_y = aggregation_function(y.fitness, weight_vectors[j], reference_point);
                    double g_xj = aggregation_function(population[j].fitness, weight_vectors[j], reference_point);

                    // If y improves subproblem j, then update
                    if (g_y >= g_xj) {
                        population[j] = y;          // Replaces it 
                        isSearched[j] = false;      // Mark as "unsearched" as it has been updated
                    }
                }
            }
        }
    }
}
