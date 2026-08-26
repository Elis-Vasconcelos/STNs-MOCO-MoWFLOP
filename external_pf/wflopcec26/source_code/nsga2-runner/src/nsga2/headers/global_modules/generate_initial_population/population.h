#ifndef POPULATION_H
#define POPULATION_H

#include <vector>
#include <string>
#include "generate_rSolution.h"
#include "../../adaptative_grid/BoundedParetoSet.h"

extern BoundedParetoSet * pareto;
extern int countRevalue;
extern std::string instance;
extern std::string algorithm;
extern std::string root_folder;
extern int stop_criteria;

std::vector<Solution> create_initial_population(int size_population);

#endif
