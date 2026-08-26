#include "../../../../headers/metaheuristics/comolsd/modules/calculate_ws.h"
using namespace std;

double calculate_ws(const pair<double, double>& fitness,
                    const pair<double, double>& lambda) {
    return lambda.first * fitness.first + lambda.second * fitness.second;
}