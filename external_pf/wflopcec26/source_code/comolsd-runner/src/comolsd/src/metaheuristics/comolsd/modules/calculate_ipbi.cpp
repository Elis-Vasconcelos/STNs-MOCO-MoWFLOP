#include "../../../../headers/metaheuristics/comolsd/modules/calculate_ipbi.h"
using namespace std;

double calculate_ipbi(const pair<double, double>& fitness,
                      const pair<double, double>& lambda,
                      const pair<double, double>& nadir_point) {
    // 1. Build the vector d = f(x) - z^nadir
    double dx = fitness.first - nadir_point.first;
    double dy = fitness.second - nadir_point.second;

    // 2. Normalizing lambda
    double norm_lambda = sqrt(lambda.first * lambda.first + lambda.second * lambda.second);
    double lx = lambda.first / norm_lambda;
    double ly = lambda.second / norm_lambda;

    // 3. Projected distance d1 (projection of d onto normalized lambda)
    double d1 = dx * lx + dy * ly;

    // 4. Orthogonal projection (d2 = ||d - d1 * lambda||)
    double px = d1 * lx;
    double py = d1 * ly;
    double d2 = sqrt((dx - px) * (dx - px) + (dy - py) * (dy - py));

    // 5. iPBI function
    double theta = 2.0;
    return d1 - theta * d2;
}