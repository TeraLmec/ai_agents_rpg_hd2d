from random import randint

class fighter_gen:
  def __init__(self):
    self.level = randint(1,5)
    self.hpmax = randint(80,120)*self.level
    self.hp = self.hpmax