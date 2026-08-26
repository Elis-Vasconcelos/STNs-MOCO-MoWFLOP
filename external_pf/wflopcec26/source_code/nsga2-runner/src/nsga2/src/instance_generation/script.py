import matplotlib.pyplot as plt
import shapely
import random
from perlin_noise import PerlinNoise
import shapely.plotting
from gen_layout import gen_complete_layout
import os, sys

def cost(depth: float) -> float:
    return 659933.9999999129 + depth * -72606.60000000268

def gen_hole(polygon: shapely.Polygon):
    new_hole = []
    hole_max =  random.uniform(polygon.length / 50, polygon.length / 25)
    
    for i in range(random.randint(3, 7)):
        new_hole.append(tuple([random.uniform(0.0, hole_max), random.uniform(0.0, hole_max)]))
    
    new_hole = shapely.Polygon(new_hole)
    
    new_hole = shapely.Polygon(new_hole.convex_hull)
    
    minx, miny, maxx, maxy = polygon.bounds

    point = shapely.Point(0, 0)
    
    while(not polygon.contains(point)):
        point = shapely.Point([random.uniform(minx, maxx), random.uniform(miny, maxy)])
    
    distance = point - new_hole.centroid
    
    coords = new_hole.exterior.coords[:]
    
    for i in range(len(coords)):
        coords[i] = (coords[i][0] + distance.x, coords[i][1] + distance.y)
    
    new_hole = shapely.Polygon(coords)
    
    return polygon.difference(new_hole)
    
def gen_holes(polygon: shapely.Polygon, qtty):

    for i in range(qtty):
        copy = polygon
        
        while(copy.equals(polygon)):
            copy = polygon
            copy = gen_hole(copy)
            
        while(copy.geom_type == "MultiPolygon" or copy.equals(polygon)):
            copy = polygon
            copy = gen_hole(copy)
        
        polygon = copy
    
    return polygon

def gen_structure(polygon: shapely.Polygon):
    minx, miny, maxx, maxy = polygon.bounds
    
    pointIn = shapely.Point([random.uniform(minx, maxx), random.uniform(miny, maxy)])
    
    while(not polygon.contains(pointIn)):
        pointIn = shapely.Point([random.uniform(minx, maxx), random.uniform(miny, maxy)])
        
    pointOut = shapely.Point([random.uniform(100000.0, 150000.0), random.uniform(100000.0, 150000.0)])
    
    while(polygon.contains(pointOut)):
        pointOut = shapely.Point([random.uniform(minx, maxx), random.uniform(miny, maxy)])
        
    
    dist = random.uniform(polygon.length / 300, polygon.length / 200)
    
    line = shapely.LineString([pointIn, pointOut])
    
    left = [shapely.Point(c) for c in line.parallel_offset(dist/2, "left").coords]
    right = [shapely.Point(p) for p in line.parallel_offset(dist/2, "right").coords]
    
    structure = shapely.Polygon(left + right).convex_hull
            
    return polygon.difference(structure)

def gen_structures(polygon: shapely.Polygon, qtty):
    for i in range(qtty):
        copy = polygon
        
        copy = gen_structure(copy)
            
        while(copy.geom_type == "MultiPolygon"):
            copy = polygon
            copy = gen_structure(copy)
        
        polygon = copy
    
    return polygon

def gen_points(polygon: shapely.Polygon, octaves: int):
    minx, miny, maxx, maxy = polygon.bounds
    
    sizex = (maxx - minx)
    sizey = (maxy - miny)
    
    valuex = round(sizex / 160)
    valuey = round(sizey / 160)
    
    noise = PerlinNoise(octaves=octaves)
    pic = [[noise([i/valuex, j/valuey]) for j in range(valuex)] for i in range(valuey)]
    
    cellx = sizex / valuex
    celly = sizey / valuey
    
    allPoints = []
    depths = []
    
    for i in range(valuey):
        centroidY = (maxy - (i * celly) + maxy - ((i + 1) * celly)) / 2 
        for j in range(valuex):
            centroidX = (minx + (j * cellx) + minx + ((j + 1) * cellx)) / 2
            
            if(polygon.contains(shapely.Point(centroidX, centroidY))):
                allPoints.append([centroidX, centroidY])
                depths.append(-25.0 + pic[i][j] * 15.0)
        
    return allPoints, depths

