#include <vector>
#include <utility>
#include <set>
#include <iostream>
#include "../../../../headers/metaheuristics/nsga2/modules/arena_non_dominated_sorting.h"
#include "../../../../headers/global_modules/dominates.h"
#include "../../../../headers/global_modules/isEqual.h"
#include "../../../../headers/globals.h"

vector<Solution*>* build_front(vector<Solution*> &population) {
  vector<Solution*>* Q = new vector<Solution*>(population.begin(), population.end()); 
  vector<Solution*>* Nds = new vector<Solution*>(); 

  while (!Q->empty()) {
    vector<Solution*> RK, R;  
    Solution* X = Q->back(); 
    Q->pop_back();

    for (auto it = Q->begin(); it != Q->end();) {
      if (dominates(*X, **it)) {
        it = Q->erase(it); // Q = Q − {Y}
      } else if (dominates(**it, *X)) {
        X = *it; // X = Y
        it = Q->erase(it); // Q = Q − {Y}
        RK.insert(RK.end(), R.begin(), R.end()); // RK = RK ∪ R
        R.clear(); // R = ∅
      } else {  
        R.push_back(*it); // R = R ∪ {Y}
        it = Q->erase(it); // Q = Q − {Y}
      }
    }

    vector<Solution*> RK_2;

    for (size_t i = 0; i < RK.size(); ++i) {
      if (!dominates(*X, *RK[i])) {
        RK_2.push_back(RK[i]);
      }
    }

    Nds->push_back(X); 

    Q->insert(Q->end(), RK_2.begin(), RK_2.end());
    Q->insert(Q->end(), R.begin(), R.end());

    if(Q->size() <= 1){
      Nds->insert(Nds->end(), Q->begin(), Q->end());
      break;
    }
  }

  for (size_t i = 0; i < Nds->size(); ++i) {
    for (auto it = population.begin(); it != population.end(); ) {
      if (isEqual(*Nds->at(i), **it)) {
        it = population.erase(it); 
      } else {
        ++it;
      }
    }
  }

  delete Q; 

  return Nds; 
}

vector<vector<Solution*>*> arena_non_dominated_sorting(vector<Solution*> &population) {
  vector<vector<Solution*>*> fronts;
  int population_count = 0; //A counter to see if we reach the 'size_of_population'

  while (!population.empty()) {
    auto front = build_front(population);
    population_count += front->size();

    fronts.push_back(front);

    if (population_count >= SIZE_OF_POPULATION) {
      break;
    }
  }
  
  return fronts;
}