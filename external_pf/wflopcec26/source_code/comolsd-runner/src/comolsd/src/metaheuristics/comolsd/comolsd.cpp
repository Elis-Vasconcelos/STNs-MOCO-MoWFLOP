#include <utility>
#include <vector>
#include <iostream>
#include <ctime> 
#include <algorithm>

#include "../../../headers/global_modules/generate_initial_population/population.h"
#include "../../../headers/global_modules/generate_initial_population/generate_rSolution.h"

#include "../../../headers/metaheuristics/comolsd/modules/calculate_ws.h"
#include "../../../headers/metaheuristics/comolsd/modules/local_search.h"
#include "../../../headers/metaheuristics/comolsd/modules/codvs.h"
#include "../../../headers/metaheuristics/comolsd/modules/update_population.h"
#include "../../../headers/metaheuristics/comolsd/modules/get_nadir_point.h"
#include "../../../headers/metaheuristics/comolsd/modules/aggregation_wrapper.h"
#include "../../../headers/metaheuristics/comolsd/modules/get_global_z_point.h"
#include "../../../headers/metaheuristics/comolsd/modules/get_global_nadir_point.h"
#include "../../../headers/metaheuristics/comolsd/modules/min_max_cost.h"

#include "../../../headers/metaheuristics/moead/modules/generate_weight_vectors.h"
#include "../../../headers/metaheuristics/moead/modules/generate_neighborhood.h"
#include "../../../headers/metaheuristics/moead/modules/get_best_z_point.h"

#include "../../../headers/metaheuristics/comolsd/comolsd.h"

using namespace std;

void comolsd(vector<Solution>& population_p){

  //COMOLS_D parameters 
  int size_population = population_p.size();
  int number_of_neighbors = 10;
  
  //Building the first predefined direction vector (w1), ie, the vector of weights to each subproblem i
  vector<pair<double, double>> w1 = build_weight_vector(size_population); 
  
  //Getting z_point
  pair<double, double> ideal_point = get_best_z_point(population_p); //Ideal z* point
  pair<double, double> nadir_point = get_nadir_point(population_p);

  // Getting global points to be used on normalization
  pair<double, double> interval = min_max_cost(); //Interval consists on the (min_cost, max_cost)
  pair<double, double> global_nadir_point = get_global_nadir_point(interval.first);
  pair<double, double> global_ideal_point = get_global_z_point(interval.second);

  //Set Q
  vector<Solution> population_q;
  
  int generation = 0;

  ofstream infoRun(root_folder + "infoRun.txt");
  
  while (countRevalue < stop_criteria) {
    infoRun << "Generation " << generation << " | Revalues: " << countRevalue << " | GridSize: " << pareto->getSize() << endl;

    local_search(population_p, w1, ideal_point, number_of_neighbors, make_aggregation_function(calculate_ws, global_ideal_point, global_nadir_point));

    vector<Solution> union_pq = population_p;
    union_pq.insert(union_pq.end(), population_q.begin(), population_q.end());

    // Updating the ideal z* point and the nadir point
    for (const auto& sol : union_pq) {
        // Updates ideal point (z*)
        ideal_point.first = max(ideal_point.first, sol.fitness.first);
        ideal_point.second = max(ideal_point.second, sol.fitness.second);
        
        // Updates nadir point (z^nad)
        nadir_point.first = min(nadir_point.first, sol.fitness.first);
        nadir_point.second = min(nadir_point.second, sol.fitness.second);
    }

    auto w2 = codvs(nadir_point, population_p, population_q, size_population);

    population_q = update_population(w2, union_pq, nadir_point, make_aggregation_function(calculate_ipbi, global_ideal_point, global_nadir_point));

    local_search(population_q, w2, nadir_point, number_of_neighbors, make_aggregation_function(calculate_ipbi, global_ideal_point, global_nadir_point));

    population_p = update_population(w1, union_pq, ideal_point, make_aggregation_function(calculate_ws, global_ideal_point, global_nadir_point));
    
    generation++;
  }
  
  infoRun.close();

}