#ifndef CALCULATE_WS_H
#define CALCULATE_WS_H

#include <utility>

double calculate_ws(const std::pair<double, double>& fitness,
                    const std::pair<double, double>& lambda);

#endif