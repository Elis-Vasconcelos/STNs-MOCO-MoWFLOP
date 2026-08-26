#ifndef MOEAD_H
#define MOEAD_H

#include <vector>
#include <utility>
#include "../../global_modules/generate_initial_population/generate_rSolution.h"

void moead(std::vector<Solution>& population);

extern ofstream infoRun;

#endif 