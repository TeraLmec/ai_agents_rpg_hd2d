from random import randint, choice
import json, os

class fighter_gen:
  def __init__(self):
    # No pre-generated state. Randomness happens on each generate call.
    pass

  def actions_gen(self):
    
    actions_nbr = randint(1,3)
    actions = [
      {
        "id": 1,
        "cost": 0,
        "effects":[
          {
            "code": randint(1,3),
            "multiplier": randint(2,5),
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
        "effects":[
          {
            "code": 10,
            "multiplier": 0,
            "duration": 1,
          },
          {
            "code": 0,
            "multiplier": 0,
            "duration": 0
          }
        ]
      }
    ]
    
    i = 0
    while i < actions_nbr:
      cost = randint(1,4)
      action = {
        "id": i+3,
        "cost": cost,
        "effects":[]
      }
      proba_list = [1,2,3,4]
      for j in range(min(2,cost)):
        proba_effect = choice(proba_list)
        multiplier = randint(5,15) * (cost + 1)
        if(proba_effect == 1 or proba_effect == 2):
          proba_list.remove(1)
          proba_list.remove(2)
          code = randint(1,3)
          duration = 1
        elif(proba_effect == 3):
          proba_list.remove(3)
          code = randint(4,6)
          duration = cost - int(multiplier / 20)
        else:
          proba_list.remove(4)
          code = randint(7,9)
          duration = cost - int(multiplier / 20)
        duration = max(duration, 1)
        effect = {
            "code": code,
            "multiplier": multiplier,
            "duration": duration
          }
        action["effects"].append(effect)
        if(cost<2):
          action["effects"].append({
            "code": 0,
            "multiplier": 0,
            "duration": 0
            })
      i += 1
      actions.append(action)
      
    return actions
  
  def generate(self, out_filename="generated_enemy.json", out_dir=None):
    fighter_stats = self._build_random_fighter()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = out_dir or os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, out_filename)
    with open(out_path, "w", encoding="utf-8") as f:
      json.dump(fighter_stats, f, indent=2, ensure_ascii=False)

    return fighter_stats

  # -- Helper to build a fresh random fighter dict each call -----------------
  def _build_random_fighter(self, custom_level = randint(1,5)):

    hpmax_randint = randint(80,120)

    # Basic stats
    level = custom_level
    hpmax = int(hpmax_randint + hpmax_randint * (level - 1) * 0.75)
    hp = hpmax
    speed = randint(3,5) + level
    apmax = 4 + int(level / 5)
    ap = 2
    actifs = [
      {"code": 0, "multiplier": 0, "duration": 0},
      {"code": 0, "multiplier": 0, "duration": 0},
    ]

    # Actions
    actions = self.actions_gen()

    # Atk and Def stats - randomly assign roles to phy/spi/ele
    init_stat = 30 * level
    
    # Randomly assign one type as principale, others as neutral/faible
    types = ["phy", "spi", "ele"]
    principale_type = choice(types)
    remaining_types = [t for t in types if t != principale_type]
    neutral_type = choice(remaining_types)
    faible_type = [t for t in remaining_types if t != neutral_type][0]
    
    # Generate stats based on assigned roles
    stats = {}
    for stat_type in types:
      if stat_type == principale_type:
        # Principale: 25-35% of init_stat
        atk_pct = 30 + choice([-5, 5])
        def_pct = 30 + choice([-5, 5])
      elif stat_type == neutral_type:
        # Neutral: 10-20% of init_stat  
        atk_pct = 15 + choice([-5, 5])
        def_pct = 15 + choice([-5, 5])
      else:  # faible_type
        # Faible: 0-10% of init_stat
        atk_pct = 5 + choice([-5, 5])
        def_pct = 5 + choice([-5, 5])
      
      atk_val = int(init_stat * (atk_pct / 100))
      def_val = int(init_stat * (def_pct / 100))
      stats[f"{stat_type}_atk"] = atk_val
      stats[f"{stat_type}_def"] = def_val

    return {
      "level": level,
      "hpMax": hpmax,
      "hp": hp,
      "speed": speed,
      "apMax": apmax,
      "ap": ap,
      "actifs": actifs,
      "stats": stats,
      "actions": actions,
    }

  def generate_dict(self):
    return self._build_random_fighter()