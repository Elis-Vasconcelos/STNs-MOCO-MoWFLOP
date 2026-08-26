#ifndef PARETOSET_CPP
#define PARETOSET_CPP

#include <list>
#include <map>
#include <math.h>
#include <cstdio>
#include <iomanip>
#include <fstream>
#include <iostream>

#include "../../headers/adaptative_grid/param.h"
#include "../../headers/adaptative_grid/Grid.h"
#include "../../headers/global_modules/generate_initial_population/generate_rSolution.h"
#include "../../headers/adaptative_grid/ParetoSet.h"

using namespace std;

double getObj(Solution *s, int obj){
    if(obj == 0){
        return s->fitness.first;
    }

    return s->fitness.second;
}

bool dominatesP(Solution &s1, Solution &s2){
    return (s1.fitness.first >= s2.fitness.first && s1.fitness.second >= s2.fitness.second) &&
           (s1.fitness.first >  s2.fitness.first || s2.fitness.second >  s2.fitness.second);
}

bool equals(Solution &s1, Solution &s2){
    return s1.fitness.first == s2.fitness.first && s1.fitness.second == s2.fitness.second;
}

void printSolution(FILE* f, Solution *s){
    fprintf(f, "(%.10lf, %.10lf)\n", s->fitness.first, s->fitness.second);
}

void printLayout(ofstream & file, Solution *s){
    for (int i = 0; i < s->turbines.size(); i++){
        for(int j = 0; j < s->turbines[i].size(); j++){
            file << s->turbines[i][j].x << " " << s->turbines[i][j].y << endl;
        }
    }
    file << "\n";
}

int ParetoSet::calculateGridPos(Solution &s) {
    int bit = 0;
    int gridPos = 0;
    for (int obj = 0; obj < NUMOBJECTIVES; obj++) {
        double begin = rangeActual[obj].min, end = rangeActual[obj].max, mid = (begin + end) / 2.0;
        for (int k = 0; k < GRIDDEPTH; k++) {
            if (getObj(&s, obj) >= mid) {
                gridPos |= (1 << bit);
                begin = mid;
            } else {
                end = mid;
            }
            mid = (begin + end) / 2.0;
            bit++;
        }
    }
    return gridPos;
}

void ParetoSet::updateGrid() {
    g.clearGrid();

    list<Solution *>::iterator it = sol.begin();
    restartRanges();
    while (it != sol.end()) {
        for (int k = 0; k < NUMOBJECTIVES; k++) {
            rangeActual[k].min = rangeNew[k].min = min(rangeActual[k].min, getObj(*it, k));
            rangeActual[k].max = rangeNew[k].max = max(rangeActual[k].max, getObj(*it, k));
        }
        it++;
    }

    it = sol.begin();
    while (it != sol.end()) {
        g.addGrid(calculateGridPos(**it));
        it++;
    }
}

void ParetoSet::restartRanges() {
    #define INF 1e9
    for (int k = 0; k < NUMOBJECTIVES; k++) {
        rangeActual[k].min = rangeNew[k].min = INF;
        rangeActual[k].max = rangeNew[k].max = -INF;
    }
    #undef INF
}

ParetoSet::ParetoSet() {
    restartRanges();
    memset(freq, 0, sizeof(freq));
}

ParetoSet::~ParetoSet() {
    clear();
}

int ParetoSet::getPositionCount(Solution &s) {
    return g.getPositionCount(calculateGridPos(s));
}

int ParetoSet::getPositionCount(int p) {
    return g.getPositionCount(p);
}

list<Solution *> ParetoSet::getElements() {
    return sol;
}

bool ParetoSet::addSol(Solution *s) {
    ASS ( assert( checkGrid() ); )
    list<Solution *>::iterator i = sol.begin();
    list<list<Solution *>::iterator> toRemove;
    while (i != sol.end()) {
        if (dominatesP(*s, **i)) {
            toRemove.push_back(i);
        }
        if (dominatesP(**i, *s) || equals(**i, *s)) {
            return false;
        }
        i++;
    }

    list<list<Solution *>::iterator>::iterator j = toRemove.begin();
    while (j != toRemove.end()) {
        g.removeGrid(calculateGridPos(***j));

        delete (**j);
        sol.erase(*j);
        j++;
    }

    Solution *t = new Solution;
    *t = *s;
    sol.push_front(t);
    g.addGrid(calculateGridPos(*t));

    for (int k = 0; k < NUMOBJECTIVES; k++) {
        rangeNew[k].min = min(rangeNew[k].min, getObj(t, k));
        rangeNew[k].max = max(rangeNew[k].max, getObj(t, k));
    }

    for (int k = 0; k < NUMOBJECTIVES; k++) {
        if (fabs(rangeNew[k].min - rangeActual[k].min) > 0.1 * rangeActual[k].min ||
            fabs(rangeNew[k].max - rangeActual[k].max) > 0.1 * rangeActual[k].max) {
            updateGrid();
            break;
        }
    }

    ASS ( assert( checkGrid() ); )
    return true;
}

void ParetoSet::printAllSolutions(string path) {
    ofstream file(path);

    file << fixed << setprecision(10);

    if (file.is_open()) {
        list<Solution *>::iterator i = sol.begin();
        Solution *s;
        while (i != sol.end()) {
            s = *i;
            file << abs(s->fitness.first) << " " << s->fitness.second << endl;
            i++;
        }
        file.close();
    } else {
        cerr << "ERROR! ParetoSet.cpp -> Error opening file for writing: " << path << endl;
    }
}

void ParetoSet::printAllSolutionsLayout(string path) {
    ofstream file(path);

    file << fixed << setprecision(10);

    if (file.is_open()) {
        list<Solution *>::iterator i = sol.begin();
        Solution *s;
        while (i != sol.end()) {
            s = *i;
            printLayout(file, s);
            i++;
        }
        file.close();
    } else {
        cerr << "ERROR! ParetoSet.cpp -> Error opening file for writing: " << path << endl;
    }
}


int ParetoSet::getSize() {
    return sol.size();
}

Solution *ParetoSet::getSolution(int p) {
    int c = 0;
    list<Solution *>::iterator i = sol.begin();
    while (i != sol.end()) {
        if (c == p) return *i;
        i++;
        c++;
    }
    return NULL;
}

void ParetoSet::clear() {
    list<Solution *>::iterator i = sol.begin(), j;
    while (i != sol.end()) {
        j = i;
        i++;
        delete (*j);
    }
    sol.clear();
    g.clearGrid();
}

bool ParetoSet::checkGrid() {
    unsigned s = 0;
    for (int i = 0; i < g.getSize(); i++) s += g.getPositionCount(i);
    return s == sol.size();
}


#endif