#include <vector>
#include <utility>
#include <iostream>

#include "../../../headers/metafeatures/landscapeElement.h"
#include "../../../headers/metafeatures/decomposition_based/tchebycheff_metafeatures.h"
#include "../../../headers/metafeatures/walks/random_walk.h"
#include "../../../headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "../../../modules/headers/population.h"
#include "../../../headers/metafeatures/features_extraction.h"

#include "../../../headers/utils/features_csv.h"

using namespace std;

extern int* countReval;
extern int mode, defaultDecompPace, defaultDomPace;
extern vector<vector<LandscapeElement>> *updated_mult_walk;
extern vector<LandscapeElement> *updated_single_walk;

extern string folder_name_adaptative_walk;
extern string folder_name_random_walk;
extern vector<string> column_names_decomposition;
extern vector<string> column_names_pareto;

vector<LandscapeElement> random_walk(int walk_lenght, int number_of_neighbors, pair<double, double> &lambda, std::pair<double, double> &global_z_point, double &max, double &min){

  vector<LandscapeElement> S;
  updated_single_walk = &S;
  Solution current_solution = create_initial_population(1)[0];
  *countReval = *countReval + 1;

  if(mode == 0 && *countReval % defaultDecompPace == 0){
    auto result = decomposition_extraction(*updated_mult_walk);
    string file_name = "fv_" + to_string(*countReval)+ ".csv";
    build_csv(result, column_names_decomposition, "dataset", "decomposition_based", "random_walk", folder_name_random_walk, file_name);
  } else if (mode == 1 && *countReval % defaultDomPace == 0){
    auto result = dominance_extraction(*updated_single_walk);
    string file_name = "fv_" + to_string(*countReval) + ".csv";
    build_csv(result, column_names_decomposition, "dataset", "pareto_based", "random_walk", folder_name_random_walk, file_name);
  }

  for(int step = 0; step < walk_lenght; step++){
    LandscapeElement element;
    element.current_solution = current_solution; //Adding the 'current_solution' to S

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
        string file_name = "fv_" + to_string(*countReval) + ".csv";
        build_csv(result, column_names_decomposition, "dataset", "decomposition_based", "random_walk", folder_name_random_walk, file_name);
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
        string file_name = "fv_" + to_string(*countReval) + ".csv";
        build_csv(result, column_names_decomposition, "dataset", "pareto_based", "random_walk", folder_name_random_walk, file_name);
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
          string file_name = "fv_" + to_string(*countReval) + ".csv";
          build_csv(result, column_names_decomposition, "dataset", "decomposition_based", "random_walk", folder_name_random_walk, file_name);
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
          string file_name = "fv_" + to_string(*countReval) + ".csv";
          build_csv(result, column_names_decomposition, "dataset", "pareto_based", "random_walk", folder_name_random_walk, file_name);
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

    //Getting a random neighbor of the neighborhood of the current solution
    Solution random_neighbor = element.neighborhod[rand() % element.neighborhod.size()];

    current_solution = random_neighbor;
  }

  return S;
}
