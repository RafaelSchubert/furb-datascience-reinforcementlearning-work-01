import random
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
    return (self.gridMap.isPointWithinExtractionArea(self.package.referencePoint) and
            self.agent.isObjectCaptured(self.package))

  def moveAgent(self, vector: tuple) -> None:
    self.agentTriesToCapturePackage_()
    if self.canAgentMove_(vector):
      self.agent.move(vector)

  def agentTriesToCapturePackage_(self) -> None:
    if self.package.isPointWithinCaptureArea(self.agent.referencePoint):
      self.agent.captureObject(self.package)

  def canAgentMove_(self, vector: tuple) -> bool:
    relevantObjects = [self.agent] + self.agent.capturedObjects
    relevantPoints = (obj.referencePointOnMovement(vector) for obj in relevantObjects)
    return all(map(self.isPointOccupiableByAgent_, relevantPoints))

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


class GridWorldParameters:

  def __init__(
        self,
        *,
        decayRate: float = 0.9,
        explorationRate: float = 0.1,
        learningRate: float = 0.01,
        punishmentForMovement: float = -0.1,
        punishmentForInvalidMovement: float = -1.,
        rewardForPackageCapture: float = +1.,
        rewardForPackageExtraction: float = +1.
      ) -> None:
    self.decayRate = decayRate
    self.explorationRate = explorationRate
    self.learningRate = learningRate
    self.punishmentForMovement = punishmentForMovement
    self.punishmentForInvalidMovement = punishmentForInvalidMovement
    self.rewardForPackageCapture = rewardForPackageCapture
    self.rewardForPackageExtraction = rewardForPackageExtraction


class GridWorldProblem:

  def __init__(self, sceneFilePath: str, parameters: GridWorldParameters = GridWorldParameters()) -> None:
    self.sceneFile = sceneFilePath
    self.parameters = parameters
    self.reset_()
    self.episodeCount = 0

  def run(self, episodes: int = 1) -> None:
    self.reset_()
    self.episodeCount = episodes
    for _ in range(episodes):
      self.runEpisode_()

  def reset_(self) -> None:
    self.scene = None
    self.scores = {}
    self.episodeCyclesCount = []

  def runEpisode_(self) -> None:
    self.resetEpisode_()
    while not self.scene.isGoalAchieved():
      self.runEpisodeCycle_()

  def resetEpisode_(self) -> None:
    self.scene = GridWorldScene(self.sceneFile)
    if not self.scores:
      self.initScores_()
    self.episodeCyclesCount.append(0)

  def initScores_(self) -> None:
    scoreKeysIteration = product(pointsInSize(self.scene.gridMap.size), GridWorldAction)
    self.scores = dict(product(scoreKeysIteration, [0.]))

  def runEpisodeCycle_(self) -> None:
    self.episodeCyclesCount[-1] += 1
    oldState = self.currentState_()
    actionTaken = self.takeAction_()
    newState = self.currentState_()
    self.reinforceLearning_(oldState, newState, actionTaken)

  def currentState_(self) -> tuple:
    return self.scene.agent.referencePoint

  def takeAction_(self) -> None:
    action = self.chooseAction_()
    self.executeAction_(action)
    return action

  def chooseAction_(self) -> GridWorldAction:
    if self.parameters.explorationRate < random.random():
      return self.chooseBestAction_()
    return self.chooseAnyAction_()

  def chooseAnyAction_(self) -> GridWorldAction:
    return random.choice(list(GridWorldAction))

  def chooseBestAction_(self) -> GridWorldAction:
    currentState = self.currentState_()
    bestLearntActions = self.bestActionsForState(currentState)
    return random.choice(bestLearntActions)

  def bestActionsForState(self, state: tuple) -> list:
    maximumActionScoreForState = self.maximumScoreForState_(state)
    return [action for action in GridWorldAction if self.scores[(state, action)] == maximumActionScoreForState]

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
    self.scores[(oldState, actionTaken)] += self.parameters.learningRate * self.reinforcementValue_(oldState, newState, actionTaken)

  def reinforcementValue_(self, oldState: tuple, newState: tuple, actionTaken: GridWorldAction) -> float:
    return self.punishmentOrRewardValue_(oldState, newState) + self.parameters.decayRate * self.temporalDifference_(oldState, newState, actionTaken)

  def punishmentOrRewardValue_(self, oldState: tuple, newState: tuple) -> float:
    if self.didAgentNotMove_(oldState, newState):
      return self.parameters.punishmentForInvalidMovement
    elif self.isPackageBeingDelivered_():
      return self.parameters.rewardForPackageExtraction
    elif self.isPackageBeingCaptured_(newState):
      return self.parameters.rewardForPackageCapture
    return self.parameters.punishmentForMovement

  def didAgentNotMove_(self, oldState: tuple, newState: tuple) -> bool:
    return newState == oldState

  def isPackageBeingCaptured_(self, newState: tuple) -> bool:
    return (not self.scene.agent.isObjectCaptured(self.scene.package) and
            self.scene.package.isPointWithinCaptureArea(newState))

  def isPackageBeingDelivered_(self) -> bool:
    return (self.scene.agent.isObjectCaptured(self.scene.package) and
            self.scene.gridMap.isPointWithinExtractionArea(self.scene.package.referencePoint))

  def temporalDifference_(self, oldState: tuple, newState: tuple, actionTaken: GridWorldAction) -> float:
    return self.maximumScoreForState_(newState) - self.scores[(oldState, actionTaken)]

  def maximumScoreForState_(self, state: tuple) -> float:
    possibleStatesIteration = map(tuple, product([state], GridWorldAction))
    return max(map(self.scores.get, possibleStatesIteration))
