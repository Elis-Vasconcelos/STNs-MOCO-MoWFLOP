#ifndef AGGREGATION_WRAPPER_H
#define AGGREGATION_WRAPPER_H

#include <functional>
#include <utility>
#include "calculate_ws.h"
#include "calculate_ipbi.h"
#include "normalize_objectives.h"

// For functions that receive 2 arguments (e.g. calculate_ws)
std::function<double(const std::pair<double, double>&,
                     const std::pair<double, double>&,
                     const std::pair<double, double>&)>
make_aggregation_function(
    double (*aggregation)(const std::pair<double, double>&,
                          const std::pair<double, double>&),
    const std::pair<double, double>& global_ideal_point,
    const std::pair<double, double>& global_nadir_point);

// For functions that receive 3 arguments (e.g. calculate_ipbi)
std::function<double(const std::pair<double, double>&,
                     const std::pair<double, double>&,
                     const std::pair<double, double>&)>
make_aggregation_function(
    double (*aggregation)(const std::pair<double, double>&,
                          const std::pair<double, double>&,
                          const std::pair<double, double>&),
    const std::pair<double, double>& global_ideal_point,
    const std::pair<double, double>& global_nadir_point);

#endif
