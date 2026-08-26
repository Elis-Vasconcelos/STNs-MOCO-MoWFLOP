#ifndef MAIN_PROGRAM_H
#define MAIN_PROGRAM_H

#include "../headers/instance_info.h"

#include "../headers/global_modules/generate_initial_population/population.h"
#include "../headers/global_modules/generate_initial_population/generate_rSolution.h"

#include "../headers/global_modules/genetic_operators/mutation.h"
#include "../headers/global_modules/genetic_operators/crossover.h"

#include "../headers/global_modules/isEqual.h"

#include "../headers/metaheuristics/moead/moead.h"
#include "../headers/metaheuristics/moead/modules/generate_neighborhood.h"
#include "../headers/metaheuristics/moead/modules/generate_weight_vectors.h"
#include "../headers/metaheuristics/moead/modules/get_best_z_point.h"
#include "../headers/metaheuristics/moead/modules/tchebycheff.h"

#include "./metaheuristics/nsga2/nsga2.h"
#include "./metaheuristics/nsga2/modules/binary_tournament.h"
#include "./metaheuristics/nsga2/modules/crowding_distance.h"
#include "./metaheuristics/nsga2/modules/non_dominated_sorting.h"
#include "./metaheuristics/nsga2/modules/arena_non_dominated_sorting.h"

#include "../headers/metaheuristics/comolsd/comolsd.h"
#include "../headers/metaheuristics/comolsd/modules/aggregation_wrapper.h"
#include "../headers/metaheuristics/comolsd/modules/build_neighborhood_decision_space.h"
#include "../headers/metaheuristics/comolsd/modules/calculate_ipbi.h"
#include "../headers/metaheuristics/comolsd/modules/calculate_ws.h"
#include "../headers/metaheuristics/comolsd/modules/codvs.h"
#include "../headers/metaheuristics/comolsd/modules/get_global_z_point.h"
#include "../headers/metaheuristics/comolsd/modules/get_global_nadir_point.h"
#include "../headers/metaheuristics/comolsd/modules/get_nadir_point.h"
#include "../headers/metaheuristics/comolsd/modules/local_search.h"
#include "../headers/metaheuristics/comolsd/modules/min_max_cost.h"
#include "../headers/metaheuristics/comolsd/modules/normalize_objectives.h"
#include "../headers/metaheuristics/comolsd/modules/unionFind.h"
#include "../headers/metaheuristics/comolsd/modules/update_population.h"


// #include "../metafeatures/features_extraction.cpp"
// #include "../metafeatures/modules/decomposition_based/get_global_z_point.cpp"
// #include "../metafeatures/modules/decomposition_based/tchebycheff_metafeatures.cpp"
// #include "../metafeatures/modules/decomposition_based/weight_vectors_metafeatures.cpp"
// #include "../metafeatures/modules/decomposition_based/get_neighborhood.cpp"
// #include "../metafeatures/modules/walks/random_walk.cpp"
// #include "../metafeatures/modules/walks/adaptative_walk.cpp"
// #include "../metafeatures/modules/normalization.cpp"

// #include "../metafeatures/modules/metrics_extraction.cpp"
// #include "../metafeatures/modules/decomposition_based/mo_features_decomposition.cpp"
// #include "../metafeatures/modules/pareto_based/mo_features_pareto.cpp"
// #include "../metafeatures/modules/statistical_functions.cpp"

#include "../headers/utils/features_csv.h"
#include "../headers/adaptative_grid/BoundedParetoSet.h"

#endif