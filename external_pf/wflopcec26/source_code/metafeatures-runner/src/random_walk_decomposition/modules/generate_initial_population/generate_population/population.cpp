#include "../../headers/population.h"
#include "../../headers/generate_rSolution.h"
#include <iostream>
#include <time.h>
using namespace std;

vector<Solution> create_initial_population(int size_population) {

  vector<Solution> population;

  for (int i = 0; i < size_population; i++) {
    population.push_back(generate_solution());
  }

  return population;
}