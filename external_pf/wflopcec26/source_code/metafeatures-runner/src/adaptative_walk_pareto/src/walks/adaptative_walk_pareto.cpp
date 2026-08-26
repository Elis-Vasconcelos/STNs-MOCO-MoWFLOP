#include <vector>
#include <utility>
#include <iostream>

#include "../../headers/metafeatures/landscapeElement.h"
#include "../../headers/metafeatures/decomposition_based/tchebycheff_metafeatures.h"
#include "../../headers/metafeatures/walks/adaptative_walk_decomposition.h"
#include "../../headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "../../modules/headers/population.h"
#include "../../headers/metafeatures/features_extraction.h"

#include "../../headers/utils/features_csv.h"

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

vector<LandscapeElement> adaptative_walk_pareto(int number_of_neighbors, Solution (*next_solution) (const LandscapeElement &, const std::vector<Solution>*)){

  vector<LandscapeElement> S;
  updated_single_walk = &S;
  Solution current_solution = create_initial_population(1)[0];
  *countReval = *countReval + 1;

  if (*countReval == limit){
    limitReached = true;
    auto result = dominance_extraction(*updated_single_walk);
    string file_name = "ofe_" + to_string(*countReval) + ".csv";
    build_csv(result, column_names_pareto, "dataset", instance, "pareto_based", "adaptative_walk", folder_name_adaptative_walk, file_name);
    return S;
  }

  //Definition of z_point
  
  while (true) {
    LandscapeElement element;
    element.current_solution = current_solution;
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
        build_csv(result, column_names_pareto, "dataset", instance, "pareto_based", "adaptative_walk", folder_name_adaptative_walk, file_name);

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
          build_csv(result, column_names_pareto, "dataset", instance, "pareto_based", "adaptative_walk", folder_name_adaptative_walk, file_name);

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

    current_solution = next_solution(element, neighborhood);

    if(current_solution.fitness.first == element.current_solution.fitness.first && current_solution.fitness.second == element.current_solution.fitness.second){
      break;
    }

    delete neighborhood;
    neighborhood = nullptr;
  }
  return S;
}

Solution pareto_next_solution(const LandscapeElement &element, const vector<Solution>* neighborhood){
  Solution best_solution;

  best_solution = element.current_solution;

  for(int i = 0; i < (*neighborhood).size(); i++){
    if(dominates((*neighborhood)[i], best_solution)){
      return (*neighborhood)[i];
    }
  }

  return best_solution;
}
