#ifndef LANDSCAPE_ELEMENT_H
#define LANDSCAPE_ELEMENT_H

#include <vector>
#include "../../modules/headers/generate_rSolution.h"

struct LandscapeElement {
  Solution current_solution;
  double tch_current_solution;
  double inf; // Proportion of inferior solutions, that current solution dominates
  double sup; // Proportion of superior solutions, that dominates current solution
  double inc; // Proportion of solutions that are incomparable with current solution
  double ind; // Proportion of solutions non dominated between them (Proportion of Pareto front)
  vector<Solution> neighborhod;
  vector<double> tchebycheff_neighbors;
};

#endif 
