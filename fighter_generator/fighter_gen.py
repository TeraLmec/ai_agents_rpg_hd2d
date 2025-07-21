from random import randint, choice
import json

class fighter_gen:
  def __init__(self):
    # Basic stats
    self.level = randint(1,5)
    self.hpmax = randint(80,120) * self.level
    self.hp = self.hpmax
    self.speed = randint(3,5) + self.level
    self.apmax = 4 + int(self.level / 5)
    self.ap = 2
    self.actifs = [
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
    self.actions =  self.actions_gen()
    
    # Atk and Def stats
    init_stat = 30 * self.level
    self.stats = [
      int(init_stat * ((30 + choice([-5, 5]))/100)),
      int(init_stat * ((30 + choice([-5, 5]))/100)),
      int(init_stat * ((15 + choice([-5, 5]))/100)),
      int(init_stat * ((15 + choice([-5, 5]))/100)),
      int(init_stat * ((5 + choice([-5, 5]))/100)),
      int(init_stat * ((5 + choice([-5, 5]))/100))
    ]
      
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
  
  def generate(self):
    fighter_stats = {
      "level": self.level,
      "hpMax": self.hpmax,
      "hp": self.hp,
      "speed": self.speed,
      "apMax": self.apmax,
      "ap": self.ap,
      "actifs": self.actifs,
      "stats": {
        "principale atk": self.stats[0], 
        "principale def": self.stats[1],
        "neutre atk": self.stats[2],
        "neutre def": self.stats[3],
        "faible atk": self.stats[4],
        "faible def": self.stats[5],
      },
      "actions": self.actions
    }
    
    with open("fighter.json", "w") as f:
      json.dump(fighter_stats, f, indent=2)
      
fighter = fighter_gen()
fighter.generate()