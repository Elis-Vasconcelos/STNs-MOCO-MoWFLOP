#include "../headers/utils/isEqual.h"

bool isEqual(Solution solutionA, Solution solutionB) {
  return (solutionA.fitness.first == solutionB.fitness.first) && (solutionA.fitness.second == solutionB.fitness.second);
}