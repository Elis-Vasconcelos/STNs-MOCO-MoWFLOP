#ifndef LANDSCAPE_METRICS_H
#define LANDSCAPE_METRICS_H

#include <vector>

struct LandscapeMetrics {
  std::vector<double> fitness_values; // Stores the fitness values ​​obtained during the walk
  std::vector<double> fitness_differences; // Stores the fitness differences between solutions and their neighbors
  std::vector<double> improving_neighbors_count; // Stores the number of neighbors that improve the solution
  std::vector<double> inf_neighbors; // Stores the proportions of neighbors that are inferior to the solution
  std::vector<double> sup_neighbors; // Stores the proportions of neighbors that are superior to the solution
  std::vector<double> inc_neighbors; // Stores the proportions of neighbors that are incomparable with the solution
  std::vector<double> ind_neighbors; // Stores the proportions of neighbors that are incomparable with each other
};

#endif 