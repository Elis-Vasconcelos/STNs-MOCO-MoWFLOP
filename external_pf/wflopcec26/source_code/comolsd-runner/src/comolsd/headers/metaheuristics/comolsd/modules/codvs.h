#ifndef CODVS_H
#define CODVS_H

#include <vector>
#include <utility>
#include <algorithm>
#include "../../../global_modules/generate_initial_population/generate_rSolution.h"
#include "../../../metaheuristics/comolsd/modules/unionFind.h"

// Generate the set of direction vectors W2 based on the population P, Q, nadir point and N
std::vector<std::pair<double, double>> codvs(
    const std::pair<double, double>& nadir_point,
    const std::vector<Solution>& population_p,
    const std::vector<Solution>& population_q,
    int N);

#endif
