import json
import os

from combat_entity import CombatEntity
from utils.effect import Effect
from utils.logger import Logger

# Mapping codes > 0 à une stat
STAT_OFF = {1: "principale atk", 2: "neutre atk", 3: "faible atk"}
STAT_DEF = {4: "principale def", 5: "neutre def", 6: "faible def"}

def load_entity(path, default_id=None):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    entity = CombatEntity.from_dict(data)
    if default_id:
        entity.id = default_id
    return entity

def get_action_type(action):
    # On récupère tous les codes non nuls
    codes = [eff["code"] for eff in action["effects"] if eff["code"] != 0]
    # Si l’un des codes est offensif, c’est une attaque
    if any(code in STAT_OFF for code in codes):
        return "Attaque"
    # Sinon on considère que c’est un buff/débuff
    return "Buff/Debuff"

def display_active_effects(entity):
    Logger.info(f"Effets actifs sur {entity.id} :")
    if not entity.buffs and not entity.debuffs:
        Logger.info("  Aucun")
    for buff in entity.buffs:
        Logger.buff(f"  +{int(buff.value*100)}% {buff.code} (reste {buff.duration} tours)")
    for debuff in entity.debuffs:
        Logger.warning(f"  -{int(debuff.value*100)}% {debuff.code} (reste {debuff.duration} tours)")

if __name__ == "__main__":
    base = os.path.dirname(__file__)
    dir_fighters = os.path.join(base, "..", "fight_simulator", "fighters")
    player = load_entity(os.path.join(dir_fighters, "player.json"), default_id="player")
    enemy  = load_entity(os.path.join(dir_fighters, "enemy.json"),  default_id="enemy")

    # Règles de combat issues de fighter_rules.md
    rules = {"max_actions_per_turn": 3, "ap_gain_per_turn": 1}

    Logger.title(f"Début du combat : {player.id} vs {enemy.id}")
    tour = 1

    while player.is_alive() and enemy.is_alive():
        Logger.info(f"\n=== Tour {tour} ===")
        display_active_effects(player)
        display_active_effects(enemy)

        # Décrémentation des effets en début de tour (après affichage)
        for ent in (player, enemy):
            ent.update_effects()

        # Regen PA
        for ent in (player, enemy):
            ent.ap = min(ent.ap + rules["ap_gain_per_turn"], ent.ap_max)

        # Initiative par speed
        ordre = sorted([player, enemy], key=lambda e: e.speed, reverse=True)

        for attaquant in ordre:
            defenseur = enemy if attaquant is player else player
            if not attaquant.is_alive() or not defenseur.is_alive():
                break

            Logger.action(f"\nPhase de {attaquant.id} (HP {attaquant.hp}/{attaquant.hp_max}, AP {attaquant.ap}/{attaquant.ap_max})")
            for _ in range(rules["max_actions_per_turn"]):
                if not attaquant.is_alive() or attaquant.ap <= 0:
                    break

                # Affichage des actions disponibles
                for i, act in enumerate(attaquant.actions, start=1):
                    t = get_action_type(act)
                    print(f"{i}) {act['id']} - {t} (coût {act['cost']} PA)")

                # Validation du choix utilisateur
                while True:
                    try:
                        choix = int(input("Votre choix : ")) - 1
                        if choix < 0 or choix >= len(attaquant.actions):
                            raise IndexError
                        action = attaquant.actions[choix]
                        break
                    except (ValueError, IndexError):
                        Logger.warning("Choix invalide, réessayez")

                if action["cost"] > attaquant.ap:
                    Logger.warning("PA insuffisants, action impossible")
                    continue

                    # Décrémentation des PA
                attaquant.ap -= action["cost"]
                Logger.info(f"\nPA restants : {attaquant.ap}/{attaquant.ap_max}")  # affichage

                # Application des effets…
                for eff in action["effects"]:
                    code = eff["code"]
                    dur = eff["duration"]
                    mult = eff["multiplier"]

                    if code in STAT_OFF:
                        # Dégâts = stat_off * multiplier%
                        stat = STAT_OFF[code]
                        base = attaquant.get_modified_stat(stat)
                        dmg  = int(base * mult / 100)
                        defenseur.hp = max(defenseur.hp - dmg, 0)
                        Logger.damage(f"{attaquant.id} inflige {dmg} à {defenseur.id}")

                    elif code in STAT_DEF:
                        # Debuff de défense sur la cible
                        stat = STAT_DEF[code]
                        val  = mult / 100
                        defenseur.debuffs.append(Effect(stat, val, dur))
                        Logger.action(f"{defenseur.id} subit -{int(val*100)}% {stat} pour {dur} tours")

                    elif 7 <= code <= 9:
                        # Buff spéciaux sur l'attaquant
                        stat = "speed" if code == 7 else "ap_max" if code == 8 else "hp_max"
                        val  = mult / 100
                        attaquant.buffs.append(Effect(stat, val, dur))
                        Logger.buff(f"{attaquant.id} gagne +{int(val*100)}% {stat} pour {dur} tours")

                    elif code == 10:
                        # Skip = petit buff de défense basique
                        val = 0.1
                        attaquant.buffs.append(Effect("principale def", val, dur))
                        Logger.buff(f"{attaquant.id} gagne +10% défense pour {dur} tours")

        # Statut fin de tour
        Logger.info(f"\nStatuts : {player.id} {player.hp} HP | {enemy.id} {enemy.hp} HP")
        tour += 1

    vainqueur = player if player.is_alive() else enemy
    Logger.title(f"\nLe vainqueur est {vainqueur.id}")