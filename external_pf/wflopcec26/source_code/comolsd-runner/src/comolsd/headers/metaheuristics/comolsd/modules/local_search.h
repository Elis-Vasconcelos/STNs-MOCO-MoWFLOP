#ifndef LOCAL_SEARCH_H
#define LOCAL_SEARCH_H

#include <vector>
#include <functional>
#include <utility>
#include "../../../wind_farm_entities/solution.h"

// Perform local search based on CoMOLS/D Algorithm 2
void local_search(std::vector<Solution>& population,
                  const std::vector<std::pair<double, double>>& weight_vectors,
                  const std::pair<double, double>& reference_point,
                  int number_of_neighbors,
                  std::function<double(const std::pair<double, double>&,
                                       const std::pair<double, double>&,
                                       const std::pair<double, double>&)> aggregation_function);

#endif
