#ifndef NORMALIZE_OBJECTIVES_H
#define NORMALIZE_OBJECTIVES_H

#include <utility>

std::pair<double, double> normalize_objectives(
    const std::pair<double, double>& fitness,
    const std::pair<double, double>& global_ideal_point,
    const std::pair<double, double>& global_nadir_point);

#endif
