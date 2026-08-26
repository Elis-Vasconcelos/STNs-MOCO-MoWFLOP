#ifndef RW_DECOMPOSITION_WALK_H
#define RW_DECOMPOSITION_WALK_H

#include "walks_common.h"
#include "../landscapeElement.h"
#include <utility>

std::pair<double, int> calculate_decomp_metrics(LandscapeElement* element, std::vector<Solution>* neighborhood);
std::vector<LandscapeElement> random_walk(int walk_lenght, int number_of_neighbors, std::pair<double, double> &lambda, std::pair<double, double> &global_z_point, double &max, double &min);

#endif 