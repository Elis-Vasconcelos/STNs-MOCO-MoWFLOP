import shapely, random
import matplotlib.pyplot as plt
import math

def polygon_order(point : tuple):
    return math.atan2(point[1], point[0])

def gen_polygon(num_vertex) -> shapely.Polygon:    
    points = []
    
    index_leastX = 0
    
    for i in range(num_vertex):
        x = random.uniform(100000.0, 150000.0)
        y = random.uniform(100000.0, 150000.0)
        
        points.append(tuple([x, y]))
        
        if points[index_leastX][0] > x:
            index_leastX = i
    
    points[0], points[index_leastX] = points[index_leastX], points[0]
    
    rest_points = points[1:]
    rest_points.sort(key=lambda x: math.atan2(x[1] - points[0][1], x[0] - points[0][0]))
    
    points = [points[0]] + rest_points
    
    polygon = shapely.Polygon(points)
    
    return polygon

def scale(polygon: shapely.Polygon, scale_factor: float):
    pointsX, pointsY = polygon.exterior.coords.xy
    
    pointsX = [x * scale_factor for x in pointsX]
    pointsY = [x * scale_factor for x in pointsY]
    
    resized_poly = shapely.Polygon([pointsX[i], pointsY[i]] for i in range(len(pointsX)))
    
    paceX = polygon.centroid.x - resized_poly.centroid.x
    paceY = polygon.centroid.y - resized_poly.centroid.y
    
    pointsX = [x + paceX for x in pointsX]
    pointsY = [x + paceY for x in pointsY]
    
    resized_poly = shapely.Polygon([pointsX[i], pointsY[i]] for i in range(len(pointsX)))
    
    return resized_poly

def translate(polygon: shapely.Polygon, pacex: float, pacey: float):
    pointsX, pointsY = polygon.exterior.coords.xy
    
    pointsX = [x + pacex for x in pointsX]
    pointsY = [y + pacey for y in pointsY]
    
    translated_poly = shapely.Polygon([pointsX[i], pointsY[i]] for i in range(len(pointsX)))
    
    return translated_poly
    

def gen_layout(num_zones) -> list[shapely.Polygon]:
    polygons : list[shapely.Polygon] = []
    area = 0

    for i in range(num_zones):
        polygons.append(scale(gen_polygon(random.randint(3, 9)), random.uniform(0.3, 1)))
        
        while polygons[i].area / 1000000 > 550:
            polygons[i] = scale(polygons[i], 0.95)
        
        while polygons[i].area / 1000000 < 20:
            polygons[i] = scale(polygons[i], 1.05)
            
        area += polygons[i].area / (1000000)
    
    rand_int = random.randint(0, len(polygons) - 1)
    while(area > 1500):    
        area -= polygons[rand_int].area / 1000000
        
        polygons[rand_int] = scale(polygons[rand_int], 0.9)
        area += polygons[rand_int].area / (1000000)
    
    while(area < 100):
        area -= polygons[rand_int].area / 1000000
        
        polygons[rand_int] = scale(polygons[rand_int], 1.1)
        area += polygons[rand_int].area / (1000000)
                
        
    return polygons

def re_position(polygonA: shapely.Polygon, polygonB: shapely.Polygon):
    minx1, miny1, maxx1, maxy1 = polygonA.bounds
    minx2, miny2, maxx2, maxy2 = polygonB.bounds
    
    mode = random.randint(0, 1)
    side = random.randint(0, 3)
    
    if mode == 0:
        if side == 0:
            pacex = maxx1 - minx2
            polygonB = translate(polygonB, pacex, 0.0)
        elif side == 1:
            pacey = maxy1 - miny2
            polygonB = translate(polygonB, 0.0, pacey)
        elif side == 2:
            pacex = minx1 - maxx2
            polygonB = translate(polygonB, pacex, 0.0)
        else:
            pacey = miny1 - maxy2
            polygonB = translate(polygonB, 0.0, pacey)
    else:
        if side == 0:
            pacex = maxx2 - minx1
            polygonA = translate(polygonA, pacex, 0.0)
        elif side == 1:
            pacey = maxy2 - miny1
            polygonA = translate(polygonA, 0.0, pacey)
        elif side == 2:
            pacex = minx2 - maxx1
            polygonA = translate(polygonA, pacex, 0.0)
        else:
            pacey = miny2 - maxy1
            polygonA = translate(polygonA, 0.0, pacey)
    
    return polygonA, polygonB

def hasIntersections(polygons: list[shapely.Polygon]):
    
    if len(polygons) == 1:
        return False
    
    result = [False] * len(polygons)
    
    for i in range(len(polygons)):
        result[i] = polygons[i].intersects(polygons[(i + 1) % len(polygons)])
    
    return any(result)

def gen_complete_layout() -> None:
    polygons = gen_layout(random.randint(1, 3))

    while hasIntersections(polygons):    
        for i in range(len(polygons)):
            if(polygons[i].intersects(polygons[(i+1) % len(polygons)])):
                polygons[i], polygons[(i+1) % len(polygons)] = re_position(polygons[i], polygons[(i+1) % len(polygons)])

    f = open("geometry.txt", "w")

    for i in range(len(polygons)):
        xe, ye = polygons[i].exterior.xy
        
        for j in range(len(xe)):
            line = f"{xe[j]:11f} {ye[j]:11f} \n"
            f.write(line)
        f.write("\n")
        
    f.close()
    


        