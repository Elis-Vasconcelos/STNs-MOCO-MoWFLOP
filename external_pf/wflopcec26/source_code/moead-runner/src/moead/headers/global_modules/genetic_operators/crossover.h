#ifndef CROSSOVER_H
#define CROSSOVER_H

#include "../generate_initial_population/population.h"
#include "../../adaptative_grid/BoundedParetoSet.h"

Solution crossover(Solution &parent_solutionA, Solution &parent_solutionB);

#endif 
