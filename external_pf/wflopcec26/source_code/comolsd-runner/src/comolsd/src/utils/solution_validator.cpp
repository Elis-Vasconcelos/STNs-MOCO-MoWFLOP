#include "../../headers/global_modules/generate_initial_population/generate_rSolution.h"
#include <iostream>
using namespace std;

bool isValid(Solution &solution){

  for(int zone = 0; zone < num_zones; zone++){

    //Checking if the number of turbines in each zone is correct

    //Checking if each turbine in the grid is correct (according to foundations)

    for(int i = 0; i < solution.turbines[zone].size(); i++){
      int index_foundation = solution.turbines[zone][i].index;
      int turbine_id_grid = solution.grid[zone][index_foundation];
      int turbine_id = solution.turbines[zone][i].id;
      if(!(turbine_id_grid == turbine_id)){
        cout << turbine_id << " " << turbine_id_grid << endl;
        cout << "Grid diffes in turbine positions" << endl;
        return false;
      }
    }

    // Checking if there are two turbines in the same position (x, y)
    for(int i = 0; i < solution.turbines[zone].size(); i++){
      for(int j = 0; j < solution.turbines[zone].size(); j++){
        if(i != j){
          if(solution.turbines[zone][i].index == solution.turbines[zone][j].index){
              cout << solution.turbines[zone][i].id << " " << solution.turbines[zone][j].id  << " " << solution.turbines[zone][i].x << " " << solution.turbines[zone][j].x << " " <<
              solution.turbines[zone][i].y << " " << solution.turbines[zone][j].y << endl;
              cout << solution.turbines[zone][i].index << " " << solution.turbines[zone][j].index << endl;
              cout << "Two turbines in same position" << endl;
            return false;
          }
        }
      }
    }

    //Cheking if the index of each turbine in foundations corresponds to its position (x,y)

    for(int i = 0; i < solution.turbines[zone].size(); i++){
      if(!(foundations[zone][solution.turbines[zone][i].index].x == solution.turbines[zone][i].x) ||
         !(foundations[zone][solution.turbines[zone][i].index].y == solution.turbines[zone][i].y)
      ) {
        cout << "Index in right position" << endl;
        return false;
      }
    }

  }

  return true;
}