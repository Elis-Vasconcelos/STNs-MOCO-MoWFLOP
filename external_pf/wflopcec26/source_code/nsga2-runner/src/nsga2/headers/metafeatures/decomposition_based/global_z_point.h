#ifndef GLOBAL_Z_POINT_H
#define GLOBAL_Z_POINT_H

#include <vector>
#include <utility>
#include "../../../headers/wind_farm_entities/turbine.h"

extern std::vector<int> turbines_per_zone;
extern float wind;
extern float power, powerFxd;
extern float thrust_coef;
extern float tcFxd;
extern std::vector<Turbine> fixd;

std::pair<double, double> get_global_z_point();

#endif 