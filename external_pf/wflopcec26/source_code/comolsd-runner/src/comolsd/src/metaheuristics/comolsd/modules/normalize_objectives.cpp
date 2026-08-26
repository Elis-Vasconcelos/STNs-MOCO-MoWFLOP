#include <utility>
using namespace std;
#include "../../../../headers/metaheuristics/comolsd/modules/normalize_objectives.h"

pair<double, double> normalize_objectives(
    const pair<double, double>& fitness,
    const pair<double, double>& global_ideal_point,
    const pair<double, double>& global_nadir_point) {

    pair<double, double> normalized;

    // Normalization of the first objective
    if (global_ideal_point.first != global_nadir_point.first) {
        normalized.first = 
            (fitness.first - global_nadir_point.first) / 
            (global_ideal_point.first - global_nadir_point.first);
    } else {
        normalized.first = 0.0; // avoid division by zero
    }

    // Normalization of the second objective
    if (global_ideal_point.second != global_nadir_point.second) {
        normalized.second = 
            (fitness.second - global_nadir_point.second) / 
            (global_ideal_point.second - global_nadir_point.second);
    } else {
        normalized.second = 0.0;
    }

    return normalized;
}
