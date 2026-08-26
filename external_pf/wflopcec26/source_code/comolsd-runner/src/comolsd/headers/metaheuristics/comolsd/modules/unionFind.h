#ifndef UNION_FIND_H
#define UNION_FIND_H

#include <vector>
#include <math.h>
#include <unordered_map>
#include "../../../global_modules/generate_initial_population/generate_rSolution.h"
using namespace std;

int findParent(vector<int>& parent, int x);
void unionSets(vector<int>& clusters, int x, int y);
double euclidDistance(const Solution& a,const Solution& b);
int findNearest(const vector<Solution>& population, int actual);
vector<vector<Solution>> unionFind(const vector<Solution>& P);

#endif