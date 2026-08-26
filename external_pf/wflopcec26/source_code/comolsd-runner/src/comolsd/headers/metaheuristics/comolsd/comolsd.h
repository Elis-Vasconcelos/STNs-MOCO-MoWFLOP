#ifndef COMOLSD_H
#define COMOLSD_H

#include <vector>
#include <utility>
#include "../../global_modules/generate_initial_population/generate_rSolution.h"
#include <fstream>

void comolsd(std::vector<Solution>& population);

extern ofstream infoRun;

#endif 