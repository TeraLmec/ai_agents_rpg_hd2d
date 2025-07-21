from utils.logger import Logger
from utils.effect import Effect

class CombatSimulator:
    def __init__(self, ai_entity, enemy_entity, actions, rules):
        self.ai = ai_entity
        self.enemy = enemy_entity
        self.actions = actions
        self.turn = 1
        self.actions_per_turn = rules.get('max_actions_per_turn', 1)
        self.ap_gain = rules.get('ap_gain_per_turn', 0)

    def run_turn(self):
        Logger.title(f"\n--- Tour {self.turn} ---")
        # ordre par vitesse décroissante
        for entity in sorted([self.ai, self.enemy], key=lambda e: -e.speed):
            if not entity.is_alive():
                continue
            entity.update_effects()
            self.execute_actions(entity)

        # regen AP en fin de tour
        self.ai.ap = min(self.ai.ap + self.ap_gain, self.ai.ap_max)
        self.enemy.ap = min(self.enemy.ap + self.ap_gain, self.enemy.ap_max)
        self.turn += 1

    def execute_actions(self, entity):
        # récupérer actions disponibles
        available = sorted([a for a in self.actions if a.cost <= entity.ap], key=lambda a: a.id)
        if not available:
            Logger.info(f"{entity.id} passe son tour")
            return
        action = available[0]
        Logger.action(f"{entity.id} utilise action {action.id} (cost: {action.cost})")
        target = self.enemy if entity == self.ai else self.ai
        # appliquer chaque effet
        for eff in action.effects:
            code = eff.get('code', 0)
            mult = eff.get('multiplier', 0)
            duration = eff.get('duration', 0)
            if code == 0:
                continue
            self.apply_effect(entity, target, code, mult, duration)
        entity.ap -= action.cost

    def apply_effect(self, source, target, code, mult, duration):
        # mapping des attaques
        if code in (1, 2, 3):
            # code 1=physique, 2=neutre, 3=faible
            stat_map = {
                1: ('principale atk', 'principale def'),
                2: ('neutre atk', 'neutre def'),
                3: ('faible atk', 'faible def')
            }
            atk_stat, def_stat = stat_map[code]
            self._attack(source, target, mult, atk_stat, def_stat)
        elif code == 4:
            # buff attaque
            value = mult / 100
            source.buffs.append(Effect('atk', value, duration))
            Logger.buff(f"{source.id} gagne un buff d'attaque +{int(value*100)}% pour {duration} tours")
        elif code == 5:
            # buff défense
            value = mult / 100
            source.buffs.append(Effect('def', value, duration))
            Logger.buff(f"{source.id} gagne un buff de défense +{int(value*100)}% pour {duration} tours")
        elif code == 6:
            # soin
            heal = mult
            source.hp = min(source.hp + heal, source.hp_max)
            Logger.heal(f"{source.id} se soigne de {heal} pts (HP: {source.hp}/{source.hp_max})")
        elif code == 7:
            # étourdissement: skip next turn
            target.debuffs.append(Effect('skip', None, duration))
            Logger.debuff(f"{target.id} est étourdi pour {duration} tours")
        elif code == 8:
            # poison
            target.debuffs.append(Effect('psn', mult, duration))
            Logger.debuff(f"{target.id} est empoisonné ({mult} dégâts/round) pour {duration} tours")
        elif code == 9:
            # intimidation: -atk/-def
            value = mult / 100
            target.debuffs.append(Effect('atk', value, duration))
            target.debuffs.append(Effect('def', value, duration))
            Logger.debuff(f"{target.id} subit -{int(value*100)}% atk/def pour {duration} tours")
        elif code >= 99:
            # passer son tour
            Logger.info(f"{source.id} passe son tour")
        else:
            Logger.info(f"Effet inconnu code={code}")

    def _attack(self, source, target, multiplier, atk_stat, def_stat):
        atk = source.get_modified_stat(atk_stat)
        dfn = target.get_modified_stat(def_stat)
        dmg = max(int(multiplier * atk - dfn), 0)
        target.hp -= dmg
        Logger.damage(f"{source.id} inflige {dmg} pts à {target.id} (HP: {target.hp}/{target.hp_max})")