# 📖 Guide complet du Système de combat 🎮

> **Document de référence rapide pour les développeurs**

---

## 🌱 1. Entités & caractéristiques de base

| Icône | Champ                | Règle / plage par niveau                |
|-------|----------------------|-----------------------------------------|
| 🆔    | id, class, level     | Niveau 1-5 (30 pts de stats / niveau)   |
| ❤️    | hpMax, hp            | (80-120 × lvl) modulé par la classe     |
|       |                      | • Guerrier 💪 : fourchette haute        |
|       |                      | • Mage 🔮 : moyenne                     |
|       |                      | • Prêtre ✝️ : équilibrée + soins        |
| ⚡    | speed                | 2-8 au niveau 1, +1/lvl                 |
| 🔋    | apMax, ap            | 4… puis 5 AP au niveau 5                |
| 📊    | statistics           | 6 stats : phys/elem/spir × Atk/Def      |
|       |                      | Distribution/30 pts :                   |
|       |                      | • Principal 30 % ± 5                    |
|       |                      | • Neutre 15 % ± 5                       |
|       |                      | • Faible 5 % ± 5                        |

---

## 🔋 2. Points d’Action & limite d’actions

| Règle                | Valeur                                 |
|----------------------|----------------------------------------|
| Gain automatique     | +1 AP / début de tour                  |
| AP max               | 4 (lvl < 5) → 5 (lvl 5)                |
| Actions / tour       | max_actions_per_turn = 3               |
| ▶️ Skip              | 0 AP • termine le tour                 |
| 🗡️ Attaque gratuite  | 0 AP • 1 action • dégâts faibles       |
| 💥 Attaque payante   | 1-5 AP • 1 action                      |
| ✨ / ☠️ Buff/Debuff   | ≥ 1 AP • 1 action et termine le tour   |

---

## ⚔️ 3. Catalogue des actions

| Code | Emoji | PA    | Termine tour ? | Effet                        |
|------|-------|-------|---------------|------------------------------|
| phy  | 🗡️    | 0/1-5 | 🚫            | Dégâts physiques             |
| elm  | 🔥    | 0/1-5 | 🚫            | Dégâts élémentaires          |
| spr  | 🌀    | 0/1-5 | 🚫            | Dégâts spirituels            |
| atk  | ✨    | ≥1    | ✅            | Buff attaque                 |
| def  | 🛡️    | ≥1    | ✅            | Buff défense                 |
| med  | ❤️‍🩹  | ≥1    | ✅            | Soin                         |
| stn  | 💫    | ≥1    | ✅            | Stun (skip adverse)          |
| psn  | ☠️    | ≥1    | ✅            | Poison                       |
| imd  | 😱    | ≥1    | ✅            | Intimidation (-Atk/-Def)     |
| skp  | ⏭️    | 0     | ✅            | Skip                         |

---

## 🛠️ 4. Définition d’une attaque (JSON)

```json
{
  "id": "power_strike",
  "code": "phy",
  "cost": 2,
  "baseMultiplier": 1.7,
  "effects": [],
  "targets": "enemy",
  
  Si cost ≥ 2 ➜ possibilité d’ajouter un 2ᵉ effet (debuff, soin, etc.).
}
```

## 📐 5. Formule de dégâts

```python
AtkMultiplier = Rand[10‒15] × (cost + 1)

damage = AtkMultiplier
         × (1 + AttStat/100)
         × (1 − DefStatTarget/100)
```

AttStat / DefStat sont pris dans la paire phys/elem/spir correspondant au code de l’attaque.

---

## 🔄 6. Déroulement d’un tour

- **Début** :  
  +1 AP, décrément des durées d’effets temporaires.
- **Phase d’actions** :  
  Jusqu’à 3 actions (selon AP restant).
- **Buff/Debuff ou Skip** :  
  Ces actions terminent immédiatement le tour.
- **Fin** :  
  Passage à l’adversaire.

---

## 🧩 7. JSON “runtime” envoyé à l’IA

```json
{
  "battle_id": "btl-00042",
  "tick": 19,
  "state": {
    "turn": 6,
    "actions_left_in_turn": 2,
    "rules": { "max_actions_per_turn": 3, "ap_gain_per_turn": 1 },
    "self": { /* voir §1 */ },
    "enemies": [ /* 1..N */ ],
    "available_actions": [ /* max 4 actions */ ]
  }
}
```
Un nouveau JSON est fourni après chaque action ; l’IA renvoie simplement :
```json
{ "action_id": "power_strike", "target_id": "goblin1" }
```

## 🧠 8. Inputs / Outputs du réseau de neurones
### Entrée normalisée (exemple MAX_ACTIONS = 4 ; MAX_BUFFS = 4)

```python
state_vector = [
  turn_norm, actions_left_norm,
  self_hp_norm, self_ap_norm, self_speed_norm,
  self_stats[6],
  enemy0_hp_norm, enemy0_ap_norm, enemy0_speed_norm,
  enemy0_stats[6],
  buffs[4][code_one_hot(9)+value+duration],
  debuffs[4][...],
  actions[4][code_one_hot(10)+cost_norm+multiplier_norm]
]
```

### Sortie
```python
action_logits[4]  # softmax → choisir index de l’action
```

## 📝 9. Journalisation (logs)
```python
{
  "enemy_actions": [
    { "order": 1, "code": "phy", "multiplier": 1.2, "duration": 0 },
    { "order": 2, "code": "psn", "multiplier": 0,   "duration": 3 }
  ],
  "states": [
    { "turn": 6, "self_hp": 83, "enemy_hp": 47, "buffs": [...], "debuffs": [...] }
  ]
}
```

## 🧰 10. Conseils d’implémentation

| ⚙️ Étape         | Outils / best-practices                           |
| ---------------- | ------------------------------------------------- |
| Validation JSON  | `pydantic`, tests unitaires                       |
| Flatten & scale  | `numpy`, `sklearn.preprocessing`                  |
| Environnement RL | `gymnasium`, reward = (-dmg\_subi + dmg\_infligé) |
| Modèle           | MLP PyTorch ou Transformer (inference text/json)  |
| Inference API    | FastAPI ➜ retourne `action_id` & `target_id`      |
| Logging          | stocker `(state, action, reward)` pour fine-tune  |
