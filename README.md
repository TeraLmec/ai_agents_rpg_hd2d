# AI Agents RPG HD2D - Combat System Documentation

This repository contains a turn-based RPG combat system featuring AI agents with neural network decision-making capabilities. The system includes fighter generation, combat simulation, and neural network input/output specifications.

---

# Combat Rules / Règles de Combat

## English Version

### Combat Overview

The game is a turn-based RPG featuring 1v1 combat between two entities (AI and Player). Each combat follows structured rules for turn order, actions, and round progression.

### Turn Structure

#### Turn Order

- **Initiative**: The entity with the **higher speed** stat goes first
- **Actions per Turn**: Each entity can perform up to **3 actions** per turn
- **Round Completion**: A round ends when both entities have completed their turns

#### Action Limitations

1. **Action Point (AP) System**:

   - Each action has an **AP cost** except the action of 0 ap that every entity have and the skip action (defined in fighter generation)

2. **Special Effect Limitation**:

   - If an entity uses an action with effect codes **4-9** (buffs/debuffs), their turn **ends immediately**
   - This applies regardless of remaining actions or AP

3. **Skip Action**:
   - Every entity has access to a **skip action** with effect code **10**
   - Skip action is always available and costs **0 AP**

### Round Progression

#### AP Recovery

- At the **end of each round**, both entities recover **1 AP**
- AP cannot exceed the entity's maximum AP limit

#### Combat State Tracking

- **Round counter** increments after both entities complete their turns
- **Action counter** tracks remaining actions for the current entity's turn

### Effect Management

#### Buff and Debuff Limitations

- **Maximum Effects**: Each entity can have at most **one active buff** and **one active debuff** simultaneously
- **Effect Categories**:
  - **Buffs**: Effect codes 4-6 (attack enhancement, defense enhancement, healing)
  - **Debuffs**: Effect codes 7-9 (stun, poison, intimidation)
- **Replacement Rule**: When applying a new buff/debuff to an entity that already has one of that category:
  - The **new effect completely replaces** the existing one
  - Previous effect duration and multiplier are **discarded**
  - New effect starts with **full duration** and **new multiplier**

### Action Resolution

#### Available Actions

- Each entity can choose from their **generated action set** (see Fighter Generation Rules)
- Actions are selected based on:
  - **Current AP availability**
  - **Strategic considerations**
  - **Effect codes and multipliers**

#### Effect Application

- **Immediate Effects**: Damage and healing apply instantly
- **Temporary Effects**: Buffs and debuffs track duration and remaining rounds
- **Buff/Debuff Limitation**: Each entity can have **maximum one active buff** and **one active debuff**
- **Effect Replacement**: When a new buff/debuff is applied to an entity that already has one of that type, the **new effect replaces the old one** completely

### Combat End Conditions

Combat ends when one of the following occurs:

- An entity's **HP drops to 0 or below**
- **Maximum round limit** is reached (if implemented)
- **Forfeit condition** is met (if applicable)

### Effect Code Reference

#### Attack Effects (Codes 1-3)

- **Code 1**: Physical attack (uses higher_atk vs higher_def)
- **Code 2**: Elemental attack (uses neutral_atk vs neutral_def)
- **Code 3**: Spiritual attack (uses lower_atk vs lower_def)

#### Buff Effects (Codes 4-6)

- **Code 4**: Attack stat enhancement
- **Code 5**: Defense stat enhancement
- **Code 6**: HP restoration (healing)

#### Debuff Effects (Codes 7-9)

