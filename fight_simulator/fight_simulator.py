import json, sys, os
from random import randint, choice
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from fighter_generator.fighter_gen import fighter_gen

class fight_simulator:
    
  def generate_fighters(self):
    fighter_gen().generate("player.json","fs2/fighters")
    fighter_gen().generate("enemy.json","fs2/fighters")
    
simulator = fight_simulator()
simulator.generate_fighters()