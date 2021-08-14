import numpy as np
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
  sizeRanges = list(map(range, reversed(size)))
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
    self.agentStartingPoint = None
    self.extractionArea = []
    self.packageStartingPoint = None
    self.size = size
    self.walkabilityMap = {}
    for (tile, point) in zip(tiles, pointsInSize(self.size)):
      self.walkabilityMap[point] = tile.walkable
      if tile is TileType.INITIAL_POINT:
        self.agentStartingPoint = point
      elif tile is TileType.EXTRACTION_ZONE:
        self.extractionArea.append(point)
      elif tile is TileType.PACKAGE_POINT:
        self.packageStartingPoint = point

  def isPointWithinExtractionArea(self, point: tuple) -> bool:
    return point in self.extractionArea

  def isPointReachable(self, point: tuple) -> bool:
    return point in self.walkabilityMap and self.walkabilityMap[point]


def addPointAndVector(point: tuple, vector: tuple) -> tuple:
  return tuple(map(sum, zip(point, vector)))


def distanceVectorBetweenPoints(destPoint: tuple, startPoint: tuple) -> tuple:
  return tuple(d-s for (d, s) in zip(destPoint, startPoint))


class MoveableObject:

  def __init__(self, referencePoint: tuple) -> None:
    self.referencePoint = referencePoint

  def occupiedArea(self) -> list:
    return [self.referencePoint]

  def occupiedAreaOnMovement(self, vector: tuple) -> list:
    return [self.referencePointOnMovement(vector)]

  def move(self, vector: tuple) -> None:
    self.referencePoint = self.referencePointOnMovement(vector)

  def referencePointOnMovement(self, vector: tuple) -> tuple:
    return addPointAndVector(self.referencePoint, vector)


class Package(MoveableObject):

  def pickupArea(self) -> list:
    return list(map(self.referencePointOnMovement, [(-1, 0), (1, 0)]))

  def isPointWithinPickupArea(self, point: tuple) -> bool:
    return point in self.pickupArea()


class Agent(MoveableObject):

  def __init__(self, referencePoint: tuple) -> None:
    super().__init__(referencePoint)
    self.attachedObjects = []

  def attachObject(self, obj: MoveableObject) -> None:
    if obj not in self.attachedObjects:
      self.attachedObjects.append(obj)

  def occupiedArea(self) -> list:
    area = super().occupiedArea()
    for obj in self.attachedObjects:
      area.extend(obj.occupiedArea())
    return area

  def occupiedAreaOnMovement(self, vector: tuple) -> list:
    area = super().occupiedAreaOnMovement(vector)
    for obj in self.attachedObjects:
      area.extend(obj.occupiedAreaOnMovement(vector))
    return area

  def move(self, vector: tuple) -> None:
    super().move(vector)
    for obj in self.attachedObjects:
      obj.move(vector)


class GridWorldScene:

  def __init__(self, sceneFile: str) -> None:
    self.gridMap = GridMap.fromMapFile(sceneFile)
    self.package = Package(self.gridMap.packageStartingPoint)
    self.agent = Agent(self.gridMap.agentStartingPoint)
