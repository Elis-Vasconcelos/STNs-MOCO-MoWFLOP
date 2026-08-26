#ifndef GLOBALS_H
#define GLOBALS_H

#include <vector>
#include <string>
#include <utility>
#include "./metafeatures/landscapeElement.h"

extern int iLandscape;
extern int* countReval;
extern std::vector<std::vector<LandscapeElement>> *updated_mult_walk;
extern std::vector<std::string> column_names_decomposition;
extern std::string folder_name_adaptative_walk;
extern std::string folder_name_random_walk;
extern int walk_length;
extern float percent_neighbors;
extern std::string instance;
extern float angle;
extern float wind;
extern int num_zones;
extern std::vector<Turbine> fixd;
extern std::vector<int> turbines_per_zone;
extern std::vector<pair<double, double>> lambda_vector;
extern std::pair<double, double> global_z_point;
extern double maximal;
extern double minimal;
extern bool limitReached;
extern int limit;

#endif
