from hashlib import new
import random
from enum import Enum
from itertools import product

from numpy.core.fromnumeric import prod


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

  def captureArea(self) -> list:
    return list(map(self.referencePointOnMovement, [(-1, 0), (1, 0)]))

  def isPointWithinCaptureArea(self, point: tuple) -> bool:
    return point in self.captureArea()


class Agent(MoveableObject):

  def __init__(self, referencePoint: tuple) -> None:
    super().__init__(referencePoint)
    self.capturedObjects = []

  def captureObject(self, obj: MoveableObject) -> None:
    if not self.isObjectCaptured(obj):
      self.capturedObjects.append(obj)

  def isObjectCaptured(self, obj: MoveableObject) -> bool:
    return obj in self.capturedObjects

  def occupiedArea(self) -> list:
    area = super().occupiedArea()
    for obj in self.capturedObjects:
      area.extend(obj.occupiedArea())
    return area

  def occupiedAreaOnMovement(self, vector: tuple) -> list:
    area = super().occupiedAreaOnMovement(vector)
    for obj in self.capturedObjects:
      area.extend(obj.occupiedAreaOnMovement(vector))
    return area

  def move(self, vector: tuple) -> None:
      super().move(vector)
      for obj in self.capturedObjects:
        obj.move(vector)


class GridWorldScene:

  def __init__(self, sceneFile: str) -> None:
    self.gridMap = GridMap.fromMapFile(sceneFile)
    self.package = Package(self.gridMap.packageStartingPoint)
    self.agent = Agent(self.gridMap.agentStartingPoint)

  def graphView(self) -> str:
    return '\n'.join(map(self.rowGraphView_, range(self.gridMap.size[1])))

  def rowGraphView_(self, row: int) -> str:
    coordinates = product(range(self.gridMap.size[0]), [row])
    return ''.join(map(self.tileGraphSymbol_, coordinates))

  def tileGraphSymbol_(self, point: tuple) -> str:
    if point == self.agent.referencePoint:
      return 'A'
    if point == self.package.referencePoint:
      return TileType.PACKAGE_POINT.symbol
    if self.gridMap.isPointWithinExtractionArea(point):
      return TileType.EXTRACTION_ZONE.symbol
    if not self.gridMap.isPointReachable(point):
      return TileType.WALL.symbol
    return TileType.FLOOR.symbol

  def isGoalAchieved(self) -> bool:
    return self.isAgentWithinExtractionZone_() and self.agent.isObjectCaptured(self.package)

  def isAgentWithinExtractionZone_(self) -> bool:
    return all(map(self.gridMap.isPointWithinExtractionArea, self.agent.occupiedArea()))

  def moveAgent(self, vector: tuple) -> None:
    self.agentTriesToCapturePackage_()
    if self.canAgentMove_(vector):
      self.agent.move(vector)

  def agentTriesToCapturePackage_(self) -> None:
    if self.package.isPointWithinCaptureArea(self.agent.referencePoint):
      self.agent.captureObject(self.package)

  def canAgentMove_(self, vector: tuple) -> bool:
    agentOccupiedAreaOnMovement = self.agent.occupiedAreaOnMovement(vector)
    return all(map(self.isPointOccupiableByAgent_, agentOccupiedAreaOnMovement))

  def isPointOccupiableByAgent_(self, point: tuple) -> bool:
    return (self.gridMap.isPointReachable(point) and
            (point != self.package.referencePoint or self.agent.isObjectCaptured(self.package)))


class GridWorldAction(Enum):

  MOVE_AGENT_NORTH = ('Move the agent 1 tile to the north.', )
  MOVE_AGENT_SOUTH = ('Move the agent 1 tile to the south.', )
  MOVE_AGENT_EAST = ('Move the agent 1 tile to the east.', )
  MOVE_AGENT_WEST = ('Move the agent 1 tile to the west.', )

  def __init__(self, description) -> None:
    super().__init__()
    self.description = description


class GridWorldProblem:

  def __init__(self, sceneFilePath: str) -> None:
    self.sceneFile = sceneFilePath
    self.resetEpisode_()
    self.initScores_()

  def resetEpisode_(self) -> None:
    self.scene = GridWorldScene(self.sceneFile)
    self.episodeCycleCount = 0

  def initScores_(self) -> None:
    statesIteration = product(pointsInSize(self.scene.gridMap.size), GridWorldAction)
    self.scores = { state: 0. for state in statesIteration }

  def runEpisode_(self) -> None:
    self.resetEpisode_()
    while (not self.scene.isGoalAchieved()):
      self.runEpisodeCycle_()

  def runEpisodeCycle_(self) -> None:
    self.episodeCycleCount += 1
    oldState = self.scene.agent.referencePoint
    actionTaken = self.takeAction_()
    newState = self.scene.agent.referencePoint
    self.reinforceLearning_(oldState, newState, actionTaken)

  def takeAction_(self) -> None:
    action = self.chooseAction_()
    self.executeAction_(action)
    return action

  def chooseAction_(self) -> GridWorldAction:
    return random.choice(list(GridWorldAction))

  def executeAction_(self, action: GridWorldAction) -> None:
    if action is GridWorldAction.MOVE_AGENT_NORTH:
      self.scene.moveAgent((0, -1))
    elif action is GridWorldAction.MOVE_AGENT_SOUTH:
      self.scene.moveAgent((0, +1))
    elif action is GridWorldAction.MOVE_AGENT_EAST:
      self.scene.moveAgent((+1, 0))
    elif action is GridWorldAction.MOVE_AGENT_WEST:
      self.scene.moveAgent((-1, 0))

  def reinforceLearning_(self, oldState: tuple, newState: tuple, actionTaken: GridWorldAction) -> None:
    oldStateScoreKey = (oldState, actionTaken)
    oldStateScore = self.scores[oldStateScoreKey]
    self.scores[oldStateScoreKey] = oldStateScore + 0.01 * (-0.1 + 0.9 * self.maximumScoreForState_(newState) - oldStateScore)

  def maximumScoreForState_(self, point: tuple) -> float:
    possibleStatesIteration = map(tuple, product([point], GridWorldAction))
    return max(map(self.scores.get, possibleStatesIteration))
