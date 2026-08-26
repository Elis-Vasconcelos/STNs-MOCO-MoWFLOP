#include <vector>
#include <iostream>
#include "../../../headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "../../../modules/headers/isEqual.h"
#include "../../../modules/headers/mutationFeature.h"
#include "../../../headers/metafeatures/features_extraction.h"


extern int* countReval;
extern int mode, defaultDecompPace, defaultDomPace;
extern vector<vector<LandscapeElement>> *updated_mult_walk;
extern vector<LandscapeElement> *updated_single_walk;


bool isEqualNeighborhood(Solution &new_neighbor, vector<Solution> &neighborhood ){
  for(auto &solution : neighborhood){
    if(isEqual(new_neighbor, solution)){
      return true;
    }
  }
  return false;
}

Solution get_neighbor(Solution &currentSolution){

  Solution new_neighbor = currentSolution;

  mutationFeature(new_neighbor);
  *countReval = *countReval + 1;

  return new_neighbor;
}
