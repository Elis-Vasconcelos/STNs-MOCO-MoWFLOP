#ifndef TURBINE_H
#define TURBINE_H

using namespace std;

struct Turbine {
    int id;
    int index;
    double x;
    double y;
    float power;
    float thrust_coef;
    int diameter;
    int zone;
    int height;
};

// Wind Turbine Formula = 0.5 * air_density * swept_area * pow_coef * (wind_spd ** 3)
// Considering Air density = 1.225
// 0.5 * air_density = 0.6125 
float power_produced(double& wind, Turbine& turbine);

#endif 