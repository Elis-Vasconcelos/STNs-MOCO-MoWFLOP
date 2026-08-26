#include "../../../../headers/metaheuristics/comolsd/modules/get_nadir_point.h"
#include <limits>

using namespace std;

pair<double, double> get_nadir_point(const vector<Solution>& population) {
    // Initialize with positive infinity, as we are looking for the worst (smallest) values
    double worst_cost = numeric_limits<double>::infinity();   // lowest -cost = highest cost
    double worst_power = numeric_limits<double>::infinity();  // lowest power

    for (const Solution& sol : population) {
        if (sol.fitness.first < worst_cost) {
            worst_cost = sol.fitness.first;
        }
        if (sol.fitness.second < worst_power) {
            worst_power = sol.fitness.second;
        }
    }

    return make_pair(worst_cost, worst_power); // z^nad
}
