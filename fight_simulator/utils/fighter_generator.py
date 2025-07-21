from random import randint

class FighterGenerator:
    @staticmethod
    def generate(level=None):
        level = level or randint(1, 5)
        hp_max = randint(80, 120) * level
        return {
            "id": "random_enemy",
            "level": level,
            "hp": hp_max,
            "hp_max": hp_max,
            "ap": 4,
            "ap_max": 4,
            "speed": randint(3, 5) + level,
            "stats": {
                "physAtk": int(0.30 * level * 30),
                "physDef": int(0.30 * level * 30),
                "elemAtk": int(0.15 * level * 30),
                "elemDef": int(0.15 * level * 30),
                "spirAtk": int(0.05 * level * 30),
                "spirDef": int(0.05 * level * 30)
            }
        }