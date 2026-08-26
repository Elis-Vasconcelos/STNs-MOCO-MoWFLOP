#include "../../../../headers/metaheuristics/comolsd/modules/build_neighborhood_decision_space.h"
#include "../../../../headers/global_modules/genetic_operators/mutation.h"

using namespace std;

vector<Solution> build_neighborhood_decision_space(const Solution& parent, int number_of_neighbors) {
    vector<Solution> neighborhood;
    neighborhood.reserve(number_of_neighbors);  

    for (int i = 0; i < number_of_neighbors; ++i) {
        Solution neighbor = parent;
        mutation(neighbor);  
        neighborhood.push_back(neighbor);
    }

    return neighborhood;
}
