#include <vector>
#include <iostream>
#include "../../headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "../../headers/utils/isEqual.h"
#include "../../headers/metaheuristics/genetic_operators/mutation/mutationFeature.h"
#include "../../headers/metafeatures/features_extraction.h"

#include "../../headers/globals.h"

bool isEqualNeighborhood(Solution* new_neighbor, vector<Solution>* neighborhood ){
  for(auto solution : *neighborhood){
    if(isEqual(*new_neighbor, solution)){
      return true;
    }
  }
  return false;
}

Solution* get_neighbor(Solution &currentSolution) {
  Solution* new_neighbor = new Solution(currentSolution);

  mutationFeature(*new_neighbor);
  *countReval = *countReval + 1;

  return new_neighbor;
}

