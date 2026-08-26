#include <vector>
#include <utility>
#include <limits>
#include <iostream>

#include "../../../headers/metafeatures/walks/adaptative_walk.h"
#include "../../../headers/metafeatures/landscapeElement.h"
#include "../../../headers/metafeatures/decomposition_based/tchebycheff_metafeatures.h"
#include "../../../modules/headers/population.h"
#include "../../../headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "../../../headers/metafeatures/features_extraction.h"

#include "../../../headers/utils/features_csv.h"


using namespace std;

extern int *countReval;
extern int mode, defaultDecompPace, defaultDomPace;
extern vector<vector<LandscapeElement>> *updated_mult_walk;
extern vector<LandscapeElement> *updated_single_walk;

extern vector<pair<double, double>> lambda_vector;
extern pair<double, double> global_z_point;
extern double maximal, minimal;
extern int iLandscape;

extern string folder_name_adaptative_walk;
extern vector<string> column_names_decomposition;
extern vector<string> column_names_pareto;

vector<LandscapeElement> adaptive_walk_decomp(int number_of_neighbors) {

  pair<double, double> lambda = lambda_vector[iLandscape];
  vector<LandscapeElement> S;
  updated_single_walk = &S;
  Solution current_solution = create_initial_population(1)[0];
  *countReval = *countReval + 1;

  if(mode == 0 && *countReval % defaultDecompPace == 0){
    auto result = decomposition_extraction(*updated_mult_walk);
    string file_name = "fv_" + to_string(*countReval) + ".csv";
    build_csv(result, column_names_decomposition, "dataset", "decomposition_based", "adaptative_walk", folder_name_adaptative_walk, file_name);
  } else if (mode == 1 && *countReval % defaultDomPace == 0){
    auto result = dominance_extraction(*updated_single_walk);
  }

  //Definition of z_point
  
  while (true) {
    LandscapeElement element;
    element.current_solution = current_solution;
    Solution neighbor;

    //Building the neighborhood of the current solution
    for(int i = 0; i < number_of_neighbors; i++){
      neighbor = get_neighbor(current_solution);

      if(mode == 0 && *countReval % defaultDecompPace == 0){
        auto actual = *updated_mult_walk;
        auto walk_copy = S;
        auto element_copy = element;

        calculate_decomp_metrics(element_copy);
        calculate_dominance_metrics(element_copy);

        walk_copy.push_back(element_copy);
        actual.push_back(walk_copy);

        auto result = decomposition_extraction(actual);

        string file_name = "fv_" + to_string(*countReval) + ".csv";
        build_csv(result, column_names_decomposition, "dataset", "decomposition_based", "adaptative_walk", folder_name_adaptative_walk, file_name);
        cout << *countReval << ". Decomposition ";
        for (double d : result){
          cout << d << " ";
        } cout << endl;
      } else if(mode == 1 && *countReval % defaultDomPace == 0){
        auto walk_copy = S;
        auto element_copy = element;

        calculate_decomp_metrics(element_copy);
        calculate_dominance_metrics(element_copy);

        walk_copy.push_back(element_copy);

        auto result = dominance_extraction(walk_copy);
        cout << *countReval << ". Dominance: ";
        for (double d : result){
          cout << d << " ";
        } cout << endl;
      }

      while(isEqualNeighborhood(neighbor, element.neighborhod)){
        neighbor = get_neighbor(current_solution);

        if(mode == 0 && *countReval % defaultDecompPace == 0){
          auto actual = *updated_mult_walk;
          auto walk_copy = S;
          auto element_copy = element;

          calculate_decomp_metrics(element_copy);
          calculate_dominance_metrics(element_copy);

          walk_copy.push_back(element_copy);
          actual.push_back(walk_copy);
          

          auto result = decomposition_extraction(actual);

          string file_name = "fv_" + to_string(*countReval) + ".csv";
          build_csv(result, column_names_decomposition, "dataset", "decomposition_based", "adaptative_walk", folder_name_adaptative_walk, file_name);
        
          cout << *countReval << ". Decomposition ";
          for (double d : result){
            cout << d << " ";
          } cout << endl;
        } else if(mode == 1 && *countReval % defaultDomPace == 0){
          auto walk_copy = S;
          auto element_copy = element;

          calculate_decomp_metrics(element_copy);
          calculate_dominance_metrics(element_copy);

          walk_copy.push_back(element_copy);

          auto result = dominance_extraction(walk_copy);
          cout << *countReval << ". Dominance: ";
          for (double d : result){
            cout << d << " ";
          } cout << endl;
        }
      }

      element.neighborhod.push_back(neighbor);
    }

    auto best_solution = calculate_decomp_metrics(element);

    calculate_dominance_metrics(element);

    S.push_back(element);

    //Defining the next 'current_solution' of the walk
    if(best_solution.first < element.tch_current_solution){
      current_solution = element.neighborhod[best_solution.second];
    } else{
      break;
    }
  }
  return S;
}

