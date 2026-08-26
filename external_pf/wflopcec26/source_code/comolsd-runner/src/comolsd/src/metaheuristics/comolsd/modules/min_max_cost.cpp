#include <vector>
#include <limits>
#include <iostream>
#include <utility>
#include "../../../../headers/metaheuristics/comolsd/modules/min_max_cost.h"

using namespace std;

pair<double, double> min_max_cost(){
    double worst_cost = foundations[0][0].cost;
    double best_cost = foundations[0][0].cost;

    for(int i = 0; i < num_zones; i++){
        for(int j = 0; j < foundations[i].size(); j++){
            if(foundations[i][j].cost < worst_cost){
                worst_cost = foundations[i][j].cost;
            } else if(foundations[i][j].cost > best_cost){
                best_cost = foundations[i][j].cost;
            }
        }
    }

    return make_pair(worst_cost, best_cost);
}