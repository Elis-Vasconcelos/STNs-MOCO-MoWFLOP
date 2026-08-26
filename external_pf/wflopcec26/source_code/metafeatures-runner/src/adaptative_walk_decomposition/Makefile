# Variáveis de compilação
CXX = g++
CXXFLAGS = -std=c++17 -Werror -O2 \
    -I./headers \
    -I./headers/utils \
    -I./headers/metafeatures \
    -I./headers/metaheuristics/genetic_operators/mutation \
    -I./headers/metaheuristics/decomposition_based \
    -I./headers/metaheuristics/pareto_based \
    -I./headers/metaheuristics/walks

# Diretórios
SRC_DIR = src
HEADER_DIR = headers
UTILS_DIR = utils
META_DIR = metaheuristics/modules/genetic_operators/mutation
RSOLUTION_DIR = modules/generate_initial_population/generate_random_solution/
POPULATION_DIR = modules/generate_initial_population/generate_population/

# Arquivos de origem
SRC_FILES = \
    $(SRC_DIR)/decomposition_based/get_global_z_point.cpp \
    $(SRC_DIR)/decomposition_based/get_neighborhood.cpp \
    $(SRC_DIR)/decomposition_based/mo_features_decomposition.cpp \
    $(SRC_DIR)/decomposition_based/tchebycheff_metafeatures.cpp \
    $(SRC_DIR)/decomposition_based/weight_vectors_metafeatures.cpp \
    $(SRC_DIR)/pareto_based/mo_features_pareto.cpp \
    $(SRC_DIR)/walks/adaptative_walk_decomposition.cpp \
    $(SRC_DIR)/metrics_extraction.cpp \
    $(SRC_DIR)/normalization.cpp \
    $(SRC_DIR)/statistical_functions.cpp \
    instance_info.cpp \
    $(UTILS_DIR)/features_csv.cpp \
    $(UTILS_DIR)/isEqual.cpp \
    $(META_DIR)/mutationFeature.cpp \
    $(RSOLUTION_DIR)/generate_rSolution.cpp \
    $(POPULATION_DIR)/population.cpp

# Arquivo principal
MAIN_FILE = main.cpp

# Arquivo de saída
OUTPUT = adaptative_walk_decomposition

# Regra para compilar
$(OUTPUT): $(SRC_FILES) $(MAIN_FILE)
	@echo Starting compilation of adaptative_walk_decomposition...
	@$(CXX) $(CXXFLAGS) -o $(OUTPUT) $(MAIN_FILE) $(SRC_FILES)
	@echo Compilation completed.

# Limpeza dos arquivos gerados
clean:
	@echo "Cleaning generated files..."
	@rm -f $(OUTPUT)
	@echo "Clean completed."

# Recompilar tudo
rebuild: clean $(OUTPUT)
	@echo "Rebuild completed."
