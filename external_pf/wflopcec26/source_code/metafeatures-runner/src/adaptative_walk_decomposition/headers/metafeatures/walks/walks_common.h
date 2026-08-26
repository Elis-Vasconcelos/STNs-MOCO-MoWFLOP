#ifndef WALKS_COMMON_H
#define WALKS_COMMON_H

#include "../landscapeElement.h"
#include "../landscapeMetrics.h"
#include "../decomposition_based/tchebycheff_metafeatures.h"

#include "../../../modules/headers/dominates.h"

extern int iLandscape;

std::pair<double, int> calculate_decomp_metrics(LandscapeElement* element, std::vector<Solution>* neighborhood);

#endif