vector<LandscapeElement> adaptive_walk(int number_of_neighbors, Solution (*next_solution) (const LandscapeElement &)){

  vector<LandscapeElement> S;
  updated_single_walk = &S;
  Solution current_solution = create_initial_population(1)[0];
  *countReval = *countReval + 1;
  
  if(mode == 0 && *countReval % defaultDecompPace == 0){
    auto result = decomposition_extraction(*updated_mult_walk);
  } else if (mode == 1 && *countReval % defaultDomPace == 0){
    auto result = dominance_extraction(*updated_single_walk);
    string file_name = "fv_" + to_string(*countReval) + ".csv";
    build_csv(result, column_names_pareto, "dataset", "pareto_based", "adaptative_walk", folder_name_adaptative_walk, file_name);
  }

  while (true) {
    LandscapeElement element;
    element.current_solution = current_solution;

    //Building the neighborhood of the current solution
    for(int i = 0; i < number_of_neighbors; i++){
      Solution neighbor = get_neighbor(current_solution);

      if(mode == 0 && *countReval % defaultDecompPace == 0){
        auto actual = *updated_mult_walk;
        auto walk_copy = S;
        auto element_copy = element;

        calculate_decomp_metrics(element_copy);
        calculate_dominance_metrics(element_copy);

        walk_copy.push_back(element_copy);
        actual.push_back(walk_copy);

        auto result = decomposition_extraction(actual);
        cout << *countReval << ". Decomposition ";
        for (double d : result){
          cout << d << " ";
        } cout << endl;
      } else if(mode == 1 && *countReval % defaultDomPace == 0){
        auto walk_copy = S;
        auto element_copy = element;

        calculate_decomp_metrics(element_copy);
        calculate_dominance_metrics(element_copy);

        walk_copy.push_back(element_copy);

        auto result = dominance_extraction(walk_copy);
        string file_name = "fv_" + to_string(*countReval) + ".csv";
        build_csv(result, column_names_pareto, "dataset", "pareto_based", "adaptative_walk", folder_name_adaptative_walk, file_name);
        cout << *countReval << ". Dominance: ";
        for (double d : result){
          cout << d << " ";
        } cout << endl;
      }

      while(isEqualNeighborhood(neighbor, element.neighborhod)){
        neighbor = get_neighbor(current_solution);

        if(mode == 0 && *countReval % defaultDecompPace == 0){
          auto actual = *updated_mult_walk;
          auto walk_copy = S;
          auto element_copy = element;

          calculate_decomp_metrics(element_copy);
          calculate_dominance_metrics(element_copy);

          walk_copy.push_back(element_copy);
          actual.push_back(walk_copy);

          auto result = decomposition_extraction(actual);
          cout << *countReval << ". Decomposition ";
          for (double d : result){
            cout << d << " ";
          } cout << endl;
        } else if(mode == 1 && *countReval % defaultDomPace == 0){
          auto walk_copy = S;
          auto element_copy = element;

          calculate_decomp_metrics(element_copy);
          calculate_dominance_metrics(element_copy);

          walk_copy.push_back(element_copy);

          auto result = dominance_extraction(walk_copy);
          string file_name = "fv_" + to_string(*countReval) + ".csv";
          build_csv(result, column_names_pareto, "dataset", "pareto_based", "adaptative_walk", folder_name_adaptative_walk, file_name);
          cout << *countReval << ". Dominance: ";
          for (double d : result){
            cout << d << " ";
          } cout << endl;
        }
      }

      element.neighborhod.push_back(neighbor);
    }

    calculate_decomp_metrics(element);

    calculate_dominance_metrics(element);

    S.push_back(element);

    current_solution = next_solution(element);

    if(current_solution.fitness.first == element.current_solution.fitness.first && current_solution.fitness.second == element.current_solution.fitness.second){
      break;
    }
  }

  return S;
}

Solution pareto_next_solution(const LandscapeElement &element){
  Solution best_solution;

  best_solution = element.current_solution;

  for(Solution sol : element.neighborhod){
    if(dominates(sol, best_solution)){
      return sol;
    }
  }

  return best_solution;
}