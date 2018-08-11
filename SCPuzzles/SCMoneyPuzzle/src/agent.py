

class Agent(object):
    pass

class Building(object):
    def __init__(self):
        self.locationX = 0.0
        self.locationY = 0.0
        self.params = {}

    def GetLocation(self):
        return self.locationX, self.locationY


class Facility(Building):
    pass

class Residence(Building):
    def __init__(self):
        super().__init__()