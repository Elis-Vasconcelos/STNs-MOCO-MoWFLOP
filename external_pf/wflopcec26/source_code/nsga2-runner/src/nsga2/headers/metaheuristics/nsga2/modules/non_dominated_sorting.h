#ifndef NON_DOMINATED_SORTING_H
#define NON_DOMINATED_SORTING_H

#include "../../../global_modules/generate_initial_population/generate_rSolution.h"
#include <vector>
using namespace std;

vector<vector<Solution*>*> non_dominated_sorting(vector<Solution*>& population_rt);

#endif 