#include "../../../../headers/metaheuristics/comolsd/modules/unionFind.h"

int findParent(vector<int>& parent, int x) {
    if (parent[x] == x){
        return x;
    }
    return parent[x] = findParent(parent, parent[x]);
}

void unionSets(vector<int>& clusters, int x, int y) {
    int px = findParent(clusters, x);
    int py = findParent(clusters, y);
    if (px != py) {
        clusters[px] = py;
    }
}

double euclidDistance(const Solution& a, const Solution& b){
    return sqrt(pow(b.fitness.first - a.fitness.first, 2) + pow(b.fitness.second - a.fitness.second, 2));
}

int findNearest(const vector<Solution>& population, int actual){
    int nearest = 0;
    if(nearest == actual){
        nearest = 1;
    }
    double nearVal = euclidDistance(population[nearest], population[actual]);

    for (int i = 0; i < population.size(); i++){
        if(i == actual){
            continue;
        }
        double result = euclidDistance(population[actual], population[i]);

        if(nearVal > result){
            nearVal = result;
            nearest = i;
        }
    }

    return nearest;
}

vector<vector<Solution>> unionFind(const vector<Solution>& P){
    vector<int> clusters(P.size());
    vector<vector<Solution>> result;

    for(int i = 0; i < P.size(); i++){
        clusters[i] = i;
    }

    for(int i = 0; i < P.size(); i++){
        unionSets(clusters, i, findNearest(P, i));
    }

    for (int i = 0; i < P.size(); i++) {
        clusters[i] = findParent(clusters, i);
    }

    unordered_map<int, vector<Solution>> resMap;
    for (int i = 0; i < P.size(); i++) {
        resMap[clusters[i]].push_back(P[i]);
    }

    for(auto& e : resMap){
        result.push_back(e.second);
    }

    return result;
}