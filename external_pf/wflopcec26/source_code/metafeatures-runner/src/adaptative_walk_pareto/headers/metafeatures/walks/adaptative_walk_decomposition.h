#ifndef ADAPTATIVE_DECOMPOSITION_WALK_H
#define ADAPTATIVE_DECOMPOSITION_WALK_H

#include "walks_common.h"
#include "../landscapeElement.h"
#include <utility>

std::pair<double, int> calculate_decomp_metrics(LandscapeElement *element, std::vector<Solution>* neighborhood);
std::vector<LandscapeElement> adaptative_walk_decomposition(int number_of_neighbors);

#endif 