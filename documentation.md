# Combat Rules

### Turn Structure

#### Turn Order

- **Initiative**: The entity with the **higher speed** stat goes first
- **Actions per Turn**: Each entity can perform up to **3 actions** per turn
- **Round Completion**: A round ends when both entities have completed their turns

#### Action Limitations

1. **Action Point (AP) System**:

   - Each action has an **AP cost** (defined in fighter generation)

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

- Actions are selected based on:
  - **Current AP availability**

#### Effect Application

- **Temporary Effects**: Buffs and debuffs track duration and remaining rounds
- **Buff/Debuff Limitation**: Each entity can have **maximum one active buff** and **one active debuff**

### Combat End Conditions

Combat ends when one of the following occurs:

- An entity's **HP drops to 0 or below**

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

# Fighter Generation Rules

### Basic Fighter Statistics

- **Level**: Randomly generated between 1-5
- **Maximum Health Points (HP)**: Random value between 80-120, multiplied by fighter level
- **Current HP**: Initially equal to maximum HP
- **Speed**: Random value between 3-5, plus level bonus
- **Maximum Action Points (AP)**: Base value of 4, plus 1 additional AP for a 5 level entity (max level)
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
   - Effect code: 10 (skip)
   - Multiplier: 0
   - Duration: 1 turn

#### Random Special Actions

- **Quantity**: 1-3 additional actions generated randomly
- **Action Point Cost**: Random between 1-4 AP per action

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

# Neural Network Input/Output Specifications

## INPUT TO NEURAL NETWORK (Total: 92 values)

### **Player Recent Actions (21 values)**

- The 3 most recent player actions (7 values each)

### **Active Buffs/Debuffs (12 values)**

- AI Active Effects (6 values):
- Player Active Effects (6 values):

### **Combat Stats (15 values)**

- AI Stats (12 values):
- Player Stats (3 values):

### **Combat State (2 values)**

- `round_count`: Current round number
- `action_left`: Remaining actions this turn

### **AI Available Actions (28 values)**

- 4 possible actions (7 values each)

**Note**: Unused action slots are set to 0

### **AI Action History (14 values)**

- Last 2 AI actions (7 values each):

**Note**: Same structure as available actions. All 0s if AI hasn't acted yet

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
- The action choosed should be the highest probability
- **Skip action (P5)** is always available regardless of AP cost

## **Decision Context**

The AI receives this complete state information **3 times per round** and must output an action probability distribution each time.

# Example of an entity stat using the fighter generator

```json

{
  "level": 3,
  "hpMax": 312,
  "hp": 312,
  "speed": 8,
  "apMax": 4,
  "ap": 2,
  "actifs": [
    {
      "code": 0,
      "multiplier": 0,
      "duration": 0
    },
    {
      "code": 0,
      "multiplier": 0,
      "duration": 0
    }
  ],
  "stats": {
    "phy_atk": 31,
    "phy_def": 22,
    "spi_atk": 9,
    "spi_def": 9,
    "ele_atk": 0,
    "ele_def": 0
  },
  "actions": [
    {
      "id": 1,
      "cost": 0,
      "effects": [
        {
          "code": 1,
          "multiplier": 2,
          "duration": 1
        },
        {
          "code": 0,
          "multiplier": 0,
          "duration": 0
        }
      ]
    },
    {
      "id": 2,
      "cost": 0,
      "effects": [
        {
          "code": 10,
          "multiplier": 0,
          "duration": 1
        },
        {
          "code": 0,
          "multiplier": 0,
          "duration": 0
        }
      ]
    },
    {
      "id": 3,
      "cost": 4,
      "effects": [
        {
          "code": 2,
          "multiplier": 70,
          "duration": 1
        },
        {
          "code": 5,
          "multiplier": 40,
          "duration": 2
        }
      ]
    },
    {
      "id": 4,
      "cost": 4,
      "effects": [
        {
          "code": 8,
          "multiplier": 70,
          "duration": 1
        },
        {
          "code": 1,
          "multiplier": 70,
          "duration": 1
        }
      ]
    },
    {
      "id": 5,
      "cost": 3,
      "effects": [
        {
          "code": 6,
          "multiplier": 60,
          "duration": 1
        },
        {
          "code": 2,
          "multiplier": 32,
          "duration": 1
        }
      ]
    }
  ]
}

```

# The json that we will receive each turn to read the neural network input data (92 entries)

```json

{
   "ply_recent_actions": [
      {
         "cost": 0,
         "effects": [
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            },
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            }
         ]
      },
      {
         "cost": 0,
         "effects": [
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            },
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            }
         ]
      },
      {
         "cost": 0,
         "effects": [
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            },
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            }
         ]
      }
   ],
   "actives": {
      "ai_active_effects": [
         {
            "code": 0,
            "multiplier": 0,
            "duration": 0
         },
         {
            "code": 0,
            "multiplier": 0,
            "duration": 0
         }
      ],
      "ply_active_effects": [
         {
            "code": 0,
            "multiplier": 0,
            "duration": 0
         },
         {
            "code": 0,
            "multiplier": 0,
            "duration": 0
         }
      ]
   },
   "combat_stats": {
      "ai_stats": {
         "level": 0,
         "hpMax": 0,
         "hp": 0,
         "speed": 0,
         "apMax": 0,
         "ap": 0,
         "stats": {
            "phy_atk": 0,
            "phy_def": 0,
            "spi_atk": 0,
            "spi_def": 0,
            "ele_atk": 0,
            "ele_def": 0
         },
         "ply_stats": {
            "level": 0,
            "hpMax": 0,
            "hp": 0
         }
      }
   },
   "combat_state": {
      "round_count": 0,
      "action_left": 0
   },
   "ai_available_actions": [
      {
         "cost": 0,
         "effects": [
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            },
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            }
         ]
      },
      {
         "cost": 0,
         "effects": [
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            },
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            }
         ]
      },
      {
         "cost": 0,
         "effects": [
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            },
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            }
         ]
      },
      {
         "cost": 0,
         "effects": [
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            },
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            }
         ]
      }
   ],
   "ai_actions_history": [
      {
         "cost": 0,
         "effects": [
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            },
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            }
         ]
      },
      {
         "cost": 0,
         "effects": [
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            },
            {
               "code": 0,
               "multiplier": 0,
               "duration": 0
            }
         ]
      }
   ]
}

```
