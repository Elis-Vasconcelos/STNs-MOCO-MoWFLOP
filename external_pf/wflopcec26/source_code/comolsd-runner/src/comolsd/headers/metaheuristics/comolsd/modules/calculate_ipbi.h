#ifndef CALCULATE_IPBI_H
#define CALCULATE_IPBI_H

#include <utility>
#include <cmath>

double calculate_ipbi(const std::pair<double, double>& fitness,
                      const std::pair<double, double>& lambda,
                      const std::pair<double, double>& nadir_point);

#endif