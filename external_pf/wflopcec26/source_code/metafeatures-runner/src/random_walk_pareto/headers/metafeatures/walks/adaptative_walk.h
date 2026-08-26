#ifndef ADAPTATIVE_WALK_H
#define ADAPTATIVE_WALK_H

#include "walks_common.h"
#include <vector>
#include <utility>
#include <functional>

std::vector<LandscapeElement> adaptive_walk_decomp(int number_of_neighbors);
std::vector<LandscapeElement> adaptive_walk(int number_of_neighbors, Solution (*next_solution) (const LandscapeElement &));

Solution pareto_next_solution(const LandscapeElement &element);

#endif 