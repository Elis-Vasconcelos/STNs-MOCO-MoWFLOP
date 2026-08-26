#ifndef BOUNDEDPARETOSET_CPP
#define BOUNDEDPARETOSET_CPP

#include "../../headers/adaptative_grid/BoundedParetoSet.h"
#include "../../headers/global_modules/generate_initial_population/generate_rSolution.h"
#include "../../headers/adaptative_grid/ParetoSet.h"
#include <cstdio>
#include <string>

using namespace std;

BoundedParetoSet::BoundedParetoSet() {}

BoundedParetoSet::~BoundedParetoSet() {}

bool BoundedParetoSet::addSol(Solution *s) {
    ASS ( assert( confereGrid() ); )
    list<Solution *>::iterator mostPopulous = sol.begin();
    int biggestPositionCount = -1;
    if (sol.size() > 0) biggestPositionCount = getPositionCount( **sol.begin() );
    
    list<Solution *>::iterator i = sol.begin();
    list< list<Solution *>::iterator > toRemove;
    while (i != sol.end()) {
        if (dominatesP(*s, **i)) {
            toRemove.push_back(i);
        }
        if (toRemove.size() == 0 && getSize()+1 > MAXARCSIZE) {
            int positionCountActual = getPositionCount(**i);
            if (biggestPositionCount < positionCountActual) {
                biggestPositionCount = positionCountActual;
                mostPopulous = i;
            }
        }
        
        if (dominatesP(**i, *s) || equals(**i, *s))
            return false;
        i++;
    }

    if (toRemove.size() == 0 && getSize()+1 > MAXARCSIZE) {
        toRemove.push_back(mostPopulous);
    }

    //fprintf(stderr,"getSize = %d %d\n",getSize(),sol.size());

    list< list<Solution *>::iterator >::iterator j = toRemove.begin();
    while (j != toRemove.end()) {
        g.removeGrid( calculateGridPos(***j) );
        delete( **j );
        sol.erase( *j );
        j++;
    }

    Solution *t = new Solution;
    *t = *s;
    sol.push_front( t );
    if (sol.size() > MAXARCSIZE) fprintf(stderr,"ERROR!\n");
    g.addGrid( calculateGridPos(*t) );

    for(int k=0;k<NUMOBJECTIVES;k++) {
        rangeNew[k].min = min(rangeNew[k].min, getObj(t, k));
        rangeNew[k].max = max(rangeNew[k].max, getObj(t, k));
    }

    for (int k=0;k<NUMOBJECTIVES;k++) {
        if (fabs(rangeNew[k].min-rangeActual[k].min) > 0.1*rangeActual[k].min || fabs(rangeNew[k].max-rangeActual[k].max) > 0.1*rangeActual[k].max) {
            updateGrid();
            break;
        }
    }

    ASS ( assert( checkGrid() ); )
    return true;
}

#endif
