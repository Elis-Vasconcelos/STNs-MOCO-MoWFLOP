#include "../../../../headers/global_modules/generate_initial_population/generate_rSolution.h"
#include "../../../../headers/global_modules/dominates.h"
#include "../../../../headers/global_modules/isEqual.h"
#include "../../../../headers/adaptative_grid/ParetoSet.h"

#include "../../../../headers/metaheuristics/moead/modules/updateEP.h"

void updateEP(list<Solution *> &EP, Solution *child){
  // Step 2.5: Update EP for child1
  // Remove dominated solutions from EP and add the new solutions (child) if it's not dominated
  
  // // Remove solutions dominated by child
  // EP.erase(remove_if(EP.begin(), EP.end(), [&](const Solution &sol) {
  //   return dominates(child, sol);
  // }), EP.end());

  list<Solution *>::iterator i = EP.begin();
  list< list<Solution *>::iterator > remover;
  while (i != EP.end()) {
    if (dominates(*child, **i)) {
      remover.push_back(i);
    }
    if (dominates(**i, *child)|| equals(**i, *child)){
      return;
    }
    i++;
	}


  list< list<Solution *>::iterator >::iterator j = remover.begin();
	while (j != remover.end()) {
		delete( **j );
		
    EP.erase(*j);
		j++;
	}

  // Check if the new child is dominated by any solution in EP or if it's already in EP
  // bool is_dominated = false;
  // bool already_exists = false;

  // for (const auto sol : EP) {
  //   if (dominates(*sol, *child)) {
  //     is_dominated = true;
  //     break;
  //   }
  //   if (isEqual(*sol, *child)) {
  //     already_exists = true;
  //     break;
  //   }
  // }  

  // if (!is_dominated && !already_exists) {
    Solution *t = new Solution;
    *t = *child;
    EP.push_back(t);
  // }
}