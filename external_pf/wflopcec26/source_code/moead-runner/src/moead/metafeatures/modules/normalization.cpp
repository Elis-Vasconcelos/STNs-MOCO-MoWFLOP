#include <vector>
#include <iostream>

#include "../../headers/metafeatures/landscapeElement.h"
#include "../../headers/metafeatures/normalization.h"

void normalization(vector<vector<LandscapeElement>>& landscapes, double &max, double &min){

  /*Normalization based in the following formula:
  ^F(x) = (F(x) - min(F(x))) / (max(F(x) - min(F(x))
  Reference: Multi-Objective Landscape Analysis and Feature-based
  Algorithm Selection, by Raphaël Cosson, pag 38 on pdf*/

  for(auto& landscape : landscapes){
    for(auto& element : landscape){
      element.tch_current_solution = (element.tch_current_solution - min) / (max - min);

      for(auto& neighbor : element.tchebycheff_neighbors){
        neighbor = (neighbor - min) / (max - min);
      }
    }
  }

}