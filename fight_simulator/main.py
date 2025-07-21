from entities import CombatEntity, CombatAction
from engine import CombatSimulator
from utils.effect import Effect

ai_stats = {"physAtk": 42, "physDef": 29, "elemAtk": 15, "elemDef": 14, "spirAtk": 5, "spirDef": 6}
enemy_stats = {"physAtk": 28, "physDef": 15, "elemAtk": 5, "elemDef": 8, "spirAtk": 0, "spirDef": 4}

ai = CombatEntity("warrior", 4, 83, 120, 3, 4, 5, ai_stats, buffs=[Effect("atk", 0.2, 1)], debuffs=[])
enemy = CombatEntity("goblin", 3, 47, 90, 2, 4, 4, enemy_stats)

actions = [
    CombatAction("free_slash", "phy", 0, 1.0, 0),
    CombatAction("power_strike", "phy", 2, 1.7, 0),
    CombatAction("battle_shout", "atk", 1, 0, 2)
]

rules = { "max_actions_per_turn": 3, "ap_gain_per_turn": 1 }

sim = CombatSimulator(ai, enemy, actions, rules)

while ai.is_alive() and enemy.is_alive():
    sim.run_turn()