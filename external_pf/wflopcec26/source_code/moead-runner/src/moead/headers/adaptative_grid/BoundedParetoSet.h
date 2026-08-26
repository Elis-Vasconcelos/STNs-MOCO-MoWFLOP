#ifndef BOUNDEDPARETOSET_H
#define BOUNDEDPARETOSET_H

#include "../global_modules/generate_initial_population/generate_rSolution.h"
#include "ParetoSet.h"
#include <list>
#include <cstdio>
#include <string>
#include <cmath>
#include <algorithm>

class BoundedParetoSet : public ParetoSet {
    private:
        static const int MAXARCSIZE = 300;

    public:
        BoundedParetoSet();
        ~BoundedParetoSet();

        bool addSol(Solution *s);
};

#endif
