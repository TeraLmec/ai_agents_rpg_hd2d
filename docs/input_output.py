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
  
    # 3 Actions that the player choose to do for each of his turns (each action can have 2 effects).
    "order_1",
    "code_11",
    "multiplier_11",
    "duration_11",
    "code_12",
    "multiplier_12",
    "duration_12",
    
    "order_2",
    "code_21",
    "multiplier_21",
    "duration_21",
    "code_22",
    "multiplier_22",
    "duration_22",

    "order_3",
    "code_31",
    "multiplier_31",
    "duration_31",
    "code_32",
    "multiplier_32",
    "duration_32",
    
    # 4 actifs that defines buffs/debuffs that are being applied in the actual
    
    # AI buff/debuff
    "code_4",
    "multiplier_4",
    "remaining_duration_4",

    "code_5",
    "multiplier_5",
    "remaining_duration_4",
    
    # Player buff/debuff
    "code_6",
    "multiplier_6",
    "remaining_duration_6",

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
    "ply_lvl",
    
    # States of the combat
    "round_count",
    "action_left",
    
    # AI actions that are available.
    
    # We have 4 actions max and 2 actions min (but we will set to 0 the stat corresponding 
    # to the number of action the character has been created with), theses represents the
    # actions that the ai can do, except skip action that it doesnt need to access
    "order_8",
    "code_81",
    "multiplier_81",
    "duration_81",
    "code_82",
    "multiplier_82",
    "duration_82",
    
    "order_9",
    "code_91",
    "multiplier_91",
    "duration_91",
    "code_92",
    "multiplier_92",
    "duration_92",
    
    "order_10",
    "code_101",
    "multiplier_101",
    "duration_101",
    "code_102",
    "multiplier_102",
    "duration_102",
    
    "order_11",
    "code_111",
    "multiplier_111",
    "duration_111",
    "code_112",
    "multiplier_112",
    "duration_112",
    
    # Recent actions that have been taken by the AI(everything will be 0 if the AI is in the first turn)
    "order_12",
    "code_121",
    "multiplier_121",
    "duration_121",
    "code_122",
    "multiplier_122",
    "duration_122",
    
    "order_13",
    "code_131",
    "multiplier_131",
    "duration_131",
    "code_132",
    "multiplier_132",
    "duration_132"
]

ouput_neural_network = [
  
  # The AI will return as ouput the probability distribution of his 5 avalaibles that it can do,
  # (it can be 3, 4 or 5 actions depending of the number of actions that the character that the ai control has been created with)
  "P1",
  "P2",
  "P3",
  "P4",
  "P5"
]

print(len(input_neural_network))