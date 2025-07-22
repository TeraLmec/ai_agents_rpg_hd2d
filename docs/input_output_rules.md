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