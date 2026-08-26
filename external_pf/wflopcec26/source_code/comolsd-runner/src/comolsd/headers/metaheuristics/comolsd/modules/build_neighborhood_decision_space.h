#ifndef BUILD_NEIGHBORHOOD_DECISION_SPACE_H
#define BUILD_NEIGHBORHOOD_DECISION_SPACE_H

#include <vector>
#include "solution.h"

std::vector<Solution> build_neighborhood_decision_space(const Solution& parent, int number_of_neighbors);

#endif
