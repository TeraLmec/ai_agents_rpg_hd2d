import json, sys, os
from random import randint, choice
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from fighter_generator.fighter_gen import FighterGen

class fight_simulator:
  def __init__(self):
    self.start = choice([1,2])
    
  def generate_fighters(self):
    FighterGen().generate("player.json","fs2/fighters")
    FighterGen().generate("enemy.json","fs2/fighters")
    
simulator = fight_simulator()
simulator.generate_fighters()