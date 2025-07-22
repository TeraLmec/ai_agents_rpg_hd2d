import json

class InputDataCreator:
    def __init__(self):
        self.level = 0
        self.hp_max = 0
        self.hp = 0
        self.speed = 0
        self.ap_max = 0
        self.ap = 0
        self.actifs = []
        self.stats = {}
        self.actions = []
        self.enemy_level = 0
        self.enemy_hp_max = 0
        self.enemy_hp = 0
        self.enemy_actifs = []
    
    def read_my_data(self, file_path: str) -> list:
          
      with open(file_path, 'r', encoding='utf-8') as file:
          data = json.load(file)
      
      self.level = data.get('level', 0)
      self.hp_max = data.get('hpMax', 0)
      self.hp = data.get('hp', 0)
      self.speed = data.get('speed', 0)
      self.ap_max = data.get('apMax', 0)
      self.ap = data.get('ap', 0)
      self.actifs = data.get('actifs', [])
      self.stats = data.get('stats', {})
      self.actions = data.get('actions', [])
      
      my_data = [self.level, self.hp_max, self.hp, self.speed, self.ap_max, self.ap]
      
      # Add AI actifs buffs/debuffs to the data
      for actif in self.actifs:
        for key in actif:
          my_data.append(actif[key])
      
      # Add AI stats
      for key in self.stats:
        my_data.append(self.stats[key])
      
      # Add AI actions
      for action in self.actions:
        if action["id"] != 2:
          my_data.append(action["cost"])
          for effect in action["effects"]:
            for key in effect:
              my_data.append(effect[key])
      
      return my_data
      
    def read_enemy_data(self, file_path: str) -> list:
          
      with open(file_path, 'r', encoding='utf-8') as file:
          data = json.load(file)
      
      self.enemy_level = data.get('level', 0)
      self.enemy_hp_max = data.get('hpMax', 0)
      self.enemy_hp = data.get('hp', 0)
      self.enemy_actifs = data.get('actifs', [])
      
      enemy_data = [self.enemy_level, self.enemy_hp_max, self.enemy_hp]
      
      # Add Enemy actifs buffs/debuffs to the data
      for actif in self.enemy_actifs:
        for key in actif:
          enemy_data.append(actif[key])
      
      return enemy_data
    
    def read_other_data(self, combat_log_path: str, my_recent_actions_path: str) -> list:
      
      # Read combat_log.json
      with open(combat_log_path, 'r', encoding='utf-8') as file:
          combat_log = json.load(file)
          
      combat_log_list = []
      for key in combat_log:
        combat_log_list.append(combat_log[key])
          
      # Read my_recent_actions.json
      with open(my_recent_actions_path, 'r', encoding='utf-8') as file:
          my_recent_actions = json.load(file)
          
      my_recent_actions_list = []
      for key in my_recent_actions:
        my_recent_actions_list.append(my_recent_actions[key])
      
      return combat_log_list + my_recent_actions_list
    
    def merged_input_data(self):
      result = self.read_my_data(file_path="fight_simulator/fighters/1.json") + self.read_enemy_data(file_path="fight_simulator/fighters/2.json") + self.read_other_data(combat_log_path="fight_simulator/data/combat_log.json", my_recent_actions_path="fight_simulator/data/my_recent_actions.json")
      print(len(result))
      print(result)
      return result
    
    def create_json_file(self, output_path: str):
      input_data = {
          "level": self.level,
          "hpMax": self.hp_max,
          "hp": self.hp,
          "speed": self.speed,
          "apMax": self.ap_max,
          "ap": self.ap,
          "actifs": self.actifs,
          "stats": self.stats,
          "actions": self.actions
      }
      
      with open(output_path, "w", encoding="utf-8") as f:
        json.dump(input_data, f, indent=2, ensure_ascii=False)
      
      print(input_data)

if __name__ == "__main__":
  I_creator = InputDataCreator()
  I_creator.merged_input_data()
  
  