input_neural_network = [
    # code: define the type of the action.
    # If code equals to:
    # - 1: physical attack
    # - 2: elemental attack
    # - 3: spiritual attack
    # - 4: buff attack
    # - 5: buff defense
    # - 6: buff PV (heal)
    # - 7: debuff stunt (make the adversary of the AI skip his turn)
    # - 8: debuff poison
    # - 9: debuff intimidation (reduce the atk and def of the AI's adversary)
    # - 99: skip his turn
    
    # order: the order on wich the action have been played by the adversary.
    # multiplier: Used along with attack and defense stats to be applied.
    # duration: the number of round that it will be applied.
    
    # remaining_duration: the number of round that the buff/debuff will be applied.
  
    # 3 Actions that the player choose to do for each of his turns.
    "code_1",
    "order_1",
    "multiplier_1",
    "duration_1",
    
    "code_2",
    "order_2",
    "multiplier_2",
    "duration_2",

    "code_3",
    "order_3",
    "multiplier_3",
    "duration_3",
    
    # 4 actifs that defines buffs/debuffs that are being applied in the actual
    
    # AI buffs/debuffs
    "code_4",
    "multiplier_4",
    "remaining_duration_4"

    "code_5",
    "multiplier_5",
    "remaining_duration_4"
    
    # Player buffs/debuffs
    "code_6",
    "multiplier_6",
    "remaining_duration_6"

    "code_7",
    "multiplier_7",
    "remaining_duration_7",
    
    # The States
    # States of the AI
    # Level for the AI level, who impact differents stats like hp, speed, ap or atk and defense
    # Hp max is the maximum HP of the ai
    # Hp is actual hp of the AI if is 0 the ai is dead and loose
    # Speed is the order for the fight, the higher begin
    # AP Max is the maximum of ap stackable for the AI
    # AP is actual action point available for the AI
    # all _atk is the value of the stats in differents type of attack : physcial, elementary or spiritual 
    # all _def is the value of the stats in differents type of defense : physcial, elementary or spiritual 
    
    "ai_lvl",
    "ai_hpmax",
    "ai_hp",
    "ai_speed",
    "ai_apmax",
    "ai_ap",
    "ai_higher_atk",
    "ai_higher_def",
    "ai_neutral_atk",
    "ai_neutral_def",
    "ai_lower_atk",
    "ai_lower_def",
    
    # States of the Player
    "ply_hpmax",
    "ply_hp",
    "ply_lvl"
    
    # States of the combat
    "round_count",
    "action_left",
    
    # AI actions that are available.
    
    # We will consider 4 actions avalaible for now but basically
    # the number of actions that the ai could do wil reduce or add at
    # the number of available inputs and influence the numbers of outputs too,
    # so later we will need to do 2 others models one for 2 actions and one
    # for 3 actions.
    "code_8",
    "order_8",
    "multiplier_8",
    "duration_8",
    
    "code_9",
    "order_9",
    "multiplier_9",
    "duration_9",
    
    "code_10",
    "order_10",
    "multiplier_10",
    "duration_10",
    
    "code_11",
    "order_11",
    "multiplier_11",
    "duration_11",
    
    # Recent actions that have been taken by the AI(everything will be 0 if the AI is in the first turn)
    "code_12",
    "order_12",
    "multiplier_12",
    "duration_12",
    
    "code_13",
    "order_13",
    "multiplier_13",
    "duration_13",
  
]

ouput_neural_network = [
  
  # The AI will return as ouput the probability distribution of his 5 avalaible actions to do, 
  # one of them is a skip, another one is a 0 ap_cost attack and the other 3 can be attack, buff, debuff.
  # P1, P2, P3, P4 and P5 represent each a probabilty (higher or lower) of response to the probleme given to the AI
  "P1",
  "P2",
  "P3",
  "P4",
  "P5"
]

print(len(input_neural_network))