#include "../../headers/population.h"
#include "../../headers/mutation2.h"
#include "../../headers/updateEP.h"

#include <algorithm>
#include <random>
#include <ctime> 
#include <cstdlib>
using namespace std;

/*The goal of the mutation is: randomly select two positions in zone i of solution.grid
(rand_intA, rand_intB) ensuring that rand_intA and rand_intB are different and that both 
are not available positions.

Next, we swap the genes (turbine_id) between grid[zone][rand_intA] and grid[zone][rand_intB].

In addition, for each gene swap (turbine_id), we must also swap the turbine information 
contained in each grid[zone][rand_intA] and grid[zone][rand_intB] position. There are three cases:

1. grid[zone][rand_intA] and grid[zone][rand_intB] both have a turbine (indexA != -1 and indexB != -1).

2. Only grid[zone][rand_intA] has a turbine (indexA != -1 and indexB == -1).

3. Only grid[zone][rand_intB] has a turbine (indexA == -1 and indexB != -1).

PS: In all cases, indexA and indexB are, respectively, the indices of the turbines at position 
grid[zone][rand_intA] and position grid[zone][rand_intB]. 
When grid[zone][rand_intA] = 0, then there is no turbine at that position and, therefore, indexA == -1.

PS: THIS IS DONE FOR ALL ZONES i SUCH AS i < num_zones.*/

//Function to find the index of a turbine (searching for its id) within of a vector of turbines in zone i.

void mutationAux2(Solution &solution, int zone, double input_mutation_prob, vector<Solution> &EP){
    random_device rd;
    mt19937 gen(rd());

    int zone_size = solution.turbines[zone].size();
    int rand_intB;
    int indexA = -1;
    int indexB = -1;

    for(int i = 0; i < zone_size; ++i){
      if((static_cast<double>(rand()) / RAND_MAX) < input_mutation_prob){
        do {
          rand_intB = rand() % solution.grid[zone].size();
        } while(solution.grid[zone][rand_intB] != 0); 
  
        int geneA = solution.turbines[zone][i].index;
        int geneB = 0;

        solution.turbines[zone][i].index = rand_intB;
        solution.turbines[zone][i].x = foundations[zone][rand_intB].x;
        solution.turbines[zone][i].y = foundations[zone][rand_intB].y;

        solution.grid[zone][geneA] = 0;
        solution.grid[zone][rand_intB] = solution.turbines[zone][i].id;

        updateEP(EP, solution);
      }
    }
}

void mutation2(Solution &solution, double input_mutation_prob, vector<Solution> &EP){
  for(int i = 0; i < num_zones; i++){
    mutationAux2(solution, i, input_mutation_prob, EP);
  }

  calculate_cost(solution);
  calculate_power(solution);
}