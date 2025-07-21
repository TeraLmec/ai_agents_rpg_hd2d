class Effect:
    def __init__(self, code, value, duration):
        self.code = code
        self.value = value
        self.duration = duration

    def update_duration(self):
        self.duration -= 1
        return self.duration > 0

    def __repr__(self):
        return f"Effect({self.code}, {self.value}, {self.duration})"