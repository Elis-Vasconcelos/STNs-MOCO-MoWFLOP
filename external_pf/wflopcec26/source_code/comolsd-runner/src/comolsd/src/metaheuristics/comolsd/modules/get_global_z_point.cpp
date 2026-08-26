#include <vector>
#include <limits>
#include <iostream>
#include <utility>
#include "../../../../headers/metaheuristics/comolsd/modules/get_global_z_point.h"

using namespace std;

pair<double,double> get_global_z_point(double best_cost){
    pair<double, double> best;

    int num_mobile = 0;
    for(int i = 0; i < turbines_per_zone.size(); i++){
        num_mobile += turbines_per_zone[i];
    }

    float power_mobile = power_alt(wind, power, thrust_coef);
    float power_fixed = power_alt(wind, power_fixed, tcFxd);

    double total = power_mobile * num_mobile + power_fixed * fixd.size();

    return make_pair(best_cost * num_mobile, total);
}