#include "../../../../headers/metaheuristics/comolsd/modules/aggregation_wrapper.h"
#include "../../../../headers/metaheuristics/comolsd/modules/normalize_objectives.h"

using namespace std;


// Normalization of the second objective
std::function<double(const pair<double, double>&,
                     const pair<double, double>&,
                     const pair<double, double>&)>
make_aggregation_function(
    double (*aggregation)(const pair<double, double>&,
                          const pair<double, double>&),
    const pair<double, double>& global_ideal_point,
    const pair<double, double>& global_nadir_point) {

    return [aggregation, global_ideal_point, global_nadir_point](
        const pair<double, double>& fitness,
        const pair<double, double>& lambda,
        const pair<double, double>& /*unused*/) -> double {

        auto normalized = normalize_objectives(fitness, global_ideal_point, global_nadir_point);
        return aggregation(normalized, lambda);
    };
}

// For functions like calculate_ipbi (3 arguments)
std::function<double(const pair<double, double>&,
                     const pair<double, double>&,
                     const pair<double, double>&)>
make_aggregation_function(
    double (*aggregation)(const pair<double, double>&,
                          const pair<double, double>&,
                          const pair<double, double>&),
    const pair<double, double>& global_ideal_point,
    const pair<double, double>& global_nadir_point) {

    return [aggregation, global_ideal_point, global_nadir_point](
        const pair<double, double>& fitness,
        const pair<double, double>& lambda,
        const pair<double, double>& nadir_point) -> double {

        auto normalized_fitness = normalize_objectives(fitness, global_ideal_point, global_nadir_point);
        auto normalized_nadir   = normalize_objectives(nadir_point, global_ideal_point, global_nadir_point);

        return aggregation(normalized_fitness, lambda, normalized_nadir);
    };
}