def create_grid(num_points : int) -> tuple[int, int]:
    factors = [(i, num_points // i) for i in range(1, int(num_points ** 0.5) + 1) if i > 1]
    
    factors += [(factor[1], factor[0]) for factor in reversed(factors)]
        
    return factors[random.randint(0, len(factors) - 1)]

def gen_grid(vec: list[float, float], rows: int, cols: int, dist : float, base: shapely.LineString):
    tVec = dist / (vec[0] ** 2 + vec[1] ** 2) ** 0.5
    vec = [vec[0] * tVec, vec[1] * tVec]
    
    perpVec = [vec[1], - vec[0]]
    
    points = []
    
    jumps = cols - 1
    
    limit = base.length - jumps * dist if base.length - jumps * dist > 0 else 0
    
    initial_point = base.interpolate(random.uniform(0, limit))
    
    for i in range(cols):
        for j in range(1, rows + 1):
            points.append([initial_point.x + vec[0] * i + perpVec[0] * j, initial_point.y + vec[1] * i + perpVec[1] * j])
    
    return points

def gen_fixed(polygons: list[shapely.Polygon], num_fixed: int):
    
    grid_sizes = create_grid(num_fixed)
    
    zone = random.randint(0, len(polygons) - 1)
        
    dist = random.uniform(200, 500)
    
    polyX, polyY = polygons[zone].exterior.xy
    
    polyX = polyX[:-1]
    polyY = polyY[:-1]
    
    rlNum = random.randint(0, len(polyX) - 1)
        
    vector = [polyX[(rlNum + 1) % len(polyX)] - polyX[rlNum], polyY[(rlNum + 1) % len(polyY)] - polyY[rlNum]]
    
    randomLine = shapely.LineString([[polyX[rlNum], polyY[rlNum]], [polyX[(rlNum + 1) % len(polyX)], polyY[(rlNum + 1) % len(polyY)]]])
    
    points = gen_grid(vector, grid_sizes[1], grid_sizes[0], 1440, randomLine)
    
    return points

os.chdir("../instances")

if len(os.listdir()) != 0:
    dirName = str(int(os.listdir()[len(os.listdir()) - 1]) + 1)
else:
    dirName = "0"

if len(sys.argv) > 1:
    dirName = sys.argv[1]
    
os.mkdir(dirName)

os.chdir(dirName)

gen_complete_layout()

lines_to_write = []

polygons = []
points = []
polygonsDensity = []

f = open("geometry.txt", 'r')

for line in f.readlines():
    if len(line.split()) == 2:
        x, y = map(float, line.split())
        points.append(tuple([x, y]))
    if len(line.split()) == 0:
        polygons.append(shapely.Polygon(points))
        points.clear()

f.close()

num_fixed = random.randint(5, 75)

points = gen_fixed(polygons, num_fixed)

while(any([polygons[i].intersects(shapely.MultiPoint(points)) for i in range(len(polygons))])):
    points = gen_fixed(polygons, num_fixed)

f = open("fixed_wf.txt", "w")

for point in points:
    f.write(f"{point[0]:.11f} {point[1]:.11f} 0.0 {len(polygons) + 1}\n")
    plt.plot(point[0], point[1], marker="o", color="orange", markersize=1)

f.close()

for i in range(len(polygons)):
    num_structs = random.randint(5, 8)
    num_holes = random.randint(2, 5)
    polygons[i] = gen_holes(polygons[i], num_holes)
    polygons[i] = gen_structures(polygons[i], num_structs - num_holes)
    
octaves = random.randint(3, 7)
for i in range(len(polygons)):
    allPoints, depths = gen_points(polygons[i], octaves + random.randint(-1, 1))
    
    polygonsDensity.append(len(allPoints))
    
    for j in range(len(allPoints)):
        lines_to_write.append(f"{allPoints[j][0]:.11f} {allPoints[j][1]:.11f} {depths[j]:.11f} {cost(depths[j]):.11f} {i + 1}\n")
    
    pointsX, pointsY = zip(*allPoints)
    
    plt.scatter(pointsX, pointsY, 2, c=depths)
    
    xe, ye = polygons[i].exterior.xy
    for inner in polygons[i].interiors:
        xi, yi = zip(*inner.coords[:])
        plt.plot(xi, yi, color="magenta")
    plt.plot(xe, ye, color="magenta")

f = open("availablePositions.txt", "w")

for line in lines_to_write:
    f.write(line)

f.close()

turbines_per_zone = [int(random.uniform(0.005, 0.02) * polygonsDensity[i]) for i in range(len(polygons))]

f = open("turbines_per_zone.txt", "w")

for i in range(len(polygons)):
    f.write(str(turbines_per_zone[i]) + " ")

f.close()

plt.colorbar()
plt.tight_layout()
plt.savefig("plot.png", dpi=195)