- **Code 7**: Stun effect (causes opponent to skip turns)
- **Code 8**: Poison effect (deals damage over time)
- **Code 9**: Intimidation (reduces opponent's attack/defense stats)

#### Special Actions

- **Code 10**: Skip turn

### Strategic Considerations

#### Turn Management

- **Early Turn Advantage**: Higher speed entities can set the combat pace
- **AP Conservation**: Managing AP for powerful late-turn actions
- **Effect Timing**: Strategic use of buffs/debuffs to maximize impact

#### Action Economy

- **Maximum Actions**: Using all 3 actions when possible
- **Effect Trade-offs**: Choosing between multiple weak actions vs. one powerful action
- **Turn Ending Effects**: Strategic use of codes 4-9 to end turn after significant impact

---

## Version Française

### Aperçu du Combat

Le jeu est un RPG au tour par tour mettant en scène un combat 1v1 entre deux entités (IA et Joueur). Chaque combat suit des règles structurées pour l'ordre des tours, les actions et la progression des rounds.

### Structure des Tours

#### Ordre des Tours

- **Initiative**: L'entité avec la statistique de **vitesse la plus élevée** joue en premier
- **Actions par Tour**: Chaque entité peut effectuer jusqu'à **3 actions** par tour
- **Fin de Round**: Un round se termine quand les deux entités ont terminé leurs tours

#### Limitations d'Actions

1. **Système de Points d'Action (PA)**:

   - Chaque action a un **coût en PA** excepté l'action qui est une attaque à 0 PA et le SKIP (défini dans la génération de combattant)
   - Les actions restantes sont perdues si les PA sont insuffisants

2. **Limitation d'Effets Spéciaux**:

   - Si une entité utilise une action avec les codes d'effet **4-9** (buffs/debuffs/effets spéciaux), son tour **se termine immédiatement**
   - Ceci s'applique indépendamment des actions ou PA restants

3. **Action Skip**:
   - Chaque entité a accès à une **action skip** avec le code d'effet **10**
   - L'action skip est toujours disponible et coûte **0 PA**

### Progression des Rounds

#### Récupération de PA

- À la **fin de chaque round**, les deux entités récupèrent **1 PA**
- Les PA ne peuvent pas dépasser la limite maximale de l'entité

#### Suivi de l'État de Combat

- Le **compteur de rounds** s'incrémente après que les deux entités aient terminé leurs tours
- Le **compteur d'actions** suit les actions restantes pour le tour de l'entité actuelle

### Gestion des Effets

#### Limitations des Buffs et Debuffs

- **Effets Maximum**: Chaque entité peut avoir au maximum **un buff actif** et **un debuff actif** simultanément
- **Catégories d'Effets**:
  - **Buffs**: Codes d'effet 4-6 (amélioration d'attaque, amélioration de défense, soin)
  - **Debuffs**: Codes d'effet 7-9 (étourdissement, poison, intimidation)
- **Règle de Remplacement**: Lors de l'application d'un nouveau buff/debuff à une entité qui en a déjà un de cette catégorie:
  - Le **nouvel effet remplace complètement** l'existant
  - La durée et le multiplicateur de l'effet précédent sont **supprimés**
  - Le nouvel effet commence avec la **durée complète** et le **nouveau multiplicateur**

### Résolution d'Actions

#### Actions Disponibles

- Chaque entité peut choisir parmi son **ensemble d'actions générées** (voir Règles de Génération des Combattants)
- Les actions sont sélectionnées selon:
  - **Disponibilité actuelle des PA**
  - **Considérations stratégiques**
  - **Codes d'effet et multiplicateurs**

#### Application des Effets

- **Effets Immédiats**: Les dégâts et soins s'appliquent instantanément
- **Effets Temporaires**: Les buffs et debuffs suivent la durée et les rounds restants
- **Limitation Buff/Debuff**: Chaque entité peut avoir **maximum un buff actif** et **un debuff actif**
- **Remplacement d'Effet**: Quand un nouveau buff/debuff est appliqué à une entité qui en a déjà un de ce type, le **nouvel effet remplace complètement l'ancien**

### Conditions de Fin de Combat

Le combat se termine quand une des conditions suivantes survient:

- Les **PV d'une entité tombent à 0 ou moins**
- La **limite maximale de rounds** est atteinte (si implémentée)
- Une **condition d'abandon** est remplie (si applicable)

### Référence des Codes d'Effet

