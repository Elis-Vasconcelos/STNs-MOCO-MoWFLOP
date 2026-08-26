#ifndef SOLUTION_H
#define SOLUTION_H

#include <vector>
#include <utility>
#include "./turbine.h"

struct Solution {
    std::vector<std::vector<int>> grid; //Represents the terrain of the wind farm in a 1D vector. '0' means there is no turbine in that position. Otherwise, there is. 
    std::vector<std::vector<Turbine>> turbines; // The Structure that is going to store the turbines off solution
    std::pair<double, double> fitness;  // The representation of the fitness evaluation, the first one is the cost while the second one is the netpower
};

#endif 