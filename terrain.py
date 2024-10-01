class TerrainType:
    def __init__(self):
        self.name = "Default Terrain"
        self.image_path = ""
        self.movement_cost = 1
        self.defense_bonus = 0.0
        self.is_water = False
        self.is_impassable = False


class GrassTerrain(TerrainType):
    def __init__(self):
        super().__init__()
        self.name = "Grasslands"
        self.image_path = "content/New_Grass_2.png"
        self.movement_cost = 1
        self.defense_bonus = 0.0


class ForestTerrain(TerrainType):
    def __init__(self):
        super().__init__()
        self.name = "Forest"
        self.image_path = "content/New_Forest.png"
        self.movement_cost = 2
        self.defense_bonus = 1.0


class HillsTerrain(TerrainType):
    def __init__(self):
        super().__init__()
        self.name = "Hills"
        self.image_path = "content/New_Hills.png"
        self.movement_cost = 2
        self.defense_bonus = 1.0


class MountainTerrain(TerrainType):
    def __init__(self):
        super().__init__()
        self.name = "Mountains"
        self.image_path = "content/New_Mountains.png"
        self.movement_cost = 999
        self.defense_bonus = 3.0
        self.is_impassable = True


class WaterTerrain(TerrainType):
    def __init__(self):
        super().__init__()
        self.name = "Water"
        self.image_path = "content/New_Water.png"
        self.movement_cost = 999
        self.defense_bonus = 0.0
        self.is_water = True