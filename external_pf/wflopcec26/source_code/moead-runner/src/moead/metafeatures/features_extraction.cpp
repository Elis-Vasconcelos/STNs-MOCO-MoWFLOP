#include <vector>
#include <random>
#include <iostream>
#include <limits> 

#include "../headers/metafeatures/decomposition_based/weight_vectors_metafeatures.h"
#include "../headers/metafeatures/decomposition_based/tchebycheff_metafeatures.h"
#include "../headers/metafeatures/decomposition_based/global_z_point.h"
#include "../headers/metafeatures/decomposition_based/get_neighborhood.h"
#include "../headers/metafeatures/decomposition_based/mo_features_decomposition.h"

#include "../headers/metafeatures/walks/random_walk.h"
#include "../headers/metafeatures/walks/adaptative_walk.h"

#include "../headers/metafeatures/normalization.h"
#include "../headers/metafeatures/metrics_extraction.h"
#include "../headers/metafeatures/features_extraction.h"
#include "../headers/metafeatures/pareto_based/mo_features_pareto.h"
#include "../headers/metafeatures/landscapeMetrics.h"
#include "../headers/metafeatures/landscapeElement.h"
#include "../headers/utils/features_csv.h"

vector<string> column_names_decomposition = {
      "FV_avg_avg", "FV_avg_sd", "FV_sd_avg", "FV_sd_sd", "FV_r1_avg", 
      "FV_r1_sd", "FV_kr_avg", "FV_kr_sd", "FV_sk_avg", "FV_sk_sd",
      "FD_avg_avg", "FD_avg_sd", "FD_sd_avg", "FD_sd_sd", "FD_r1_avg", 
      "FD_r1_sd", "FD_kr_avg", "FD_kr_sd", "FD_sk_avg", "FD_sk_sd",
      "IN_avg_avg", "IN_avg_sd", "IN_sd_avg", "IN_sd_sd", "IN_r1_avg", 
      "IN_r1_sd", "IN_kr_avg", "IN_kr_sd", "IN_sk_avg", "IN_sk_sd",
};

vector<string> column_names_pareto = {
  "INF.avg", "INF.sd", "INF.r1", "INF.kr", "INF.sk",
  "SUP.avg", "SUP.sd", "SUP.r1", "SUP.kr", "SUP.sk",
  "INC.avg", "INC.sd", "INC.r1", "INC.kr", "INC.sk",
  "IND.avg", "IND.sd", "IND.r1", "IND.kr", "IND.sk",
};

extern string folder_name_adaptative_walk;

vector<pair<double, double>> lambda_vector;

pair<double, double> global_z_point;

//Getting the min and max values of all solutions x, ie, {max/min(F(x)) | 'x' in landscapes}
double maximal = numeric_limits<double>::lowest();
double minimal = numeric_limits<double>::infinity();

int iLandscape;

int countDecomp = 0;
int countPareto = 0;
int *countReval = &countDecomp;


int defaultDecompPace = 300;
int defaultDomPace = 200;

int mode = 0;
vector<vector<LandscapeElement>> *updated_mult_walk;
vector<LandscapeElement> *updated_single_walk;


vector<double> decomposition_extraction(vector<vector<LandscapeElement>> &landscapes){
  //Normalizing the landscapes elements
  normalization(landscapes, maximal, minimal);
  
  //METRICS -> Getting the metrics of each landscape of each type
  vector<LandscapeMetrics> metrics = metrics_extraction(landscapes);

  return mo_features_extraction(metrics);
}

vector<double> dominance_extraction(vector<LandscapeElement> &landscape){
  LandscapeMetrics metric = metric_extraction(landscape);

  return mo_features_extraction_pareto(metric);
}

void features_extraction(int qtd_of_landscapes, int walk_lenght, int number_of_neighbors){

  //Building the lambda vector, ie, the vector of weights to each subproblem i
  lambda_vector = build_weight_vector_metafeatures(qtd_of_landscapes);

  //Building a landscape for each subproblem
  vector<vector<LandscapeElement>> landscapes_random_walk;
  vector<vector<LandscapeElement>> landscapes_adaptative_walk_D; // Adaptative walk decomposition based
  vector<vector<LandscapeElement>> landscapes_adaptative_walk_P; // Adaptative walk pareto based

  //Getting the global z_point
  global_z_point = get_global_z_point();

  updated_mult_walk = &landscapes_random_walk;
  cout << endl << "Multi Random walk:" << endl;

  for(int i = 0; i < qtd_of_landscapes; i++){
    iLandscape = i;
    landscapes_random_walk.push_back(random_walk(walk_lenght, number_of_neighbors, lambda_vector[i], global_z_point, maximal, minimal));
  }

  countDecomp = 0;
  updated_mult_walk = &landscapes_adaptative_walk_D;
  cout << endl << "Multi adaptive decomposition walk:" << endl;

  for(int i = 0; i < qtd_of_landscapes; i++){
    iLandscape = i;
    landscapes_adaptative_walk_D.push_back(adaptive_walk_decomp(number_of_neighbors));
  }

  auto RW_mo_decomposition_features = decomposition_extraction(landscapes_random_walk);
  auto AWD_mo_decomposition_features = decomposition_extraction(landscapes_adaptative_walk_D);
  // auto AWP_mo_decomposition_features = decomposition_extraction(landscapes_adaptative_walk_P);

  countReval = &countPareto;
  mode = 1;

  //PARETO -> Getting the multiobjective features of each landscape of each type (random walk and adaptative walk)
  cout << endl << "Single Random walk:" << endl;
  auto single_random_walk = random_walk(walk_lenght, number_of_neighbors, lambda_vector[0], global_z_point, maximal, minimal);
  countPareto = 0;

  cout << endl << "Single adaptive dominance walk:" << endl;
  auto single_adaptive_walk_P = adaptive_walk(number_of_neighbors, pareto_next_solution);
  countPareto = 0;

  // cout << "Decomposition adaptive walk: " << single_adaptive_walk_D.size() << endl;
  cout << "Dominance adaptive walk: " << single_adaptive_walk_P.size() << endl;

  auto RW_mo_pareto_features = dominance_extraction(single_random_walk);
  // auto AWD_mo_pareto_features = dominance_extraction(single_adaptive_walk_D);
  auto AWP_mo_pareto_features = dominance_extraction(single_adaptive_walk_P);
}