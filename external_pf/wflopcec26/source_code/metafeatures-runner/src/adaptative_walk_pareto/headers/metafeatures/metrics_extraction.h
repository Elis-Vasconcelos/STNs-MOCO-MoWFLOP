#ifndef METRICS_EXTRACTION_H
#define METRICS_EXTRACTION_H

#include <vector>
#include "../../modules/headers/generate_rSolution.h"
#include "./landscapeMetrics.h"
#include "./landscapeElement.h"

LandscapeMetrics metric_extraction(vector<LandscapeElement> &landscape);

std::vector<LandscapeMetrics> metrics_extraction(std::vector<std::vector<LandscapeElement>> &landscapes);

#endif 
