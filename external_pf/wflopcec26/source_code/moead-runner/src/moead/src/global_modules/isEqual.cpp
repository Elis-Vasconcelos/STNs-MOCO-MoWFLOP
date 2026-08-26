#include "../../headers/global_modules/generate_initial_population/generate_rSolution.h"
#include "../../headers/global_modules/isEqual.h"

bool isEqual(Solution solutionA, Solution solutionB) {
  return (solutionA.fitness.first == solutionB.fitness.first) && (solutionA.fitness.second == solutionB.fitness.second);
}