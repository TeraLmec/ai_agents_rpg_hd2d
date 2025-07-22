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

   - Each action has an **AP cost** (defined in fighter generation)
   - When an entity runs out of AP, their turn **ends immediately**
   - Remaining actions are forfeited if AP is insufficient

2. **Special Effect Limitation**:

   - If an entity uses an action with effect codes **4-9** (buffs/debuffs/special effects), their turn **ends immediately**
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

- Each entity can choose from their **generated action set** (see fighter_rules.md)
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

   - Chaque action a un **coût en PA** (défini dans la génération de combattant)
   - Quand une entité n'a plus de PA, son tour **se termine immédiatement**
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

- Chaque entité peut choisir parmi son **ensemble d'actions générées** (voir fighter_rules.md)
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
