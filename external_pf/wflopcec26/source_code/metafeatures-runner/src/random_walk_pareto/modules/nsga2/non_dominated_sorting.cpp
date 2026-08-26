#include <vector>
#include <utility>
#include <iostream>
#include "../headers/non_dominated_sorting.h"
#include "../headers/dominates.h"

//Check if a SolutionA dominates a SolutionB
bool dominates(Solution solutionA, Solution solutionB){
  return (solutionA.fitness.first >= solutionB.fitness.first && solutionA.fitness.second >= solutionB.fitness.second) && (solutionA.fitness.first > solutionB.fitness.first || solutionA.fitness.second > solutionB.fitness.second);
}

//Building the fronts
vector<vector<Solution>> non_dominated_sorting(vector<Solution>& solutions){
  vector<vector<int>> fronts_indices; // It's a vector that contains each front (that is, the indexes of the solutions in each front)
  vector<int> first_front; // Contains the solutions' indexes that are in the first front

  /* We're creating a scheme to build the fronts considering the index of each solution in 'solutions'.
  Each solutions[i] will have a number of solutions that domines it (domination_count). 
  - To reach the domination_count of a solution i (solutions[i]), we only need to access domination_count_vector[i]
  Each solutions[i] will have a vector of indexes of solutions that are dominated by it (domination_vector).
  - To reach the domination_vector of a solution i (solutions[i]), we only need to access domination_vector[i]*/

  vector<vector<int>> domination_vector(solutions.size()); // A vector of solutions' indexes that are dominated by solutions[i]
  vector<int> domination_count_vector(solutions.size()); // A vector of int that represents the number of solutions that dominates solutions[i] (domination_count)

  // Getting the first front 
  for(int p = 0; p < solutions.size(); p++){
    int domination_count = 0;
    for(int q = 0; q < solutions.size(); q++){
      if(p != q){
        if(dominates(solutions[p], solutions[q])){
          domination_vector[p].push_back(q); // Adding the index of the solution q to domination_vector[p], since solutions[p] domines solutions[q]
        }
        else if(dominates(solutions[q], solutions[p])){
          domination_count++;
        }
      }
    }

    domination_count_vector[p] = domination_count;

    if(domination_count == 0){
      first_front.push_back(p);
    }
  }

  fronts_indices.push_back(first_front);
  
  int i = 0; // Front counter
  while(!fronts_indices[i].empty()){
    vector<int> next_front;

    for (int p_index : fronts_indices[i]) {
      for (int q_index : domination_vector[p_index]) {
        /* Here we're accessing the domination_count of the solution q that it's dominated by p. 
        For this, we need the index of q in solutions. To reach this, notice that
        q is dominated by p, ie, q belongs to domination_vector[p_index]. */
        domination_count_vector[q_index]--;

        if (domination_count_vector[q_index] == 0) {
          next_front.push_back(q_index);
        }
      }
    }
    i++;
    fronts_indices.push_back(next_front);
  }

  if (fronts_indices.back().empty()) {
    fronts_indices.pop_back();
  }

  // Converting back the indices to the solutions
  vector<vector<Solution>> fronts;
  for (const auto& front : fronts_indices) {
    vector<Solution> front_solutions;
    for (int index : front) {
      front_solutions.push_back(solutions[index]);
    }
    fronts.push_back(front_solutions);
  }

  return fronts;
}