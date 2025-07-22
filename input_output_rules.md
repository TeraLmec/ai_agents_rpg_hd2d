# Neural Network Input/Output Specifications

## INPUT TO NEURAL NETWORK (Total: 92 values)

### **Player Recent Actions (21 values)**

The 3 most recent player actions (7 values each):

- `order_X`: Action sequence number in combat
- `code_X1`, `code_X2`: Effect type codes (1-9, 99 for skip)
- `multiplier_X1`, `multiplier_X2`: Effect strength values
- `duration_X1`, `duration_X2`: How many rounds effect lasts

### **Active Buffs/Debuffs (12 values)**

#### AI Active Effects (6 values):

- `code_4`, `code_5`: Effect type codes currently on AI
- `multiplier_4`, `multiplier_5`: Effect strength
- `remaining_duration_4`, `remaining_duration_5`: Rounds left

#### Player Active Effects (6 values):

- `code_6`, `code_7`: Effect type codes currently on player
- `multiplier_6`, `multiplier_7`: Effect strength
- `remaining_duration_6`, `remaining_duration_7`: Rounds left

### **Combat Stats (15 values)**

#### AI Stats (12 values):

- `ai_lvl`: AI fighter level
- `ai_hpmax`: AI maximum health points
- `ai_hp`: AI current health points
- `ai_speed`: AI speed stat (determines turn order)
- `ai_apmax`: AI maximum action points
- `ai_ap`: AI current action points
- `ai_higher_atk`: AI physical attack stat
- `ai_higher_def`: AI physical defense stat
- `ai_neutral_atk`: AI elemental attack stat
- `ai_neutral_def`: AI elemental defense stat
- `ai_lower_atk`: AI spiritual attack stat
- `ai_lower_def`: AI spiritual defense stat

#### Player Stats (3 values):

- `ply_hpmax`: Player maximum health points
- `ply_hp`: Player current health points
- `ply_lvl`: Player level

### **Combat State (2 values)**

- `round_count`: Current round number
- `action_left`: Remaining actions this turn

### **AI Available Actions (28 values)**

4 possible actions (7 values each):

- `order_X`: Action ID (8-11)
- `code_X1`, `code_X2`: Effect codes for this action
- `multiplier_X1`, `multiplier_X2`: Effect multipliers
- `duration_X1`, `duration_X2`: Effect durations

**Note**: Unused action slots are set to 0

### **AI Action History (14 values)**

Last 2 AI actions (7 values each):

- Same structure as available actions
- All 0s if AI hasn't acted yet

## OUTPUT FROM NEURAL NETWORK (5 values)

### **Action Probability Distribution**

- **P1**: Probability of choosing first available action (0.0-1.0)
- **P2**: Probability of choosing second available action (0.0-1.0)
- **P3**: Probability of choosing third available action (0.0-1.0)
- **P4**: Probability of choosing fourth available action (0.0-1.0)
- **P5**: Probability of skip action (0.0-1.0) - always available

### **Output Rules**

- All probabilities must **sum to 1.0**
- Unavailable actions should have **probability = 0**
- AI selects action based on **highest probability** or **sampling** from distribution
- **Skip action (P5)** is always available regardless of AP cost

## **Effect Code Reference**

### **Attack Types (Codes 1-3):**

- **Code 1**: Physical attack
- **Code 2**: Elemental attack
- **Code 3**: Spiritual attack

### **Buff Types (Codes 4-6):**

- **Code 4**: Buff attack stats
- **Code 5**: Buff defense stats
- **Code 6**: Buff HP (healing)

### **Debuff Types (Codes 7-9):**

