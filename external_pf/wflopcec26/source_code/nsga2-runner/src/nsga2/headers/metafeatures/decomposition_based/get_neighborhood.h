#ifndef GET_NEIBORHOOD_METAFEATURES_H
#define GET_NEIBORHOOD_METAFEATURES_H

#include <vector>
#include "../../../modules/headers/generate_rSolution.h"

Solution get_neighbor(Solution &currentSolution);

bool isEqualNeighborhood(Solution &new_neighbor, vector<Solution> &neighborhood);


#endif 