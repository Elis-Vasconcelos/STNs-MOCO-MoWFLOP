#include <utility>
#include "../headers/generate_rSolution.h"
#include "../headers/binary_tournament.h"

pair<Solution, Solution> binary_tournament(vector<Solution>& population){
  pair<Solution, Solution> parents;

  //Getting a random index for a solution 
  int i1 = rand() % population.size();
  int i2 = rand() % population.size();
  int i3 = rand() % population.size();
  int i4 = rand() % population.size();

  Solution candidate1 = population[i1];
  Solution candidate2 = population[i2];
  Solution candidate3 = population[i3];
  Solution candidate4 = population[i4];

  //Choosing the best solution in the first objective
  if(candidate1.fitness.first >= candidate2.fitness.first) parents.first = candidate1;
  else parents.first = candidate2;

  //Choosing the best solution in the second objective
  if(candidate3.fitness.second >= candidate4.fitness.second) parents.second = candidate3;
  else parents.second = candidate4;

  return parents;
}