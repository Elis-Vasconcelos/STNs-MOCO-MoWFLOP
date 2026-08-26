#include <vector>
#include <utility>
#include <iostream>
#include <limits> 

#include "../../headers/metafeatures/landscapeElement.h"
#include "../../headers/metafeatures/decomposition_based/tchebycheff_metafeatures.h"
#include "../../headers/metafeatures/walks/RW_decomposition.h"
#include "../../headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "../../modules/headers/population.h"
#include "../../headers/metafeatures/features_extraction.h"

#include "../../headers/utils/features_csv.h"

#include "../../headers/globals.h"

using namespace std;

pair<double, int> calculate_decomp_metrics(LandscapeElement *element, vector<Solution>* neighborhood){

  //Getting the value of tchebycheff function for the current solution 
  double current_solution_fitness = calculate_gte_metafeatures(element->current_solution.fitness, lambda_vector[iLandscape], global_z_point);
  element->tch_current_solution = current_solution_fitness;

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

  for(int i = 0; i < neighborhood->size(); i++){
    pair<double, double> fitness_value = (*neighborhood)[i].fitness;
    double neighbor_solution_fitness = calculate_gte_metafeatures(fitness_value, lambda_vector[iLandscape], global_z_point);
    element->tchebycheff_neighbors.push_back(neighbor_solution_fitness);

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

vector<LandscapeElement> random_walk(int walk_lenght, int number_of_neighbors, pair<double, double> &lambda, std::pair<double, double> &global_z_point, double &max, double &min){

  vector<LandscapeElement> S;
  Solution current_solution = create_initial_population(1)[0];
  *countReval = *countReval + 1;

  if(*countReval == limit){
    limitReached = true;
    auto result = decomposition_extraction(*updated_mult_walk);
    string file_name = "ofe_" + to_string(*countReval)+ ".csv";
    build_csv(result, column_names_decomposition, "dataset", instance, "decomposition_based", "random_walk", folder_name_random_walk, file_name);
    return S;
  } 

  for(int step = 0; step < walk_lenght; step++){
    LandscapeElement element;
    element.current_solution = current_solution; //Adding the 'current_solution' to S
    vector<Solution>* neighborhood = new vector<Solution>();
    Solution* neighbor;

    //Building the neighborhood of the current solution
    for(int i = 0; i < number_of_neighbors; i++){
      neighbor = get_neighbor(current_solution);

      if(*countReval == limit){
        limitReached = true;
        auto actual = *updated_mult_walk;
        vector<LandscapeElement>* walk_copy = new vector<LandscapeElement>(S);
        LandscapeElement* element_copy = new LandscapeElement(element);

        calculate_decomp_metrics(element_copy, neighborhood);
        
        walk_copy->push_back(*element_copy);
        actual.push_back(*walk_copy);

        auto result = decomposition_extraction(actual);
        string file_name = "ofe_" + to_string(*countReval) + ".csv";
        build_csv(result, column_names_decomposition, "dataset", instance, "decomposition_based", "random_walk", folder_name_random_walk, file_name);

        delete element_copy;
        delete walk_copy;
        return S;
      }

      while(isEqualNeighborhood(neighbor, neighborhood)){
        neighbor = get_neighbor(current_solution);

        if(*countReval == limit){
          limitReached = true;
          auto actual = *updated_mult_walk;
          vector<LandscapeElement>* walk_copy = new vector<LandscapeElement>(S);
          LandscapeElement* element_copy = new LandscapeElement(element); 

          calculate_decomp_metrics(element_copy, neighborhood);

          walk_copy->push_back(*element_copy);
          actual.push_back(*walk_copy);

          auto result = decomposition_extraction(actual);
          string file_name = "ofe_" + to_string(*countReval) + ".csv";
          build_csv(result, column_names_decomposition, "dataset", instance, "decomposition_based", "random_walk", folder_name_random_walk, file_name);

          delete element_copy;
          delete walk_copy;
          return S;
        }
      }
      
      neighborhood->push_back(*neighbor);
      delete neighbor;
    }

    calculate_decomp_metrics(&element, neighborhood);

    S.push_back(element);

    Solution random_neighbor = (*neighborhood)[rand() % neighborhood->size()];
    current_solution = random_neighbor;
    
    delete neighborhood;
    neighborhood = nullptr;
  }

  return S;
}