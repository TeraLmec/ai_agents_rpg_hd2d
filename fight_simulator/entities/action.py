class CombatAction:
    def __init__(self, id, code, cost, multiplier, duration, targets="enemy", effects=None):
        self.id = id
        self.code = code
        self.cost = cost
        self.multiplier = multiplier
        self.duration = duration
        self.targets = targets
        self.effects = effects or []

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            code=data.get("code", data["id"]),
            cost=data["cost"],
            multiplier=data.get("baseMultiplier", 0.0),
            duration=max(e.get("duration", 0) for e in data.get("effects", [])),
            targets=data.get("targets", "enemy"),
            effects=data.get("effects", [])
        )