#ifndef BEST_Z_POINT_H
#define BEST_Z_POINT_H

#include <vector>
#include <utility>
#include "../../../global_modules/generate_initial_population/generate_rSolution.h"
using namespace std;

pair<double, double> get_best_z_point(vector<Solution>& population);

#endif 