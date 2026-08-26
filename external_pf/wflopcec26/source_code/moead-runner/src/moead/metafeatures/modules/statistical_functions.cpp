#include <vector>
#include <iostream>
#include <numeric>
#include <cmath>

#include "../../headers/metafeatures/statistical_functions.h"

using namespace std;

double mean(const vector<double>& values) {
  return accumulate(values.begin(), values.end(), 0.0) / values.size();
}

double sd(const vector<double>& values) {
  double avg = mean(values);
  double sum = 0.0;
  for (double value : values){
    sum += pow(value - avg, 2);
  }
  return sqrt(sum / values.size());
}

double r1(const vector<double>& values) {
  double avg = mean(values);
  double numerator = 0.0, denominator = 0.0;
  for (size_t t = 0; t < values.size() - 1; ++t) {
    numerator += (values[t] - avg) * (values[t + 1] - avg);
    denominator += pow(values[t] - avg, 2);
  }
  return denominator != 0 ? numerator / denominator : 0.0;
}

double kr(const vector<double>& values) {
  double avg = mean(values);
  double stddev = sd(values);
  double sum = 0.0;

  for (double value : values) {
    sum += pow((value - avg) / stddev, 4);
  }
  return sum / values.size();
}

double sk(const vector<double>& values) {
  double avg = mean(values);
  double stddev = sd(values);
  double sum = 0.0;
  for (double value : values) {
    sum += pow((value - avg) / stddev, 3);
  }
  return sum / values.size();
}