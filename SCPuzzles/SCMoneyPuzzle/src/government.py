import core_tools
import agent


class ResourceBank(agent.Facility):
    def __init__(self, w):
        self.w = w
        self.gs = {}


    def StartStage01(self):
        """
        
        """
        pass




class ManagementG(object):
    """
    """
    def __init__(self, template):
        super().__init__()
        self.params = {}
        self.params["type"] = core_tools.AgentTypes.Government
        self.params["minResourceQ"] = 100.0
        
    def StartStage01(self, agent_):
        self.SetupDecMarket(agent_)


    def SetupDecMarket(self, agent_):
        """
        """
        for resourceID in core_tools.resources:
            #setup decision
            agent_.decisions[("dec", *resourceID, core_tools.FITypes.Ask)] = {"q":0.0, 
                                    "p":core_tools.DEFAULT_P, 
                                    "ask":{"id":resourceID, 
                                    "type":core_tools.FITypes.Ask}}
            agent_.decisions[("dec", *resourceID, core_tools.FITypes.Bid)] = {"q":0.0, 
                                    "p":core_tools.DEFAULT_P, 
                                    "ask":{"id":(*resourceID, agent_.office.island + "W"), 
                                    "type":core_tools.FITypes.Ask}}
            

    def AcMarket(self, agent_):
        """
        """
        #submit ask to the market with seeds in case someone needs it 
        #for all resources on the island for now
        for resourceID in core_tools.resources:
            if self.params["type"] == core_tools.AgentTypes.Government:
                id_ = ("dec", *resourceID, core_tools.FITypes.Ask)
                #returns record about stored goods from inventory 
                gs = agent_.resourceBank[resourceID][core_tools.AgentTypes.Government]
                if id_ in agent_.decisions:
                    dec = agent_.decision[id_]
                    if gs["q"] > 0.0:
                        marketOrder = dec["ask"]
                        #check how much wants to sell and how much can sell
                        marketOrder["q"] = gs["q"]
                        marketOrder["p"] = dec["p"]
                        marketOrder["agent"] = agent_

                        #assume that market discarded old ask
                        agent_.w.GetMarketMessage(marketOrder)

                if gs["q"] <= self.params["minResourceQ"]:
                    marketOrder = dec["bid"]
                    marketOrder["market"] = core_tools.AgentTypes.MarketResourceFoodW
                    marketOrder["q"] = self.params["minResourceQ"] - gs["q"]
                    marketOrder["p"] = dec["p"]
                    marketOrder["agent"] = agent_

                    #assume that market discarded old 
                    agent_.w.GetMarketMessage(marketOrder)

            elif self.params["type"] == core_tools.AgentTypes.GovernmentW:
                #sell on the international market 
                gs = agent_.resourceBank[resourceID][core_tools.AgentTypes.Government]
                if gs["q"] > 0.0:
                    for islandID, island in agent_.w:
                        if islandID != agent_.office.island:
                            marketOrder = {"id":(*resourceID, islandID + "W"), 
                                            "type":core_tools.FITypes.Ask}
                            marketOrder["q"] = gs["q"]
                            marketOrder["p"] = core_tools.DEFAULT_P
                            marketOrder["agent"] = agent_

                            #assume that market discarded old ask
                            agent_.w.GetMarketMessage(marketOrder)

 



class Government(object):
    def __init__(self, template, w_):
        self.w = w_
        self.facilities = []
        self.fi = []
        self.regulations = {}
        self.decisions = {}
        #has ResourceBank as another facility
        self.resourceBank = ResourceBank(w_)
        self.facilities.append(self.resourceBank)

        #has office as a main location 
        self.office = agent.Office(template["office"])
        self.facilities.append(self.office)

        self.management = self.CreateManagement(template)
        

        
    def CreateManagement(self, template):
        return ManagementG(template["management"])



    def StartStage01(self, w_):
        self.management.StartStage01(self)

        #get random bank
        bankID = core_tools.random.randrange(0, len(self.w.banks))
        psMoney = {'type':core_tools.FITypes.PSMoney,
                    'currency':core_tools.ContractTypes.SCMoney,
                    'q':1000.0,
                    'issuer':self.w.banks[bankID]}
        self.fi.append(psMoney)
        self.w.banks[bankID].GetPSContract(psMoney)
        


    def AcTick(self):
        """
        """
        self.management.AcTick(self)
        


    def GetContract(self, data):
        """
        """
        if data["type"] == core_tools.ContractTypes.PropertyContract:
            self.fi.append(data)



    def AcLegalSystem(self):
        """
        """



    def MarketSettleContract(self, q_, ask_, bid_):
        """
        selling of goods from the resourceBank
        """
        #sell good from inventory
        #ROADMAP deliver goods from the Depot, not from the unnamed location 
        #as it is now
        #get first part of id 

        #here if 
        if self.management.params["type"] == core_tools.AgentTypes.GovernmentW:
            #to remove location part of ID that is used for world market 
            id_ = tuple(bid_["id"][0:3])
        elif self.management.params["type"] == core_tools.AgentTypes.Government:
            id_ = bid_["id"]
        gs = self.resourceBank[id_][core_tools.AgentTypes.Government]
        gs["q"] -= q_

        lgOrder = core_tools.copy.deepcopy(bid_.copy)
        #change agent to self from the buyer that was in the bid
        lgOrder["agent"] = self
        #update quantity
        lgOrder["q"] = q_ 
        #update destination
        if ("destination", "location") in bid_:
            lgOrder[("destination", "location")] = bid_[("destination", "location")]
        else:
            lgOrder[("destination", "location")] = bid_["agent"]
        lgOrder[("destination", "agent")] = bid_["agent"]
        #send into world logistics
        self.w.GetLogisticMessage(lgOrder)
        #inform buyer that has goods coming 
        bid_["agent"].signalQueue.put((core_tools.SimulSignals.MarketClearBid, q_, bid_["id"]))