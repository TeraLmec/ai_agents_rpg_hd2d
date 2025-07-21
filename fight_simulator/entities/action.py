class CombatAction:
    def __init__(self, id, code, cost, multiplier, duration, targets="enemy"):
        self.id = id
        self.code = code
        self.cost = cost
        self.multiplier = multiplier
        self.duration = duration
        self.targets = targets