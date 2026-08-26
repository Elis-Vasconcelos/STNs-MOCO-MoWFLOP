#ifndef RANDOM_WALK_PARETO_H
#define RANDOM_WALK_PARETO_H

#include "../landscapeElement.h"
#include <utility>

void calculate_dominance_metrics(LandscapeElement* element, std::vector<Solution>* neighborhood);
std::vector<LandscapeElement> random_walk(int walk_lenght, int number_of_neighbors);

#endif 