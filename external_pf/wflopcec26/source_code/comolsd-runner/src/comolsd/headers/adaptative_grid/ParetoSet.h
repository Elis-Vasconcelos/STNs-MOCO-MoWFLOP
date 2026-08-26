#ifndef PARETOSET_H
#define PARETOSET_H

#include <list>
#include <map>
#include <cmath>
#include <fstream>
#include <string>
#include <cstring>
#include <cstdio>
#include <iomanip>
#include <iostream>
#include "param.h"
#include "Grid.h"
#include "../global_modules/generate_initial_population/generate_rSolution.h"

typedef struct {
    double min, max;
} range;

double getObj(Solution *s, int obj);
bool dominatesP(Solution &s1, Solution &s2);
bool equals(Solution &s1, Solution &s2);
void printSolution(FILE* f, Solution *s);
void printLayout(std::ofstream &file, Solution *s);

class ParetoSet {
    protected:
        std::list<Solution *> sol;
        range rangeNew[2], rangeActual[2];
        int freq[NUMVERTEX][NUMVERTEX];
        Grid g;

        int calculateGridPos(Solution &s);
        void updateGrid();
        void restartRanges();

    public:
        ParetoSet();
        virtual ~ParetoSet();

        int getPositionCount(Solution &s);
        int getPositionCount(int p);
        std::list<Solution *> getElements();
        
        virtual bool addSol(Solution *s);
        void printAllSolutions(std::string path);
        void printAllSolutionsLayout(std::string path);
        int getSize();
        Solution *getSolution(int p);
        void clear();
        bool checkGrid();
};

#endif
