# Meta-Learning-Based Algorithm Selection for Multi-Objective Wind Farm Layout Optimization

This repository contains the implementation, datasets and experimental outputs for a multi-objective wind farm layout optimization study. The project compares several multi-objective algorithms on the wind farm layout problem and builds meta-learning models that characterize and predict algorithm performance across instances.

## 📄 Abstract

Wind farm layout optimization involves multiple conflicting objectives and highly irregular search landscapes, making the selection of suitable multi-objective metaheuristics a challenging task. Although meta-learning has been successfully employed to select metaheuristics for single-objective optimization, its application to real-world multi-objective engineering problems remains unexplored. This paper proposes a meta-learning approach for automatically selecting metaheuristics for the Multi-Objective Wind Farm Layout Optimization Problem (MoWFLOP). The proposed approach uses fitness landscape meta-features to predict the performance of multi-objective state-of-the-art metaheuristics under different quality indicators. We evaluate 90 datasets with different sampling configurations from 516 real-world wind farms. The analyses comprised the results of the metaheuristics, the impact of sampling configurations, and the meta-learning performance for metaheuristic selection. Results show that the meta-learning approach surpassed the baseline of selecting the same algorithm for all instances.

## 📂 Repository Structure
```
├── algorithms_raw_results/  # Raw outputs from multi-objective algorithms (COMOLSD, MOEAD, NSGA2, ...)
├── metafeatures_raw/        # Extracted meta-features for each instance (many numbered instance folders)
├── regression_metrics/      # Metrics, processed CSVs, and model outputs for regression analyses
├── metadataset_final/       # Final meta-dataset: 90 datasets (one per walk-parameter configuration)
├── correlation_matrix/      # Correlation analyses and visualizations between features and metrics
├── gap_spearman_tables/     # Tables with gap and Spearman correlation values for each feature and walk configuration
└── source_code/             # Code that produced the results presented in the paper
```

## 👥 Authors

| Name | Affiliation | Contact |
|------|-------------|---------| 
|Gustavo J. N. Silva | Federal University of Bahia, Institute of Computing | gustavojorge080@gmail.com |
|João G. Lofiego | Federal University of Bahia, Institute of Computing | joao.lofiego@ufba.br|
|Islame F. C. Fernandes | Federal University of Bahia, Institute of Computing | islame.felipe@ufba.br|

## 📧 Contact

- For questions, contact the lead authors: gustavojorge080@gmail.com and joao.lofiego@ufba.br.
