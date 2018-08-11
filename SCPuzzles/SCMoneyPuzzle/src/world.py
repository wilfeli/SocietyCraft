import core_tools
import agent
import market
import institutions
import geography
import queue



class World():

    human_speed = 10

    
    def __init__(self):
        self.humans = []
        self.firms = []
        self.banks = []
        self.map = geography.Map({})
        self.paymentSystem = institutions.PaymentSystem(self)
        self.government = None
        self._markets = []
        self._markets.append(market.MarketFood(self)) #market for BtoH food from Store to H
        self._markets.append(market.MarketRawFood(self)) #market for BtoB food from Farm to F
        self._markets.append(market.MarketHK(self)) #market for HK contracts
        self._markets.append(market.MarketCredit(self)) #market for Credit contracts
        self.wTime = -1

        self.institutionsQueue = queue.Queue()
        self.logisticQueue = queue.Queue()
        self.lgOrders = []


    def markets(self, name, agent = None):
        for market in self._markets:
            if market.marketType == name:
                return market
        return None



    def Life(self):
        """
        """
        #run for few ticks
        for i in range(256):

            self.wTime += 1
            deltaTime = 1
            #ticks of agents - to do actions and stage decisions
            self.AcTickAgents(deltaTime)
            #go over institutions, including markets
            self.AcTickInstitutions(deltaTime)
            #go over logistic orders
            self.AcTickLogistic(deltaTime)

    def LifeInstitutions(self):
        """
        will become separate thread, where markets match asks and bids and maybe empty queue

        """
        pass


    def AcTickAgents(self, deltaTime):
        """
        Handles all actions during the tick
        """
        
        for h in self.humans:
            #update decisions
            h.AcTick(self.wTime, deltaTime, self)
            #move physical image
            pos = self.IsAtLocation(h.intentions['location'], h.body)
            if not(pos):
                #update location of a body
                h.body.locationX += World.human_speed * (h.intentions['location'][0] - h.body.locationX)
                h.body.locationY += World.human_speed * (h.intentions['location'][1] - h.body.locationY)
            else:
                h.AcIntention()

        for f in self.firms:
            f.AcTick(self.wTime, deltaTime)


    def IsAtLocation(self, location, body):
        """
        """
        #check if it is tuple 
        #if not - GetLocation from an agent
        #
        locationBody = body.GetLocation()
        if locationBody == location:
            return True
        
        return False



    def AcTickInstitutions(self, deltaTime):
        #clear queue of bids and asks for markets for x calls 


        #run matching for markets 
        #markets are run in some order - randomize 


        #guarantee that markets do not need to handle incremental bid/ask updating
        #all bids/asks are cleared after the cycle of matching 
        while not self.institutionsQueue.empty():
            marketOrder = self.institutionsQueue.get()
            #FIXME: add more details on what types of goods want to buy
            if "Food" in marketOrder['id'][0]:
                market = self.markets(core_tools.AgentTypes.MarketRawFood)
                market.GetBidAsk(marketOrder)
            elif "HK" in marketOrder['id'][0]:
                market = self.markets(core_tools.AgentTypes.MarketHK)
                market.GetBidAsk(marketOrder)
            


        #match bids and asks for markets
        for market in self._markets:
            market.AcTick()







    def AcTickLogistic(self, deltaTime):
        """
        """
        #empty queue
        while not (self.logisticQueue.empty()):
            #get LG order
            lgOrder = self.logisticQueue.get()
            #add to active orders
            self.lgOrders.append(lgOrder)
            #start transportation
            lgOrder['TimeTravel'] = 0.0
            lgOrder['status'] = 'InTransit'

        #move cargo one tick
        for lgOrder in self.lgOrders:
            lgOrder['TimeTravel'] += deltaTime
            if lgOrder['TimeTravel'] >= lgOrder['agent'].logistics.params['TimeTravel']:
                lgOrder[('destination', 'agent')].GetLogisticMessage(lgOrder)
                lgOrder['status'] = 'Delivered'

        #remove incactive orders
        def IsInactiveOrder(lgOrder):
            return lgOrder['status'] == 'Delivered'

        self.lgOrders[:] = core_tools.filterfalse(IsInactiveOrder, self.lgOrders)


    def GetMarketMessage(self, mes):
        """
        """
        #marks as active message
        mes['State'] = core_tools.ContractStates.Active
        self.institutionsQueue.put(mes)


    def GetLogisticMessage(self, mes):
        self.logisticQueue.put(mes)