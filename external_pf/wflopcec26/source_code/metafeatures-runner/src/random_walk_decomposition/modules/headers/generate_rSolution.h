#ifndef GENERATE_RSOLUTION_H
#define GENERATE_RSOLUTION_H

#include <vector>
#include <utility>
#include "turbine.h"
using namespace std;

struct Foundation {
    double x;
    double y;
    double cost;
};

float power_alt(float& wind, float& power, float& tc);

extern vector<vector<Foundation>> foundations;
extern vector<Turbine> fixd;
extern vector<int> turbines_per_zone;

extern float wind;
extern float power;
extern float thrust_coef;
extern float angle;
extern int num_zones;
extern int id;

struct Solution {
    vector<vector<int>> grid; //Represents the terrain of the wind farm in a 1D vector. '0' means there is no turbine in that position. Otherwise, there is. 
    vector<vector<Turbine>> turbines; // The Structure that is going to store the turbines off solution
    pair<double, double> fitness;  // The representation of the fitness evaluation, the first one is the cost while the second one is the netpower
};

Solution generate_solution();

double calculate_cost(Solution& sol);

double calculate_interference(Turbine& t_initial, Turbine& t_interfered);

double calculate_power(Solution& sol);

#endif