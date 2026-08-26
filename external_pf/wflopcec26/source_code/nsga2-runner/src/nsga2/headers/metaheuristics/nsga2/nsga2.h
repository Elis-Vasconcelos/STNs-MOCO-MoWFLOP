#ifndef NSGA2_H
#define NSGA2_H

#include "../../global_modules/generate_initial_population/generate_rSolution.h"
#include <vector>
using namespace std;

void updatePopulation(vector<Solution*>& population);

vector<Solution*> nsga2(vector<Solution>& pop);

extern ofstream infoRunNSGA2;

#endif 