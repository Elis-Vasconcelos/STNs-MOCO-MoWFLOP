#ifndef FEATURES_CSV_H
#define FEATURES_CSV_H

#include <vector>
#include <string>

void build_csv(const std::vector<double> &mo_features, const std::vector<string> &column_names, 
               const string &filename, const string &rootfolder, const string &folder, 
               const string &subfolder, const string &subsubfolder);
#endif 
