#ifndef WALKS_COMMON_H
#define WALKS_COMMON_H

#include "../landscapeElement.h"
#include "../landscapeMetrics.h"

extern vector<pair<double, double>> lambda_vector;
extern pair<double, double> global_z_point;
extern double maximal, minimal;
extern int iLandscape;

bool add_front_0(Solution &solution, vector<Solution> &front_0){
  for(int i = 0; i < front_0.size(); i++){
    if(dominates(front_0[i], solution)){
      return false;
    }
  }

  for(int i = 0; i < front_0.size(); i++){
    if(dominates(solution, front_0[i])){
      front_0.erase(front_0.begin() + i);
    }
  }

  front_0.push_back(solution);
  return true;
}

int number_pareto_front(LandscapeElement &landscape){
  vector<Solution> pareto_front;
  Solution solution_0 = landscape.neighborhod[0];

  for(int i = 0; i < landscape.neighborhod.size(); i++){
    if(dominates(landscape.neighborhod[i], solution_0)){
      solution_0 = landscape.neighborhod[i];
    }
  }

  pareto_front.push_back(solution_0);

  for(int i = 1; i < landscape.neighborhod.size(); i++){
    add_front_0(landscape.neighborhod[i], pareto_front);
  }
  
  return pareto_front.size();
}

void calculate_dominance_metrics(LandscapeElement &element){

  vector<Solution> neighborhood = element.neighborhod;

  //Calculating Dominance Metrics
    double num_neighbors = (double) neighborhood.size();

    int countDominating = 0;    // Number of neighbors that Current Solution Dominates
    int countIsDominated = 0;   // Number of neighbors that dominates Current Solution
    for(int i = 0; i < neighborhood.size(); i++){
      if(dominates(element.current_solution, neighborhood[i])){
        countDominating++;
      } else if(dominates(neighborhood[i], element.current_solution)){
        countIsDominated++;
      }
    }

    element.inf = countDominating / num_neighbors ;
    element.sup = countIsDominated / num_neighbors;
    element.inc = 1.0 - (element.inf + element.sup);
    element.ind = number_pareto_front(element) / num_neighbors;
}

pair<double, int> calculate_decomp_metrics(LandscapeElement &element){

  //Getting the value of tchebycheff function for the current solution 
  double current_solution_fitness = calculate_gte_metafeatures(element.current_solution.fitness, lambda_vector[iLandscape], global_z_point);
  element.tch_current_solution = current_solution_fitness;

  //Getting the min and max values of all solutions x
  if(current_solution_fitness < minimal){
    minimal = current_solution_fitness;
  }

  if(current_solution_fitness > maximal){
    maximal = current_solution_fitness;
  }

  //Finding the best neighbor and calculating its fitness
  double best_neighbor_fitness = numeric_limits<double>::infinity();
  int index_best_neighbor;

  for(int i = 0; i < element.neighborhod.size(); i++){
    double neighbor_solution_fitness = calculate_gte_metafeatures(element.neighborhod[i].fitness, lambda_vector[iLandscape], global_z_point);
    element.tchebycheff_neighbors.push_back(neighbor_solution_fitness);

    //Getting the min and max values of all solutions x
    if(neighbor_solution_fitness < minimal){
      minimal = neighbor_solution_fitness;
    }
    if(neighbor_solution_fitness > maximal){
      maximal = neighbor_solution_fitness;
    }

    if(neighbor_solution_fitness < best_neighbor_fitness){
      best_neighbor_fitness = neighbor_solution_fitness;
      index_best_neighbor = i;
    }
  }

  return make_pair(best_neighbor_fitness, index_best_neighbor);
}

#endif