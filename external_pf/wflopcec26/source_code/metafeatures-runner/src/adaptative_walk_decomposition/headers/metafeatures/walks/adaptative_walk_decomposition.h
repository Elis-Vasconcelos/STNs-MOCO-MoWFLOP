#ifndef RW_DECOMPOSITION_WALK_H
#define RW_DECOMPOSITION_WALK_H

#include "../landscapeElement.h"
#include <vector>
#include <utility>

std::pair<double, int> calculate_decomp_metrics(LandscapeElement *element, std::vector<Solution>* neighborhood);
std::vector<LandscapeElement> adaptative_walk_decomposition(int number_of_neighbors);

#endif 