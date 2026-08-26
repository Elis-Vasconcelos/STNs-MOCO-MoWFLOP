#ifndef GENERATE_NEIGHBORHOOD_H
#define GENERATE_NEIGHBORHOOD_H

#include <vector>
#include <utility>

std::vector<std::vector<int>> build_neighborhood(int number_of_neighbors, std::vector<std::pair<double, double>>& lambda_vector, int size_population);

#endif 