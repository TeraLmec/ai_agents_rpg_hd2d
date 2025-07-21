class CombatEntity:
    def __init__(self, id, level, hp, hp_max, ap, ap_max, speed, stats, buffs=None, debuffs=None):
        self.id = id
        self.level = level
        self.hp = hp
        self.hp_max = hp_max
        self.ap = ap
        self.ap_max = ap_max
        self.speed = speed
        self.stats = stats
        self.buffs = buffs or []
        self.debuffs = debuffs or []

    def is_alive(self):
        return self.hp > 0

    def get_modified_stat(self, stat_name):
        value = self.stats[stat_name]
        for buff in self.buffs:
            if stat_name.lower().startswith(buff.code):
                value += value * buff.value
        for debuff in self.debuffs:
            if stat_name.lower().startswith(debuff.code):
                value -= value * debuff.value
        return max(0, int(value))

    def update_effects(self):
        self.buffs = [b for b in self.buffs if b.update_duration()]
        self.debuffs = [d for d in self.debuffs if d.update_duration()]