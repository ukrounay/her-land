import numpy as np

class vec2:
    x: float
    y: float
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, multiplier):
        if isinstance(multiplier, vec2):
            return vec2(self.x * multiplier.x, self.y * multiplier.y)
        return vec2(self.x * multiplier, self.y * multiplier)
    
    def __div__(self, multiplier):
        if isinstance(multiplier, vec2):
            return vec2(self.x / multiplier.x, self.y / multiplier.y)
        return vec2(self.x / multiplier, self.y / multiplier)
    def __truediv__(self, multiplier):
        if isinstance(multiplier, vec2):
            return vec2(self.x / multiplier.x, self.y / multiplier.y)
        return vec2(self.x / multiplier, self.y / multiplier)

    def length(self):
        return np.sqrt(self.x ** 2 + self.y ** 2)

    def normalized(self):
        length = self.length()
        if length > 0:
            return vec2(self.x / length, self.y / length)
        return vec2()
    
    def __str__(self) -> str:
        return f"{self.x}, {self.y}"
    
    def copy(self):
        return vec2(self.x, self.y)

class vec2i:
    x: int
    y: int
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, multiplier):
        if isinstance(multiplier, vec2):
            return vec2(self.x * multiplier.x, self.y * multiplier.y)
        return vec2(self.x * multiplier, self.y * multiplier)

    def length(self):
        return np.sqrt(self.x ** 2 + self.y ** 2)

    def normalized(self):
        length = self.length()
        if length > 0:
            return vec2(self.x / length, self.y / length)
        return vec2()
    
    def __str__(self) -> str:
        return f"{self.x}, {self.y}"
    
    def from_vec2(vec):
        return vec2i(int(vec.x), int(vec.y))