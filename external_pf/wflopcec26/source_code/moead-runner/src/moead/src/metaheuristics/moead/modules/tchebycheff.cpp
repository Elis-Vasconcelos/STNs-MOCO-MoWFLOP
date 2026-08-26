#include <vector>
#include <cmath>
#include <iostream>
#include <utility>
#include <limits> 
#include "../../../../headers/metaheuristics/moead/modules/tchebycheff.h"

using namespace std;

/* Tchebycheff Function:
Computes the maximum value of lambda_j_i * |f_i(x) - z_i*| for each objective function component, 
given a subproblem x_j, weight lambda_j (vector of weights of the subproblem x_j), and a reference point z_point.*/

double calculate_gte(pair<double, double>& x_j, pair<double, double>& lambda_j, pair<double, double>& z_point){

  // The vector of objective functions f_i(x_j)
  vector<double> f_values = {x_j.first, x_j.second};

  // The vector of lambda values lambda_j_i
  vector<double> lambda_j_values = {lambda_j.first, lambda_j.second};

  // The vector of z* values
  vector<double> z_values = {z_point.first, z_point.second};  

  // Calculate lambda_j_i * |f_i(x) - z_i*| for each i and find the maximum
  double max_value = numeric_limits<double>::lowest();
  for (int i = 0; i < f_values.size(); ++i) {
    double current_value = lambda_j_values[i] * abs(f_values[i] - z_values[i]);
    if (current_value > max_value) {
      max_value = current_value;
    }
  }

  return max_value;
}

/*
int main() {
    pair<double, double> x_j = {0.3, 0.7};          
    pair<double, double> lambda_j = {0.5, 0.5};     
    pair<double, double> z = {0.2, 0.8};            

    double result = calculate_gte(x_j, lambda_j, z);

    cout << result;

    return 0;
}*/