from utils.logger import Logger
from utils.effect import Effect

class CombatSimulator:
    def __init__(self, ai_entity, enemy_entity, actions, rules):
        self.ai = ai_entity
        self.enemy = enemy_entity
        self.actions = actions
        self.turn = 1
        self.actions_per_turn = rules["max_actions_per_turn"]
        self.ap_gain = rules["ap_gain_per_turn"]

    def run_turn(self):
        Logger.title(f"\n--- Tour {self.turn} ---")
        entities = sorted([self.ai, self.enemy], key=lambda e: -e.speed)

        for entity in entities:
            if not entity.is_alive():
                continue
            entity.update_effects()
            self.execute_actions(entity)

        self.ai.ap = min(self.ai.ap + self.ap_gain, self.ai.ap_max)
        self.enemy.ap = min(self.enemy.ap + self.ap_gain, self.enemy.ap_max)
        self.turn += 1

    def execute_actions(self, entity):
        available_actions = [a for a in self.actions if a.cost <= entity.ap]
        if not available_actions:
            Logger.info(f"{entity.id} passe son tour")
            return
        action = available_actions[0]
        Logger.action(f"{entity.id} utilise {action.code} (mult: {action.multiplier})")
        self.apply_action(entity, self.enemy if entity == self.ai else self.ai, action)
        entity.ap -= action.cost

    def apply_action(self, source, target, action):
        if action.code == "phy":
            atk = source.get_modified_stat("physAtk")
            dfn = target.get_modified_stat("physDef")
            dmg = int(action.multiplier * atk - dfn)
            dmg = max(dmg, 0)
            target.hp -= dmg
            Logger.damage(f"{source.id} inflige {dmg} dmg à {target.id} (HP restant : {target.hp})")
        elif action.code == "atk":
            source.buffs.append(Effect("atk", 0.25, action.duration))
            Logger.buff(f"{source.id} gagne un buff d'attaque +25% pour {action.duration} tours")