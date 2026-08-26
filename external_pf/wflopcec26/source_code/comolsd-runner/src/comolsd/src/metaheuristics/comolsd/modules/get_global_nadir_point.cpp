#include <vector>
#include <limits>
#include <iostream>
#include <utility>
#include "../../../../headers/metaheuristics/comolsd/modules/get_global_z_point.h"

using namespace std;

pair<double,double> get_global_nadir_point(double worst_cost){
    pair<double, double> best;

    int num_mobile = 0;
    for(int i = 0; i < turbines_per_zone.size(); i++){
        num_mobile += turbines_per_zone[i];
    }

    return make_pair(worst_cost * num_mobile, 0);
}