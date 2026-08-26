CXX = g++
CXXFLAGS = -std=c++17 -Werror -O2 \
    -I./headers \
    -I./headers/utils \
    -I./headers/metaheuristics \
    -I./headers/metaheuristics/moead \
    -I./headers/metaheuristics/moead/modules \
    -I./headers/metaheuristics/nsga2 \
    -I./headers/metaheuristics/nsga2/modules \
    -I./headers/global_modules \
    -I./headers/global_modules/genetic_operators \
    -I./headers/global_modules/generate_initial_population \
    -I./headers/adaptative_grid \
    -I./headers/wind_farm_entities

SRC_DIR = src
HEADER_DIR = headers
META_DIR = $(SRC_DIR)/global_modules/genetic_operators/mutation
CROSS_DIR = $(SRC_DIR)/global_modules/genetic_operators/crossover
RSOLUTION_DIR = $(SRC_DIR)/global_modules/generate_initial_population/generate_random_solution
POPULATION_DIR = $(SRC_DIR)/global_modules/generate_initial_population/generate_population

SRC_FILES = \
    $(SRC_DIR)/adaptive_grid/ParetoSet.cpp \
    $(SRC_DIR)/adaptive_grid/BoundedParetoSet.cpp \
    $(SRC_DIR)/adaptive_grid/Grid.cpp \
    $(SRC_DIR)/global_modules/dominates.cpp \
    $(SRC_DIR)/global_modules/isEqual.cpp \
    $(POPULATION_DIR)/population.cpp \
    $(RSOLUTION_DIR)/generate_rSolution.cpp \
    $(META_DIR)/mutation.cpp \
    $(CROSS_DIR)/crossover.cpp \
    $(SRC_DIR)/metaheuristics/moead/modules/generate_neighborhood.cpp \
    $(SRC_DIR)/metaheuristics/moead/modules/generate_weight_vectors.cpp \
    $(SRC_DIR)/metaheuristics/moead/modules/get_best_z_point.cpp \
    $(SRC_DIR)/metaheuristics/moead/modules/tchebycheff.cpp \
    $(SRC_DIR)/metaheuristics/moead/modules/updateEP.cpp \
    $(SRC_DIR)/metaheuristics/moead/moead.cpp \
    ${SRC_DIR}/metaheuristics/nsga2/modules/binary_tournament.cpp \
    $(SRC_DIR)/metaheuristics/nsga2/modules/non_dominated_sorting.cpp \
    $(SRC_DIR)/metaheuristics/nsga2/modules/arena_non_dominated_sorting.cpp \
    ${SRC_DIR}/metaheuristics/nsga2/modules/crowding_distance.cpp \
    $(SRC_DIR)/metaheuristics/nsga2/nsga2.cpp \
    instance_info.cpp

MAIN_FILE = main.cpp

OUTPUT = nsga2

$(OUTPUT): $(SRC_FILES) $(MAIN_FILE)
	@echo Starting compilation of $(OUTPUT)...
	@$(CXX) $(CXXFLAGS) -o $(OUTPUT) $(MAIN_FILE) $(SRC_FILES)
	@echo Compilation completed.

clean:
	@echo Cleaning generated files...
	@rm -f $(OUTPUT)
	@echo Clean completed.

rebuild: clean $(OUTPUT)
	@echo Rebuild completed.
