#ifndef FEATURES_CSV_H
#define FEATURES_CSV_H

#include <vector>
#include <string>

void build_csv(const std::vector<double> &mo_features, const std::vector<std::string> &column_names, 
               const std::string &rootfolder, const std::string &instance, const std::string &folder, 
               const std::string &subfolder, const std::string &subsubfolder, const std::string &filename);

#endif 
