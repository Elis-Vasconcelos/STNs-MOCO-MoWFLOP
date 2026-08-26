#include "../../headers/population.h"
#include "../../headers/mutation.h"
#include <algorithm>
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
int find_index(vector<Turbine> &vec, int value){
  for(int i = 0; i < vec.size(); i++){
    if(vec[i].id == value){
      return i;
    }
  }

  return -1;
}

void mutationAux(Solution &solution, int zone){

    int zone_size = solution.grid[zone].size();
    int rand_intA, rand_intB;
    int indexA = -1;
    int indexB = -1;

    // Select two positions at random in zone i of the solution.grid
    // Ensure that rand_intA and rand_intB are different and both are not a available position
    do{
      rand_intA = rand() % zone_size;
      rand_intB = rand() % zone_size;
    } while(rand_intA == rand_intB || (solution.grid[zone][rand_intA] == 0 && solution.grid[zone][rand_intB] == 0));

    // Swapping the genes (turbine_id) betwen grid[zone][rand_intA] e grid[zone][rand_intB]
    int geneA = solution.grid[zone][rand_intA];
    int geneB = solution.grid[zone][rand_intB];

    if(solution.grid[zone][rand_intA] != 0){
      indexA = find_index(solution.turbines[zone], solution.grid[zone][rand_intA]);
    }

    if(solution.grid[zone][rand_intB] != 0){
      indexB = find_index(solution.turbines[zone], solution.grid[zone][rand_intB]);
    }

    if(indexA != -1 && indexB != -1){
      int index;
      double x, y;

      index = solution.turbines[zone][indexA].index;
      x = solution.turbines[zone][indexA].x;
      y = solution.turbines[zone][indexA].y;

      solution.turbines[zone][indexA].index = solution.turbines[zone][indexB].index;
      solution.turbines[zone][indexA].x = solution.turbines[zone][indexB].x;
      solution.turbines[zone][indexA].y = solution.turbines[zone][indexB].y;

      solution.turbines[zone][indexB].index = index;
      solution.turbines[zone][indexB].x = x;
      solution.turbines[zone][indexB].y = y;
    } else if (indexA != -1 && indexB == -1){
      solution.turbines[zone][indexA].index = rand_intB;
      solution.turbines[zone][indexA].x = foundations[zone][rand_intB].x;
      solution.turbines[zone][indexA].y = foundations[zone][rand_intB].y;
    } else {
      solution.turbines[zone][indexB].index = rand_intA;
      solution.turbines[zone][indexB].x = foundations[zone][rand_intA].x;
      solution.turbines[zone][indexB].y = foundations[zone][rand_intA].y;
    }

    solution.grid[zone][rand_intA] = geneB;
    solution.grid[zone][rand_intB] = geneA;
}

void mutation(Solution &solution){
  for(int i = 0; i < num_zones; i++){
    mutationAux(solution, i);
  }

  calculate_cost(solution);
  calculate_power(solution);
}