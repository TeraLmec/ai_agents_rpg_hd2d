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

   - Code d'effet: Aléatoire entre 1-3
   - Multiplicateur de dégâts: Aléatoire entre 2-5
   - Durée: 1 tour

2. **Skip** (ID: 2, Coût: 0 PA)
   - Code d'effet: 10 (boost de défense)
   - Multiplicateur: 0
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

**Groupe 3 (Effets de Buff/Debuff)**:

- Codes d'effet: 4-6
- Durée: Coût PA - (multiplicateur ÷ 20)

**Groupe 4 (Effets Spéciaux)**:

- Codes d'effet: 7-9
- Durée: Coût PA - (multiplicateur ÷ 20)

#### Mise à l'Échelle du Multiplicateur

- **Formule**: (Aléatoire 5-15) × (coût PA + 1)
- Les actions plus coûteuses ont des effets proportionnellement plus forts

#### Règles de Durée

- **Durée Minimum**: Tous les effets durent au moins 1 tour
- **Calcul de Durée**: Basé sur le coût PA moins le multiplicateur mis à l'échelle
- **Remplissage Faible Coût**: Les actions coûtant moins de 2 PA reçoivent un emplacement d'effet vide

### Règles Spéciales de Génération

- Chaque groupe de probabilité ne peut être sélectionné qu'une fois par action
- Toutes les statistiques sont arrondies à des entiers
- La durée est forcée à minimum 1 tour indépendamment du calcul
- Deux emplacements "actifs" (effets actifs) sont réservés pour les effets d'exécution