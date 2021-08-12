from enum import Enum
from itertools import product


class TileType(Enum):

  FLOOR = ('.', True)
  WALL = ('#', False)
  INITIAL_POINT = ('I', True)
  EXTRACTION_ZONE = ('E', True)
  PACKAGE_POINT = ('P', True)

  def __init__(self, symbol: str, walkable: bool) -> None:
      super().__init__()
      self.symbol = symbol
      self.walkable = walkable


def pointsInSize(size: tuple) -> tuple:
  sizeRanges = tuple(map(range, reversed(size)))
  coordinatesIteration = map(reversed, product(*sizeRanges))
  yield from map(tuple, coordinatesIteration)


class GridMap:

  def fromMapFile(mapFilePath: str):
    symbolToTileDict = { t.symbol: t for t in TileType }
    tiles = []
    width = 0
    height = 0
    with open(mapFilePath, 'rt') as mapFile:
      for line in mapFile:
        line = line.rstrip().upper()
        width = max(width, len(line))
        height += 1
        tiles.extend([symbolToTileDict[s] for s in line])
    return GridMap(tiles, (width, height))

  def __init__(self, tiles: list, size: tuple) -> None:
    self.startingPoint = None
    self.extractionArea = []
    self.packageStartingPoint = None
    self.size = size
    self.walkabilityMap = {}
    for (tile, point) in zip(tiles, pointsInSize(self.size)):
      self.walkabilityMap[point] = tile.walkable
      if tile is TileType.INITIAL_POINT:
        self.startingPoint = point
      elif tile is TileType.EXTRACTION_ZONE:
        self.extractionArea.append(point)
      elif tile is TileType.PACKAGE_POINT:
        self.packageStartingPoint = point

  def isPointWithinExtractionArea(self, point: tuple) -> bool:
    return point in self.extractionArea

  def isPointReachable(self, point: tuple) -> bool:
    return point in self.walkabilityMap and self.walkabilityMap[point]


class MoveableObject:

  def __init__(self, referencePoint: tuple) -> None:
    self.referencePoint = referencePoint

  def move(self, vector: tuple) -> None:
    self.referencePoint = tuple(map(sum, zip(self.referencePoint, vector)))
