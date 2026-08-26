#ifndef GET_NADIR_POINT_H
#define GET_NADIR_POINT_H

#include <vector>
#include <utility>
#include "../../../global_modules/generate_initial_population/generate_rSolution.h"

// Returns the nadir point (z^nad) for the max-max problem with -cost and power
std::pair<double, double> get_nadir_point(const std::vector<Solution>& population);

#endif
