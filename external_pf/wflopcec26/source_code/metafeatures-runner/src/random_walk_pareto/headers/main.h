#ifndef MAIN_PROGRAM_H
#define MAIN_PROGRAM_H

#include "../instance_info.cpp"

#include "../modules/generate_initial_population/generate_random_solution/generate_rSolution.cpp"
#include "../modules/generate_initial_population/generate_population/population.cpp"

#include "../modules/genetic_operators/mutation/mutation.cpp"
#include "../modules/genetic_operators/mutation/mutation2.cpp"
#include "../modules/genetic_operators/mutation/mutationFeature.cpp"
#include "../modules/genetic_operators/crossover/crossover.cpp"

#include "../metaheuristics/general_modules/isEqual.cpp"
#include "../metaheuristics/general_modules/solution_validator.cpp"

#include "../metaheuristics/moead/moead.cpp"
#include "../modules/moead/generate_weight_vectors.cpp"
#include "../modules/moead/generate_neighborhood.cpp"
#include "../modules/moead/get_best_z_point.cpp"
#include "../modules/moead/tchebycheff.cpp"
#include "../modules/moead/updateEP.cpp"

#include "../metaheuristics/nsga2/nsga2.cpp"
#include "../modules/nsga2/binary_tournament.cpp"
#include "../modules/nsga2/crowding_distance.cpp"
#include "../modules/nsga2/non_dominated_sorting.cpp"

#include "../metafeatures/features_extraction.cpp"
#include "../metafeatures/modules/decomposition_based/get_global_z_point.cpp"
#include "../metafeatures/modules/decomposition_based/tchebycheff_metafeatures.cpp"
#include "../metafeatures/modules/decomposition_based/weight_vectors_metafeatures.cpp"
#include "../metafeatures/modules/decomposition_based/get_neighborhood.cpp"
#include "../metafeatures/modules/walks/random_walk.cpp"
#include "../metafeatures/modules/walks/adaptative_walk.cpp"
#include "../metafeatures/modules/normalization.cpp"

#include "../metafeatures/modules/metrics_extraction.cpp"
#include "../metafeatures/modules/decomposition_based/mo_features_decomposition.cpp"
#include "../metafeatures/modules/pareto_based/mo_features_pareto.cpp"
#include "../metafeatures/modules/statistical_functions.cpp"

#include "../utils/features_csv.cpp"

#endif