#### Effets d'Attaque (Codes 1-3)

- **Code 1**: Attaque physique (utilise higher_atk vs higher_def)
- **Code 2**: Attaque élémentaire (utilise neutral_atk vs neutral_def)
- **Code 3**: Attaque spirituelle (utilise lower_atk vs lower_def)

#### Effets de Buff (Codes 4-6)

- **Code 4**: Amélioration des statistiques d'attaque
- **Code 5**: Amélioration des statistiques de défense
- **Code 6**: Restauration de PV (soin)

#### Effets de Debuff (Codes 7-9)

- **Code 7**: Effet d'étourdissement (fait passer le tour à l'adversaire)
- **Code 8**: Effet de poison (inflige des dégâts dans le temps)
- **Code 9**: Intimidation (réduit les stats d'attaque/défense de l'adversaire)

#### Actions Spéciales

- **Code 10**: Passer son tour (position défensive, peut apporter des avantages mineurs)

### Considérations Stratégiques

#### Gestion des Tours

- **Avantage du Premier Tour**: Les entités avec vitesse élevée peuvent définir le rythme du combat
- **Conservation des PA**: Gérer les PA pour des actions puissantes en fin de tour
- **Timing des Effets**: Utilisation stratégique des buffs/debuffs pour maximiser l'impact

#### Économie d'Actions

- **Actions Maximales**: Utiliser les 3 actions quand possible
- **Compromis d'Effets**: Choisir entre plusieurs actions faibles vs. une action puissante
- **Effets de Fin de Tour**: Utilisation stratégique des codes 4-9 pour terminer le tour après un impact significatif

---

# Fighter Generation Rules / Règles de génération des combattants

## English Version

### Basic Fighter Statistics

- **Level**: Randomly generated between 1-5
- **Maximum Health Points (HP)**: Random value between 80-120, multiplied by fighter level
- **Current HP**: Initially equal to maximum HP
- **Speed**: Random value between 3-5, plus level bonus
- **Maximum Action Points (AP)**: Base value of 4, plus 1 additional AP for every 5 levels
- **Starting AP**: Always begins with 2 AP
- **Active Effects**: Two reserved slots for temporary effects (initially empty)

### Combat Statistics Calculation

- **Base Stat Formula**: 30 × fighter level
- **Stat Distribution**:
  - **Primary Attack/Defense**: 30% of base stat (±5% variation)
  - **Neutral Attack/Defense**: 15% of base stat (±5% variation)
  - **Weak Attack/Defense**: 5% of base stat (±5% variation)

### Action Generation System

#### Default Actions (Always Available)

1. **Basic Attack** (ID: 1, Cost: 0 AP)

   - Effect code: Random between 1-3
   - Damage multiplier: Random between 2-5
   - Duration: 1 turn

2. **Skip** (ID: 2, Cost: 0 AP)
   - Effect code: 10 (defense boost)
   - Multiplier: 0
   - Duration: 1 turn

#### Random Special Actions

- **Quantity**: 1-3 additional actions generated randomly
- **Action Point Cost**: Random between 1-4 AP per action
- **Effects per Action**: Maximum 2 effects (limited by AP cost)

#### Effect Generation Rules

Effects are generated based on probability groups:

**Group 1 & 2 (Offensive Effects)**:

- Effect codes: 1-3
- Duration: 1 turn
- Cannot be repeated within the same action

**Group 3 (Buff/Debuff Effects)**:

- Effect codes: 4-6
- Duration: AP cost - (multiplier ÷ 20)

**Group 4 (Special Effects)**:

- Effect codes: 7-9
- Duration: AP cost - (multiplier ÷ 20)

#### Multiplier Scaling

- **Formula**: (Random 5-15) × (AP cost + 1)
- Higher cost actions have proportionally stronger effects

#### Duration Rules

- **Minimum Duration**: All effects last at least 1 turn
- **Duration Calculation**: Based on AP cost minus scaled multiplier
- **Low-Cost Padding**: Actions costing less than 2 AP receive an empty effect slot

