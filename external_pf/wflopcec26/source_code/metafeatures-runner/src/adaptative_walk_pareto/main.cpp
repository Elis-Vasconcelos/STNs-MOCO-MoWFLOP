#include <vector>
#include <random>
#include <iostream>
#include <limits> 

#include "./headers/metafeatures/decomposition_based/weight_vectors_metafeatures.h"
#include "./headers/metafeatures/decomposition_based/tchebycheff_metafeatures.h"
#include "./headers/metafeatures/decomposition_based/global_z_point.h"
#include "./headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "./headers/metafeatures/decomposition_based/mo_features_decomposition.h"

#include "./headers/metafeatures/walks/adaptative_walk_pareto.h"

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
vector<string> column_names_pareto = {
  "INF_avg", "INF_sd", "INF_r1", "INF_kr", "INF_sk",
  "SUP_avg", "SUP_sd", "SUP_r1", "SUP_kr", "SUP_sk",
  "INC_avg", "INC_sd", "INC_r1", "INC_kr", "INC_sk",
  "IND_avg", "IND_sd", "IND_r1", "IND_kr", "IND_sk",
};

int iLandscape;
int countDecomp = 0;
bool limitReached = false;
int limit = 500000;
int *countReval = &countDecomp;
int defaultDomPace = 100;
int walk_length = 8;
string folder_name_adaptative_walk;
string folder_name_random_walk;
vector<LandscapeElement> *updated_single_walk;
float percent_neighbors = 1.0;

vector<pair<double, double>> lambda_vector;
pair<double, double> global_z_point;

//Getting the min and max values of all solutions x, ie, {max/min(F(x)) | 'x' in landscapes}
double maximal = numeric_limits<double>::lowest();
double minimal = numeric_limits<double>::infinity();

// ----- END: GLOBALS ------- 

vector<double> dominance_extraction(vector<LandscapeElement> &landscape){
  LandscapeMetrics metric = metric_extraction(landscape);

  return mo_features_extraction_pareto(metric);
}

void AP_pareto_main(int qtd_of_landscapes, int number_of_neighbors){

  auto single_adaptive_walk_P = adaptative_walk_pareto(number_of_neighbors, pareto_next_solution);

  auto AWP_mo_pareto_features = dominance_extraction(single_adaptive_walk_P);

  if(!limitReached){
    string file_name = "ofe_" + to_string(*countReval) + ".csv";
    build_csv(AWP_mo_pareto_features, column_names_pareto, "dataset", instance, "pareto_based", "adaptative_walk", folder_name_adaptative_walk, file_name);
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

  AP_pareto_main(size_of_population, num_neighbors * percent_neighbors);
  
  cout << endl;

  cout << "TOTAL NUMBER OF AVALIATIONS: " << *countReval;
}