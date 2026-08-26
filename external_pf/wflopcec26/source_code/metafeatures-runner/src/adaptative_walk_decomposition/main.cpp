#include <vector>
#include <random>
#include <iostream>
#include <limits> 

#include "./headers/metafeatures/decomposition_based/weight_vectors_metafeatures.h"
#include "./headers/metafeatures/decomposition_based/tchebycheff_metafeatures.h"
#include "./headers/metafeatures/decomposition_based/global_z_point.h"
#include "./headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "./headers/metafeatures/decomposition_based/mo_features_decomposition.h"

#include "./headers/metafeatures/walks/adaptative_walk_decomposition.h"

#include "./headers/metafeatures/normalization.h"
#include "./headers/metafeatures/metrics_extraction.h"
#include "./headers/metafeatures/features_extraction.h"
#include "./headers/metafeatures/pareto_based/mo_features_pareto.h"
#include "./headers/metafeatures/landscapeMetrics.h"
#include "./headers/metafeatures/landscapeElement.h"
#include "./headers/utils/features_csv.h"

#include "./modules/headers/dominates.h"
#include "./headers/instance_info.h"
#include "./headers/globals.h"


// ----- BEGIN: GLOBALS ------- 
vector<string> column_names_decomposition = {
      "FV_avg_avg", "FV_avg_sd", "FV_sd_avg", "FV_sd_sd", "FV_r1_avg", 
      "FV_r1_sd", "FV_kr_avg", "FV_kr_sd", "FV_sk_avg", "FV_sk_sd",
      "FD_avg_avg", "FD_avg_sd", "FD_sd_avg", "FD_sd_sd", "FD_r1_avg", 
      "FD_r1_sd", "FD_kr_avg", "FD_kr_sd", "FD_sk_avg", "FD_sk_sd",
      "IN_avg_avg", "IN_avg_sd", "IN_sd_avg", "IN_sd_sd", "IN_r1_avg", 
      "IN_r1_sd", "IN_kr_avg", "IN_kr_sd", "IN_sk_avg", "IN_sk_sd",
};

int iLandscape;
int countDecomp = 0;
bool limitReached = false;
int limit = 500000;
int *countReval = &countDecomp;
int walk_length = 8;
string folder_name_adaptative_walk;
string folder_name_random_walk;
vector<vector<LandscapeElement>> *updated_mult_walk;
float percent_neighbors = 1.0;

vector<pair<double, double>> lambda_vector;
pair<double, double> global_z_point;

//Getting the min and max values of all solutions x, ie, {max/min(F(x)) | 'x' in landscapes}
double maximal = numeric_limits<double>::lowest();
double minimal = numeric_limits<double>::infinity();

// ----- END: GLOBALS ------- 

vector<double> decomposition_extraction(vector<vector<LandscapeElement>> &landscapes){
  //Normalizing the landscapes elements
  normalization(landscapes, maximal, minimal);
  
  //METRICS -> Getting the metrics of each landscape of each type
  vector<LandscapeMetrics> metrics = metrics_extraction(landscapes);

  return mo_features_extraction(metrics);
}

void AP_decomposition_main(int qtd_of_landscapes, int number_of_neighbors){

  //Building the lambda vector, ie, the vector of weights to each subproblem i
  lambda_vector = build_weight_vector_metafeatures(qtd_of_landscapes);

  //Building a landscape for each subproblem
  vector<vector<LandscapeElement>> landscapes_adaptative_walk;

  //Getting the global z_point
  global_z_point = get_global_z_point();

  updated_mult_walk = &landscapes_adaptative_walk;

  for(int i = 0; i < qtd_of_landscapes; i++){
    iLandscape = i;
    landscapes_adaptative_walk.push_back(adaptative_walk_decomposition(number_of_neighbors));

    if(limitReached){
      break;
    }
  }

  auto AP_mo_decomposition_features = decomposition_extraction(landscapes_adaptative_walk);
  
  if (!limitReached){
    string file_name = "ofe_" + to_string(*countReval) + ".csv";
    build_csv(AP_mo_decomposition_features, column_names_decomposition, "dataset", instance, "decomposition_based", "adaptative_walk", folder_name_adaptative_walk, file_name);
  }
}

int main(int argc, char* argv[]){

  int num_neighbors = 200;
  int size_of_population = 20;

  get_instance_info(argc, argv);

  cout << "Instance: " << instance << endl << endl;

  cout << "Maximum neighbors: " << num_neighbors << endl;
  cout << "Percentage of neighbors: " << percent_neighbors << endl;
  cout << "Total number of neighbors analyzed: " << num_neighbors * percent_neighbors << endl << endl;
  
  cout << "Number of subproblems: " << size_of_population << endl << endl;
  
  int sum = 0;
  for(auto elem : turbines_per_zone)
    sum += elem;

  cout << "Number of fixed turbines: " << fixd.size() << endl;
  cout << "Number of mobile turbines: " << sum << endl;
  cout << "Wind: " << wind << endl;
  cout << "Angle: " << angle << endl << endl;

  cout << "Run time: " << endl; 

  AP_decomposition_main(size_of_population, num_neighbors * percent_neighbors);

  cout << "TOTAL NUMBER OF AVALIATIONS: " << *countReval;
}