#include <vector>
#include <utility>
#include <iostream>

#include "../../headers/metafeatures/landscapeElement.h"
#include "../../headers/metafeatures/decomposition_based/tchebycheff_metafeatures.h"
#include "../../headers/metafeatures/walks/random_walk_pareto.h"
#include "../../headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "../../modules/headers/population.h"
#include "../../headers/metafeatures/features_extraction.h"

#include "../../headers/utils/features_csv.h"
#include "../../modules/headers/dominates.h"

#include "../../headers/globals.h"

using namespace std;

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

int number_pareto_front(LandscapeElement *landscape, vector<Solution>* neighborhood){
  vector<Solution> pareto_front;
  Solution solution_0 = (*neighborhood)[0];

  for(int i = 0; i < (*neighborhood).size(); i++){
    if(dominates((*neighborhood)[i], solution_0)){
      solution_0 = (*neighborhood)[i];
    }
  }

  pareto_front.push_back(solution_0);

  for(int i = 1; i < (*neighborhood).size(); i++){
    add_front_0((*neighborhood)[i], pareto_front);
  }
  
  return pareto_front.size();
}

void calculate_dominance_metrics(LandscapeElement* element, vector<Solution>* neighborhood) {
    double num_neighbors = static_cast<double>(neighborhood->size());

    int countDominating = 0;    // Number of neighbors that Current Solution Dominates
    int countIsDominated = 0;   // Number of neighbors that Dominates Current Solution
    for (int i = 0; i < neighborhood->size(); i++) {
        if (dominates(element->current_solution, (*neighborhood)[i])) {
            countDominating++;
        } else if (dominates((*neighborhood)[i], element->current_solution)) {
            countIsDominated++;
        }
    }

    element->inf = countDominating / num_neighbors;
    element->sup = countIsDominated / num_neighbors;
    element->inc = 1.0 - (element->inf + element->sup);
    element->ind = number_pareto_front(element, neighborhood) / num_neighbors;
}

vector<LandscapeElement> random_walk(int walk_lenght, int number_of_neighbors){

  vector<LandscapeElement> S;
  updated_single_walk = &S;
  Solution current_solution = create_initial_population(1)[0];
  *countReval = *countReval + 1;

  if (*countReval == limit){
    limitReached = true;
    auto result = dominance_extraction(*updated_single_walk);
    string file_name = "ofe_" + to_string(*countReval) + ".csv";
    build_csv(result, column_names_pareto, "dataset", instance, "pareto_based", "random_walk", folder_name_random_walk, file_name);
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
        vector<LandscapeElement>* walk_copy = new vector<LandscapeElement>(S);
        LandscapeElement* element_copy = new LandscapeElement(element);

        calculate_dominance_metrics(element_copy, neighborhood);

        walk_copy->push_back(*element_copy);

        auto result = dominance_extraction(*walk_copy);
        string file_name = "ofe_" + to_string(*countReval) + ".csv";
        build_csv(result, column_names_pareto, "dataset", instance, "pareto_based", "random_walk", folder_name_random_walk, file_name);

        delete element_copy;
        delete walk_copy;
        return S;
      }

      while(isEqualNeighborhood(neighbor, neighborhood)){
        neighbor = get_neighbor(current_solution);

        if(*countReval == limit){
          limitReached = true;
          vector<LandscapeElement>* walk_copy = new vector<LandscapeElement>(S);
          LandscapeElement* element_copy = new LandscapeElement(element);

          calculate_dominance_metrics(element_copy, neighborhood);

          walk_copy->push_back(*element_copy);

          auto result = dominance_extraction(*walk_copy);
          string file_name = "ofe_" + to_string(*countReval) + ".csv";
          build_csv(result, column_names_pareto, "dataset", instance, "pareto_based", "random_walk", folder_name_random_walk, file_name);

          delete element_copy;
          delete walk_copy;
          return S;
        }
      }
      
      neighborhood->push_back(*neighbor);
      delete neighbor;
    }

    calculate_dominance_metrics(&element, neighborhood);

    S.push_back(element);

    Solution random_neighbor = (*neighborhood)[rand() % neighborhood->size()];
    current_solution = random_neighbor;
    
    delete neighborhood;
    neighborhood = nullptr;
  }

  return S;
}