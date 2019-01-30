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
        self.simulParameters = {
            "FrequencyAcTickUI":core_tools.WTime.N_TICKS_DAY,
            "DeathAgeHuman":core_tools.WTime.N_TOTAL_TICKS_YEAR
        }
        self._markets = []
        self._markets.append(market.MarketFinalFood(self)) #market for BtoH food from Store to H
        self._markets.append(market.MarketIntermediateFood(self)) #market for BtoB food from Farm to F
        self._markets.append(market.MarketRawFood(self)) #market for BtoB seeds for growing
        self._markets.append(market.MarketHK(self)) #market for HK contracts
        self._markets.append(market.MarketCredit(self)) #market for Credit contracts
        self.wTime = -1
        self.counterUI = core_tools.WTime.N_TICKS_DAY
        self.templates = {}


        self.institutionsQueue = queue.Queue()
        self.logisticQueue = queue.Queue()
        self.tickQueue = queue.Queue()
        self.dataQueue = queue.Queue()
        self.signalQueue = queue.Queue()
        self.lgOrders = []


    def markets(self, name, agent = None):
        for market in self._markets:
            if market.marketType == name:
                return market
        return None


    def SetUI(self, ui_):
        """
        """
        self.ui = ui_

    def Life(self):
        while not self.tickQueue.empty():
            self.tickQueue.get()
            self.AcTick()
            self.counterUI -= 1.0 
            if self.counterUI <= 0.0:
                self.AcTickUI()
                #TODO 
                self.counterUI = self.simulParameters["FrequencyAcTickUI"]


    def AcTick(self):
        self.wTime += 1
        deltaTime = 1
        #ticks of agents - to do actions and stage decisions
        self.AcTickAgents(deltaTime)
        #go over institutions, including markets
        self.AcTickInstitutions(deltaTime)
        #go over logistic orders
        self.AcTickLogistic(deltaTime)



    @core_tools.deprecated
    def LifeDebug(self, N_SIMUL_TICKS = 256):
        """
        """
        #run for few ticks
        for i in range(N_SIMUL_TICKS):
            self.AcTick()



    def LifeInstitutions(self):
        """
        will become separate thread, where markets match asks and bids and maybe empty queue

        """
        pass


    def AcTickAgents(self, deltaTime):
        """
        Handles all actions during the tick


        Order of ticking is H always goes first to setup its decisions 
        #FIXME F, B, G, CB order to be determined 

        """
        
        for h in self.humans:

            if h.body.params["Age"] > self.simulParameters["DeathAgeHuman"]:
                #have 10% chance of dying 
                p = core_tools.random.uniform(0, 1)
                if p < self.simulParameters["ProbabilityDeathHuman"]:
                    h.body.state = core_tools.AgentStates.Dead

            if h.body.state != core_tools.AgentStates.Dead:

                #update decisions
                h.AcTick(self.wTime, deltaTime, self)

                ####################################################
                #move will be handled by the UE4 engine 
                #actions are taken by agents themselves if they are triggered by being at the location
                #there is a bit of lag before arriving and doing something there
                #but agents plan for that 

                #move physical image
                pos = self.IsAtLocation(h.intentions['location'], h.body)
                if not(pos):
                    #update location of a body
                    h.body.locationX += World.human_speed * (h.intentions['location'][0] - h.body.locationX)
                    h.body.locationY += World.human_speed * (h.intentions['location'][1] - h.body.locationY)
                else:
                    h.AcIntention()
                ####################################################
            else:
                self.DeathHuman(h)
                self.signalQueue.put(core_tools.SimulSignals.CreateHuman)
                

        self.humans = [agent_ for agent_ in self.humans if h.body.state != core_tools.AgentStates.Dead]

        for f in self.firms:
            f.AcTick(self.wTime, deltaTime)


    def DeathHuman(self, h):
        """
        """
        #pick F at random 
        def IsManagingFirm(agent_):
            return "ManagementBtoH" in type(agent_.management).__name__
        
        building = h.residence
        firms = [firm for firm in w.firms if IsManagingFirm(firm)]
        randomNumber = random.randrange(0, len(firms))

        #pass property to some firm
        firms[randomNumber].facilities.append(building)
        building.params['PropertyRights'] = firms[randomNumber]

        #remove all contracts
        for contract in h.fi:
            if contract["type"] == core_tools.ContractTypes.CreditContract:
                contract["issuer"].ReceiveMessageLS(contract) 
                contract["PSTransaction"] = True
        #FIXME incomplete handle of contracts

        


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


    def IsEAtLocation(self, location, agent):
        """
        if wants to be at location generally in this tick
        """
        #check if it is tuple 
        #if not - GetLocation from an agent
        #
        locationGhost = agent.intentions["location"]
        if locationGhost == location:
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
                market = self.markets(core_tools.AgentTypes.MarketIntermediateFood)
                market.GetBidAsk(marketOrder)
            elif "HK" in marketOrder['id'][0]:
                market = self.markets(core_tools.AgentTypes.MarketHK)
                market.GetBidAsk(marketOrder)
            elif "FI" in marketOrder['id'][0] and "credit" in marketOrder['id'][1]:
                market = self.markets(core_tools.AgentTypes.MarketCredit)
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



    def AcTickUI(self):
        """
        """
        data = {}
        for agent_ in self.banks:
            data[(self.wTime, agent_.id)] = agent_.simulData[self.wTime]
        self.dataQueue.put(data)