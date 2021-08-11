from enum import Enum
from itertools import product


class TileType(Enum):

  FLOOR = ('.', )
  WALL = ('#', )
  INITIAL_POINT = ('I', )
  EXTRACTION_ZONE = ('E', )
  PACKAGE = ('P', )

  def __init__(self, symbol: str) -> None:
      super().__init__()
      self.symbol = symbol


def pointsInSize(size: tuple) -> tuple:
  yield from product(*[range(dimension) for dimension in size])


class GridMap:

  def fromMapFile(mapFilePath: str):
    return GridMap([], (0, 0))

  def __init__(self, tiles: list, size: tuple) -> None:
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
