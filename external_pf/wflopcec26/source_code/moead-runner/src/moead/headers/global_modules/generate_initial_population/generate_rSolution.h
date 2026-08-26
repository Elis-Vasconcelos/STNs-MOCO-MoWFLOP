#ifndef GENERATE_RSOLUTION_H
#define GENERATE_RSOLUTION_H

#include <vector>
#include <utility>
#include "../../wind_farm_entities/turbine.h"
#include "../../wind_farm_entities/solution.h"
#include "../../wind_farm_entities/foundations.h"

float power_alt(float& wind, float& power, float& tc);

extern std::vector<std::vector<Foundation>> foundations;
extern std::vector<Turbine> fixd;
extern std::vector<int> turbines_per_zone;

extern float wind;
extern float power;
extern float thrust_coef;
extern float angle;
extern int num_zones;
extern int id;

Solution generate_solution();

double calculate_cost(Solution& sol);

double calculate_interference(Turbine& t_initial, Turbine& t_interfered);

double calculate_power(Solution& sol);

#endif
