#include <vector>
#include <iostream>
#include <algorithm>
#include <limits>
#include "../../../headers/main.h"
using namespace std;

bool cmp_second(const pair<int, double>& a, const pair<int, double>& b){
    return a.second < b.second;
}

bool cmp_cd(const pair<int, double>&a, const pair<int, double>&b){
    return a.second >= b.second;
}

vector<Solution*> crowding_distance(vector<Solution*> &population){
    int num = population.size();
    pair<int, double> dfault = make_pair(0, 1);
    float infinity = numeric_limits<float>::max();
    
    vector<pair<int, double>> base(num, dfault);
    for(int i = 0; i < num; i++){
        base[i].first = i;
    }

    vector<pair<int, double>> byF1, byF2, final;
    byF1 = byF2 = final = base;
    vector<Solution*> aux = population;

    for(int i=0; i<num; i++){
        byF1[i].second = population[i]->fitness.first;
        byF2[i].second = population[i]->fitness.second * -1;
    }

    stable_sort(byF1.begin(), byF1.end(), cmp_second);
    stable_sort(byF2.begin(), byF2.end(), cmp_second);

    vector<pair<int, double>> distancesF1, distancesF2;
    distancesF1 = byF1;
    distancesF2 = byF2;

    distancesF1[0].second = infinity;
    distancesF2[0].second = infinity;
    distancesF1[num-1].second = infinity;
    distancesF2[num-1].second = infinity;

    for(int i = 1; i < num-1; i++){
        distancesF1[i].second = population[byF1[i+1].first]->fitness.first - population[byF1[i-1].first]->fitness.first;
        distancesF2[i].second = (population[byF2[i+1].first]->fitness.second - population[byF2[i-1].first]->fitness.second) * -1;
    }

    for(int i = 0; i < num; i++) {
        final[distancesF1[i].first].second *= distancesF1[i].second;
        final[distancesF2[i].first].second *= distancesF2[i].second;
    }

    stable_sort(final.begin(), final.end(), cmp_cd);

    for(int i = 0; i < num; i++) {
        population[i] = aux[final[i].first];
    }

    return population;
}