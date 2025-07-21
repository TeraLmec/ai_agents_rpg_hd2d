import os
import json
from entities import CombatEntity, CombatAction
from engine import CombatSimulator

# 1) Chemin vers le dossier data
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Fonction utilitaire pour charger une entité sans champ "id" dans le JSON
def load_entity(json_path):
    name = os.path.splitext(os.path.basename(json_path))[0]
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    entity = CombatEntity.from_dict(data)
    entity.id = name  # définir l'id à partir du nom de fichier
    return entity

# 2) Chargement de l'IA et de l’ennemi
ai_entity = load_entity(os.path.join(DATA_DIR, 'fighter.json'))
enemy_entity = load_entity(os.path.join(DATA_DIR, 'enemy.json'))

# 3) Construction de la liste d’actions disponibles (depuis l'IA)
with open(os.path.join(DATA_DIR, 'fighter.json'), encoding='utf-8') as f:
    ai_data = json.load(f)
actions = [CombatAction.from_dict(a) for a in ai_data.get('actions', [])]

# 4) Règles de combat
rules = {
    'max_actions_per_turn': 3,
    'ap_gain_per_turn': 1
}

# 5) Lancement de la simulation
sim = CombatSimulator(ai_entity, enemy_entity, actions, rules)
while ai_entity.is_alive() and enemy_entity.is_alive():
    sim.run_turn()