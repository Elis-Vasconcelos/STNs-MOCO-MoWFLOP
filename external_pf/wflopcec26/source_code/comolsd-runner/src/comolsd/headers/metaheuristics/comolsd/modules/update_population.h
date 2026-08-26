#ifndef UPDATE_POPULATION_H
#define UPDATE_POPULATION_H

#include <vector>
#include <functional>
#include <utility>
#include "../../../global_modules/generate_initial_population/generate_rSolution.h"

std::vector<Solution> update_population(
    const std::vector<std::pair<double, double>>& direction_vector,
    const std::vector<Solution>& TP,
    const std::pair<double, double>& reference_point,
    std::function<double(const std::pair<double, double>&,
                         const std::pair<double, double>&,
                         const std::pair<double, double>&)> aggregation_function);

#endif
