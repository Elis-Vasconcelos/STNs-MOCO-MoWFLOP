#ifndef ZG_H
#define ZG_H

//#define DEBUG
#ifdef DEBUG
#define D(x) x
#endif
#ifndef DEBUG
#define D(x)
#endif

//#define ASSERT
#ifdef ASSERT
#define ASS(x) x
#endif
#ifndef ASSERT
#define ASS(x)
#endif

#define f(k,i,j) costs[k][i][j]
#define EPS 1e-9

#define NUMOBJECTIVES 2



#define NUMVERTEX 600

#define NUMEDGES (NUMEVERTEX-1)
#define GRIDDEPTH 5


#endif