- **Code 7**: Debuff stunt (skip opponent's turn)
- **Code 8**: Debuff poison
- **Code 9**: Debuff intimidation (reduce opponent's attack/defense)

### **Special Actions:**

- **Code 10**: Skip turn

## **Decision Context**

The AI receives this complete state information **3 times per round** and must output an action probability distribution each time, allowing it to:

- **React to player patterns** (last 3 actions)
- **Manage resources** (HP/AP)
- **Consider active effects** (buffs/debuffs)
- **Plan strategically** based on available actions and combat state

---

# Spécifications d'Entrée/Sortie du Réseau de Neurones

## ENTRÉE DU RÉSEAU DE NEURONES (Total : 92 valeurs)

### **Actions Récentes du Joueur (21 valeurs)**

Les 3 actions les plus récentes du joueur (7 valeurs chacune) :

- `order_X` : Numéro de séquence d'action dans le combat
- `code_X1`, `code_X2` : Codes de type d'effet (1-9, 99 pour passer)
- `multiplier_X1`, `multiplier_X2` : Valeurs de force d'effet
- `duration_X1`, `duration_X2` : Nombre de rounds pendant lesquels l'effet dure

### **Buffs/Debuffs Actifs (12 valeurs)**

#### Effets Actifs de l'IA (6 valeurs) :

- `code_4`, `code_5` : Codes de type d'effet actuellement sur l'IA
- `multiplier_4`, `multiplier_5` : Force de l'effet
- `remaining_duration_4`, `remaining_duration_5` : Rounds restants

#### Effets Actifs du Joueur (6 valeurs) :

- `code_6`, `code_7` : Codes de type d'effet actuellement sur le joueur
- `multiplier_6`, `multiplier_7` : Force de l'effet
- `remaining_duration_6`, `remaining_duration_7` : Rounds restants

### **Statistiques de Combat (15 valeurs)**

#### Statistiques de l'IA (12 valeurs) :

- `ai_lvl` : Niveau du combattant IA
- `ai_hpmax` : Points de vie maximum de l'IA
- `ai_hp` : Points de vie actuels de l'IA
- `ai_speed` : Statistique de vitesse de l'IA (détermine l'ordre des tours)
- `ai_apmax` : Points d'action maximum de l'IA
- `ai_ap` : Points d'action actuels de l'IA
- `ai_higher_atk` : Statistique d'attaque physique de l'IA
- `ai_higher_def` : Statistique de défense physique de l'IA
- `ai_neutral_atk` : Statistique d'attaque élémentaire de l'IA
- `ai_neutral_def` : Statistique de défense élémentaire de l'IA
- `ai_lower_atk` : Statistique d'attaque spirituelle de l'IA
- `ai_lower_def` : Statistique de défense spirituelle de l'IA

#### Statistiques du Joueur (3 valeurs) :

- `ply_hpmax` : Points de vie maximum du joueur
- `ply_hp` : Points de vie actuels du joueur
- `ply_lvl` : Niveau du joueur

### **État du Combat (2 valeurs)**

- `round_count` : Numéro du round actuel
- `action_left` : Actions restantes ce tour

### **Actions Disponibles de l'IA (28 valeurs)**

4 actions possibles (7 valeurs chacune) :

- `order_X` : ID d'action (8-11)
- `code_X1`, `code_X2` : Codes d'effet pour cette action
- `multiplier_X1`, `multiplier_X2` : Multiplicateurs d'effet
- `duration_X1`, `duration_X2` : Durées d'effet

**Note** : Les emplacements d'actions non utilisés sont définis à 0

### **Historique des Actions de l'IA (14 valeurs)**

Les 2 dernières actions de l'IA (7 valeurs chacune) :

- Même structure que les actions disponibles
- Tous à 0 si l'IA n'a pas encore agi

## SORTIE DU RÉSEAU DE NEURONES (5 valeurs)

### **Distribution de Probabilité d'Actions**

- **P1** : Probabilité de choisir la première action disponible (0.0-1.0)
- **P2** : Probabilité de choisir la deuxième action disponible (0.0-1.0)
- **P3** : Probabilité de choisir la troisième action disponible (0.0-1.0)
- **P4** : Probabilité de choisir la quatrième action disponible (0.0-1.0)
- **P5** : Probabilité de l'action passer (0.0-1.0) - toujours disponible

### **Règles de Sortie**

- Toutes les probabilités doivent **totaliser 1.0**
- Les actions non disponibles devraient avoir **probabilité = 0**
- L'IA sélectionne l'action basée sur la **probabilité la plus élevée** ou **échantillonnage** de la distribution
- **L'action passer (P5)** est toujours disponible indépendamment du coût en PA

## **Référence des Codes d'Effet**

### **Types d'Attaque (Codes 1-3) :**

- **Code 1** : Attaque physique
- **Code 2** : Attaque élémentaire
- **Code 3** : Attaque spirituelle

### **Types de Buff (Codes 4-6) :**

- **Code 4** : Améliorer les statistiques d'attaque
- **Code 5** : Améliorer les statistiques de défense
- **Code 6** : Améliorer les PV (soin)

### **Types de Debuff (Codes 7-9) :**

- **Code 7** : Debuff étourdissement (faire passer le tour de l'adversaire)
- **Code 8** : Debuff poison
- **Code 9** : Debuff intimidation (réduire l'attaque/défense de l'adversaire)

### **Actions Spéciales :**

- **Code 10** : Passer son tour

## **Contexte de Décision**

L'IA reçoit cette information d'état complète **3 fois par round** et doit produire une distribution de probabilité d'action à chaque fois, lui permettant de :

- **Réagir aux schémas du joueur** (3 dernières actions)
- **Gérer les ressources** (PV/PA)
- **Considérer les effets actifs** (buffs/debuffs)
- **Planifier stratégiquement** basé sur les actions disponibles et l'état de combat
