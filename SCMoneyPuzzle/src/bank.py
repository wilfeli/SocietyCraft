import agent

class Bank(agent.Agent):

    def __init__(self, template, w):
        #what financial instruments has
        self.fi = []


    def GetPSContract(self, contract):
        self.fi.append(contract)