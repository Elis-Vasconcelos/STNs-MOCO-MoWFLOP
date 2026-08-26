#ifndef ADAPTATIVE_PARETO_WALK_H
#define ADAPTATIVE_PARETO_WALK_H

#include "../landscapeElement.h"
#include <utility>

void calculate_dominance_metrics(LandscapeElement* element, std::vector<Solution>* neighborhood);
std::vector<LandscapeElement> adaptative_walk_pareto(int number_of_neighbors, Solution (*next_solution) (const LandscapeElement &, const std::vector<Solution>*));

Solution pareto_next_solution(const LandscapeElement &element, const std::vector<Solution>* neighborhood);

#endif 