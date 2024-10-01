from MovableUnit import MovableUnit


class MilitaryUnit(MovableUnit):
    def __init__(self, player_owner, spawn_hex):
        super().__init__(player_owner, spawn_hex)
        self.blocks_enemy = True
        self.combat_strength = 1
        self.level = "Recruit"
        self.cost = 1
        self.battle_role = 'Melee'


class Phalanx(MilitaryUnit):
    def __init__(self, player_owner, spawn_hex):
        super().__init__(player_owner, spawn_hex)
        self.dead_image = 'content/phalanx_dead.png'
        self.name = "Phalanx"
        self.movement_speed = 2
        self.cost = 20
        self.select_sound = "content/sounds/Phalanx_Select.wav"
        self.move_sound = "content/sounds/Phalanx_Move.wav"
        self.build_sound = "content/sounds/Phalanx_Build.wav"

    def get_image_path(self):
        team_images = ['content/phalanx_low.png', 'content/green_phalanx_low.png']
        return team_images[self.player_owner]

class Garrison(MilitaryUnit):
    def __init__(self, player_owner, spawn_hex):
        super().__init__(player_owner, spawn_hex)
        self.dead_image = 'content/garrison_dead.png'
        self.name = "Garrison"
        self.movement_speed = 0
        self.cost = 15
        self.select_sound = "content/sounds/Phalanx_Select.wav"
        self.move_sound = "content/sounds/Phalanx_Move.wav"
        self.build_sound = "content/sounds/Phalanx_Build.wav"

    def get_image_path(self):
        team_images = ['content/garrison.png', 'content/garrison_green.png']
        return team_images[self.player_owner]


class Archer(MilitaryUnit):
    def __init__(self, player_owner, spawn_hex):
        super().__init__(player_owner, spawn_hex)
        self.name = "Archer"
        self.view_distance = 3
        self.dead_image = 'content/archer_dead.png'
        self.movement_speed = 2
        self.cost = 20
        self.select_sound = "content/sounds/Archer_Select.wav"
        self.move_sound = "content/sounds/Archer_Move.wav"
        self.build_sound = "content/sounds/Archer_Build.wav"
        self.battle_role = 'Ranged'

    def get_image_path(self):
        team_images = ['content/archer.png', 'content/green_archer.png']
        return team_images[self.player_owner]


class Cavalry(MilitaryUnit):
    def __init__(self, player_owner, spawn_hex):
        super().__init__(player_owner, spawn_hex)
        self.name = "Cavalry"
        self.view_distance = 2
        self.dead_image = 'content/cavalry_dead.png'
        self.movement_speed = 4
        self.cost = 40
        self.select_sound = "content/sounds/Cavalry_Select.wav"
        self.move_sound = "content/sounds/Cavalry_Move.wav"
        self.build_sound = "content/sounds/Cavalry_Build.wav"
        self.battle_role = 'Cavalry'

    def get_image_path(self):
        team_images = ['content/cavalry.png', 'content/green_cavalry.png']
        return team_images[self.player_owner]


class Trireme(MilitaryUnit):
    def __init__(self, player_owner, spawn_hex):
        super().__init__(player_owner, spawn_hex)
        self.name = "Trireme"
        self.view_distance = 2
        self.dead_image = 'content/trireme_dead.png'
        self.movement_speed = 4
        self.cost = 40
        self.select_sound = "content/sounds/Trireme_Select.wav"
        self.move_sound = "content/sounds/Trireme_Move.wav"
        self.build_sound = "content/sounds/Trireme_Select.wav"
        self.battle_role = 'Naval'
        self.moves_on_water = True
        self.moves_on_land = False

    def get_image_path(self):
        team_images = ['content/trireme.png', 'content/trireme_green.png']
        return team_images[self.player_owner]
