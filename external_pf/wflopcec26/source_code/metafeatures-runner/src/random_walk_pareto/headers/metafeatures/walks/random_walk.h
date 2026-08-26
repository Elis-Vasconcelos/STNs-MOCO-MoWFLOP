#ifndef RANDOM_WALK_H
#define RANDOM_WALK_H

#include "walks_common.h"
#include <utility>

std::vector<LandscapeElement> random_walk(int walk_lenght, int number_of_neighbors, std::pair<double, double> &lambda, std::pair<double, double> &global_z_point, double &max, double &min);

#endif 