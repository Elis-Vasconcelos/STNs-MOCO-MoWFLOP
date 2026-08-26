#ifndef MO_FEATURES_EXTRACTION_H
#define MO_FEATURES_EXTRACTION_H

#include <vector>
#include "landscapeElement.h"
using namespace std;

void features_extraction(int qtd_of_landscapes, int walk_lenght, int number_of_neighbors);

vector<double> decomposition_extraction(vector<vector<LandscapeElement>> &landscapes);

vector<double> dominance_extraction(vector<LandscapeElement> &landscape);

#endif 
