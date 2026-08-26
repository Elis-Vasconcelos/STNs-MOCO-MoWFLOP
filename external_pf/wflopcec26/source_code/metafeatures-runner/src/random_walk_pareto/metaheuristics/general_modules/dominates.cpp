#include "../../modules/headers/generate_rSolution.h"
#include "../../modules/headers/dominates.h"

bool dominates(Solution solutionA, Solution solutionB){
  return (solutionA.fitness.first >= solutionB.fitness.first && solutionA.fitness.second >= solutionB.fitness.second) && (solutionA.fitness.first > solutionB.fitness.first || solutionA.fitness.second > solutionB.fitness.second);
}