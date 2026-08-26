#include "../../headers/adaptative_grid/Grid.h"
#include <cstring>

Grid::Grid() {
    clearGrid();  
}

int Grid::getPositionCount(int p) {
    if (p < 0 || p >= tam) return -1;
    return grid[p];
}

void Grid::addGrid(int p) {
    grid[p]++;
}

void Grid::removeGrid(int p) {
    grid[p]--;
}

void Grid::clearGrid() {
    memset(grid, 0, sizeof(grid[0]) * tam);  
}

int Grid::getSize() {
    return tam;
}
