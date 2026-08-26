#include "../../../../headers/metaheuristics/comolsd/modules/update_population.h"
#include <random>

using namespace std;

vector<Solution> update_population(
    const vector<pair<double, double>>& direction_vector,
    const vector<Solution>& TP,
    const pair<double, double>& reference_point,
    function<double(const pair<double, double>&,
                    const pair<double, double>&,
                    const pair<double, double>&)> aggregation_function) {

    int num_directions = direction_vector.size();
    vector<Solution> TQ(num_directions);

    // Step 1: Initialize TQ with random solutions from TP
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<> dis(0, TP.size() - 1);

    for (int i = 0; i < num_directions; ++i) {
      TQ[i] = TP[dis(gen)];
    }

    // Step 2: for each x in TP, evaluate with each vector lambda_i and update if it improves
    for (const Solution& x : TP) {
        for (int i = 0; i < num_directions; ++i) {
            double new_value = aggregation_function(x.fitness, direction_vector[i], reference_point);
            double current_value = aggregation_function(TQ[i].fitness, direction_vector[i], reference_point);

            if (new_value >= current_value) {
                TQ[i] = x;
            }
        }
    }

    return TQ;
}
