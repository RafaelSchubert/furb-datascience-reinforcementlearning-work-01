from enum import auto, IntEnum
from itertools import product


class TileType(IntEnum):

  FLOOR = auto()
  WALL = auto()
  INITIAL_POINT = auto()
  EXTRACTION_ZONE = auto()
  PACKAGE = auto()


def pointsInSize(size: tuple) -> tuple:
  yield from product(*[range(dimension) for dimension in size])


class GridMap:

  def fromMapFile(mapFilePath: str):
    return GridMap([], (0, 0))

  def __init__(self, tiles: list, size: tuple):
    self.startingPoint = None
    self.extractionArea = []
    self.packageStartingPoint = None
    self.size = size
    self.walkabilityMap = {}
    for (t, p) in zip(tiles, pointsInSize(self.size)):
      self.walkabilityMap[p] = t is not TileType.WALL
      if t is TileType.INITIAL_POINT:
        self.startingPoint = p
      elif t is TileType.EXTRACTION_ZONE:
        self.extractionArea.append(p)
      elif t is TileType.PACKAGE:
        self.packageStartingPoint = p
