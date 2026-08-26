#include <vector>
#include <cstdlib>
#include "../../../../headers/wind_farm_entities/turbine.h"
#include "../../../../headers/global_modules/generate_initial_population/generate_rSolution.h"
#include <time.h>
#include <cmath>
#include <iostream>
using namespace std;

const double PI = 3.14159265358979323846;

// References:
// [1] - Multi-objective genetic algorithm based innovative wind farm layout optimization method | By Ying Chen, Hua Li, Bang He, Pengcheng Wang, Kai Jin
// [2] - Multi-objective optimization of wind farm layouts – Complexity, constraint handling and scalability | By S. Rodrigues, P. Bauer, Peter A.N. Bosman


// Power produced by a turbine according to [1]
// 0.6127 = 0.5 * 1.2254
float power_produced(double& wind, Turbine& turbine){
    return 0.6127 * turbine.power * (wind * wind * wind);
}

// Power produced by a turbine according to [1]
float power_alt(float& wind, float& power, float& tc){
    return 0.6127 * power * (wind * wind * wind);
}

double calculate_cost(Solution& sol){
    double acc = 0;

    for(int z = 0; z < num_zones; z++){
        for(int i = 0; i < sol.turbines[z].size(); i++){
            acc += foundations[sol.turbines[z][i].zone][sol.turbines[z][i].index].cost;
        }
    }

    if(acc > 0){
        acc = acc * (-1);
    }

    sol.fitness.first = acc;

    return acc;
}

double calculate_interference(Turbine& t_initial, Turbine& t_interfered){

    if(t_initial.id == t_interfered.id){
        return 0;
    }
    
    double toRadians = angle * PI / 180.0;

    float xWind = cos(toRadians);
    float yWind = sin(toRadians);


    float xVector = t_interfered.x - t_initial.x;
    float yVector = t_interfered.y - t_initial.y;

    float scalar = (xVector * xWind + yVector * yWind) / (xWind * xWind + yWind * yWind);

    if(scalar <= 0){
        return 0;
    }

    // Wake decay coefficient according to [2]
    double alpha = 0.5 / log(t_initial.height / 0.0005);

    float xWake = t_initial.x + scalar * xWind;
    float yWake = t_initial.y + scalar * yWind;

    float wakeDistance = sqrt((xWake - t_initial.x) * (xWake - t_initial.x) + (yWake - t_initial.y) * (yWake - t_initial.y));
    float distBtwnCenter = sqrt((xWake - t_interfered.x) * (xWake - t_interfered.x) + (yWake - t_interfered.y) * (yWake - t_interfered.y));

    float wakeDiameter = t_initial.diameter + alpha * wakeDistance;

    if((wakeDiameter + t_interfered.diameter)/2 <= distBtwnCenter){
        return 0;
    }

    double distBtwnturbs = sqrt((xVector * xVector) + (yVector * yVector));

    // Interference that t_initial caused on t_interfered according to [2]
    double result = (1 - sqrt(1 - t_initial.thrust_coef)) / pow(1 + alpha * distBtwnturbs / (t_interfered.diameter * 0.5), 2);

    return result;
}

double calculate_power(Solution& sol){
    double power = 0;
    double deficit, windResulted, result;

    for(int z = 0; z < num_zones; z++){
        for(int i = 0; i < sol.turbines[z].size(); i++){
            deficit = 0;

            for(int j = 0; j < num_zones; j++){
                for(int k = 0; k < sol.turbines[j].size(); k++){
                    result = calculate_interference(sol.turbines[j][k], sol.turbines[z][i]);
                    deficit += result * result;
                }
            }

            for(int a = 0; a < fixd.size(); a++){
                result = calculate_interference(fixd[a], sol.turbines[z][i]);
                deficit += result * result;
            }

            // Wind resulted according to [2]
            windResulted = wind * (1 - min(sqrt(deficit), 1.0));


            power += power_produced(windResulted, sol.turbines[z][i]);
        }
    }

    for (int i = 0; i < fixd.size(); i++){
        deficit = 0.0;

        for(int j = 0; j < fixd.size(); j++){
            result = calculate_interference(fixd[j], fixd[i]);
            deficit += result * result;
        }

        for(int j = 0; j < num_zones; j++){
            for(int k = 0; k < turbines_per_zone[j]; k++){
                result = calculate_interference(sol.turbines[j][k], fixd[i]);
                deficit += result * result;
            }
        }

        // Wind resulted according to [2]
        windResulted = wind * (1 - sqrt(deficit));

        power += power_produced(windResulted, fixd[i]);
    }

    sol.fitness.second = power;
    return power;
}

Solution generate_solution(){
    id = fixd.size();

    vector<vector<int>> pos(num_zones);
    
    for(int i = 0; i < num_zones; i++){
        pos[i].resize(foundations[i].size());
    }

    vector<vector<Turbine>> turbines(num_zones);
    
    for(int i = 0; i < num_zones; i++){
        turbines[i].resize(turbines_per_zone[i]);
    }

    Turbine t;


    for(int z = 0; z < num_zones; z++){
        for (int i = 0; i < pos[z].size(); i++){
            pos[z][i] = i;
        }
    }


    vector<vector<int>> solution_grid(num_zones);

    for(int i = 0; i < num_zones; i++){
        solution_grid[i].resize(foundations[i].size());
    }

    int rand_int;
    int elmn;

    t.diameter = 240;
    t.height = 150;

    for(int z = 0; z < num_zones; z++){
        for(int i = 0; i < turbines_per_zone[z]; i++){
            rand_int = rand() % pos[z].size();

            elmn = pos[z][rand_int];

            t.id = id;
            solution_grid[z][elmn] = t.id;
            t.index = elmn;
            t.x = foundations[z][elmn].x;
            t.y = foundations[z][elmn].y;
            t.power = power;
            t.thrust_coef = thrust_coef;
            t.zone = z;
            turbines[z][i] = t;
            // cout << t.id << " " << t.x << " " << t.y << endl;

            pos[z].erase(pos[z].begin() + rand_int);

            id++;
        }
    }

    //Filling the Solution

    Solution rSolution;
    
    rSolution.grid = solution_grid;
    rSolution.turbines = turbines;

    rSolution.fitness.first = calculate_cost(rSolution);
    rSolution.fitness.second = calculate_power(rSolution);

    return rSolution;
}