### Special Generation Rules

- Each probability group can only be selected once per action
- All statistics are rounded to integers
- Duration is enforced to minimum 1 turn regardless of calculation
- Two "actifs" (active effects) slots are reserved for runtime effects

---

## Version Française

### Statistiques de Base du Combattant

- **Niveau**: Généré aléatoirement entre 1-5
- **Points de Vie Maximum (PV)**: Valeur aléatoire entre 80-120, multipliée par le niveau du combattant
- **PV Actuels**: Initialement égaux aux PV maximum
- **Vitesse**: Valeur aléatoire entre 3-5, plus bonus de niveau
- **Points d'Action Maximum (PA)**: Valeur de base de 4, plus 1 PA supplémentaire tous les 5 niveaux
- **PA de Départ**: Commence toujours avec 2 PA
- **Effets Actifs**: Deux emplacements réservés pour les effets temporaires (initialement vides)

### Calcul des Statistiques de Combat

- **Formule de Stat de Base**: 30 × niveau du combattant
- **Répartition des Stats**:
  - **Attaque/Défense Principale**: 30% de la stat de base (±5% de variation)
  - **Attaque/Défense Neutre**: 15% de la stat de base (±5% de variation)
  - **Attaque/Défense Faible**: 5% de la stat de base (±5% de variation)

### Système de Génération d'Actions

#### Actions par Défaut (Toujours Disponibles)

1. **Attaque de Base** (ID: 1, Coût: 0 PA)

   - Code d'effet: 1-3 (dépend de la stat d'attaque principale de l'entité)
   - Multiplicateur de dégâts: Aléatoire entre 2-5
   - Durée: 1 tour

2. **Skip** (ID: 2, Coût: 0 PA)
   - Code d'effet: 10
   - Durée: 1 tour

#### Actions Spéciales Aléatoires

- **Quantité**: 1-3 actions supplémentaires générées aléatoirement
- **Coût en Points d'Action**: Aléatoire entre 1-4 PA par action
- **Effets par Action**: Maximum 2 effets (limité par le coût en PA)

#### Règles de Génération d'Effets

Les effets sont générés selon des groupes de probabilité:

**Groupe 1 & 2 (Effets Offensifs)**:

- Codes d'effet: 1-3
- Durée: 1 tour
- Ne peuvent pas être répétés dans la même action

**Groupe 3 (Effets de Buff)**:

- Codes d'effet: 4-6
- Durée: Coût PA - (multiplicateur ÷ 20)
- Ne peuvent pas être répétés dans la même action

**Groupe 4 (Effets de Debuff)**:

- Codes d'effet: 7-9
- Durée: Coût PA - (multiplicateur ÷ 20)
- Ne peuvent pas être répétés dans la même action

#### Mise à l'Échelle du Multiplicateur

- **Formule**: (Aléatoire 5-15) × (coût PA + 1)
- Les actions plus coûteuses ont des effets proportionnellement plus forts

#### Règles de Durée

- **Durée Minimum**: Tous les effets durent au moins 1 tour
- **Calcul de Durée**: Basé sur le coût PA moins le multiplicateur mis à l'échelle
- **Remplissage Faible Coût**: Les actions coûtant moins de 2 PA reçoivent un emplacement d'effet vide

### Règles Spéciales de Génération

- Chaque probabilité ne peut être sélectionné qu'une fois par action
- Toutes les statistiques sont arrondies à des entiers
- La durée est forcée à minimum 1 tour indépendamment du calcul
- Deux emplacements "actifs" (effets actifs) sont réservés pour les effets d'exécution

---

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

---

## Project Structure

- **`fighter_generator/`**: Contains the fighter generation system
- **`fight_simulator/`**: Contains the combat simulation engine
- **`ai/`**: Contains AI-related components for neural network decision making
- **Individual rule files**: `combat_rules.md`, `fighter_rules.md`, `input_output_rules.md` (maintained for reference)
