#include <iostream>
#include <fstream>
#include <vector>
#include <iomanip>

#include "../../headers/utils/features_csv.h"

using namespace std;

void build_csv(const vector<double> &mo_features, const vector<string> &column_names, 
               const string &rootfolder, const string &folder, 
               const string &subfolder, const string &subsubfolder, const string &filename) {
    
    string separator = "\\"; //for windows
    string full_path = rootfolder + separator + folder + separator + subfolder + separator + subsubfolder;
    string file_path = full_path + separator + filename;

    ofstream file(file_path);

    if (file.is_open()) {
        for (size_t i = 0; i < column_names.size(); ++i) {
            file << column_names[i];
            if (i != column_names.size() - 1) {
                file << ",";
            }
        }
        file << "\n";

        file << fixed << setprecision(10);
        for (size_t i = 0; i < mo_features.size(); ++i) {
            file << mo_features[i];
            if (i != mo_features.size() - 1) {
                file << ",";
            }
        }
        file << "\n";

        file.close();
        cout << "CSV file created with success in: " << file_path << endl;
    } else {
        cerr << "Error opening the file for writing: " << file_path << endl;
    }
}
