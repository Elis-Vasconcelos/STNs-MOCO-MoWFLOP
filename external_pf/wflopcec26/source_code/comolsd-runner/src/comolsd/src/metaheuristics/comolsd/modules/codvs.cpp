#include "../../../../headers/metaheuristics/comolsd/modules/codvs.h"

using namespace std;

pair<double, double> centroid(vector<Solution>& pop){
    double x = 0;
    double y = 0;

    for(Solution s : pop){
        x += s.fitness.first;
        y += s.fitness.second;
    }

    return make_pair(x / pop.size(), y / pop.size());
}

double euclideanDistance(const pair<double, double>& a, const pair<double, double>& b) {
    return sqrt(pow(a.first - b.first, 2) + pow(a.second - b.second, 2));
}

vector<pair<double, double>> codvs(
    const pair<double, double>& nadir_point,
    const vector<Solution>& population_p,
    const vector<Solution>& population_q,
    int N) {

    int L = N - population_p.size();

    auto C = unionFind(population_p);

    int k = C.size();

    vector<pair<double,double>> U(k);

    // Creating the Centroid vector
    for(int i = 0; i < k; i++){
        U[i] = centroid(C[i]);
    }

    // In case of low amount of clusters, add new ones by getting random solution and putting them as a new centroid
    while ((k * (k - 1) / 2) <= L) {  
        int random_index = rand() % population_p.size();
        U.push_back(population_p[random_index].fitness);
        k++;
    }

    vector<pair<double, double>> V;  // Midpoints
    vector<double> D;                // Distances
    vector<size_t> I;                // Original indices

    // Creating the Midpoint pair vector V, and the Distance pair Vector D 
    for (int i = 0; i < k; i++) {
        for (int j = i + 1; j < k; j++) {
            pair<double, double> midpoint = make_pair(
                (U[i].first + U[j].first) / 2,
                (U[i].second + U[j].second) / 2);
            
            V.push_back(midpoint);
            
            D.push_back(euclideanDistance(U[i], U[j]));
        }
    }

    // Create and sort index array based on distances
    I.resize(D.size());
    for (size_t i = 0; i < I.size(); ++i) I[i] = i;

    // Sort indices based on corresponding distance values
    stable_sort(I.begin(), I.end(), [&D](size_t i1, size_t i2) { return D[i1] < D[i2]; });

    // Getting the L first Midpoints
    vector<pair<double, double>> VL;
    for (int i = 0; i < L; i++) {
        VL.push_back(V[I[i]]);
    }

    // Generate direction vectors
    vector<pair<double, double>> W2;
    for (auto& v : VL) {
        W2.push_back(make_pair(
            nadir_point.first - v.first,
            nadir_point.second - v.second));
    }

    return W2;
}
