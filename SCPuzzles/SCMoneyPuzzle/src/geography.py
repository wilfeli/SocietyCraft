import random


class Map():
    #dimensions of the game
    TILESIZE = 40
    MAPWIDTH = 32
    MAPHEIGHT = 16



    #tilemap
    DIRT = 0
    GRASS = 1
    WATER = 2
    SAND = 3
    TREE = 4
    ROAD = 5
    CLOUD = 6


    def __init__(self, template):
        #representation of tilemap
        self.tilemap = [[Map.DIRT for w in range(Map.MAPWIDTH)] for h in range(Map.MAPHEIGHT)]
        self.buildings = []

        #map with degree of common
        for rw in range(Map.MAPHEIGHT):
            for cl in range(Map.MAPWIDTH):
                randomNumber = random.randint(0, 15)
                if randomNumber == 0:
                    tile = Map.TREE
                elif randomNumber == 1 or randomNumber == 2:
                    tile = Map.WATER
                elif randomNumber >= 3 and randomNumber <= 7:
                    tile = Map.GRASS
                else:
                    tile = Map.DIRT
                self.tilemap[rw][cl] = tile
                