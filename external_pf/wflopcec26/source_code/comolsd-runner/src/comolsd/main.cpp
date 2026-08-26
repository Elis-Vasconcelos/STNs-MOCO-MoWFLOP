#include "./headers/main.h"
#include "./headers/globals.h"

#include <iostream>
#include <string>
using namespace std;

int countRevalue = 0;

BoundedParetoSet * pareto = new BoundedParetoSet();
int stop_criteria = 1000000;
string algorithm = "comolsd";
string instance = "A";
string root_folder = "./";

int main(int argc, char* argv[]){

    if(argc == 2){
        instance = argv[1];
    } else if (argc > 2){
        instance = argv[1];
        root_folder = argv[2];
    }

    string path;

    int num_neighbors = 10;

    get_instance_info(argc, argv);

    int sum = 0;
    for(auto elem : turbines_per_zone)
        sum += elem;

    cout << endl;
    cout << "Number of subproblems: " << SIZE_OF_POPULATION << endl;
    cout << "Number of neighbors: " << num_neighbors << endl;
    cout << "Number of fixed turbines: " << fixd.size() << endl;
    cout << "Number of mobile turbines: " << sum << endl;
    cout << "Wind: " << wind << endl;
    cout << "Angle: " << angle << endl << endl;

    cout << "Run time:" << endl;
    
    auto population = create_initial_population(SIZE_OF_POPULATION);

    // pareto->printAllSolutions("initial_population.out");
    comolsd(population);
}