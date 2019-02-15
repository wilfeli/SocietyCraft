import core_tools
import agent 



class Market(agent.Agent):
    def __init__(self, w):
        super().__init__()
        self.asks = {}
        self.bids = {}
        self.ids = []
        self.paymentSystem = w.paymentSystem
        self.history = {"p":core_tools.DEFAULT_P, 
                        "currency":core_tools.ContractTypes.SCMoney}


    def GetBidAsk(self, marketOrder):
        if marketOrder["type"] == core_tools.FITypes.Ask:
            self.asks[marketOrder["id"]].append(marketOrder)
        elif marketOrder["type"] == core_tools.FITypes.Bid:
            self.bids[marketOrder["id"]].append(marketOrder)

    def AcTick(self):
        """
        """
        pass



    def StartStage01(self, w_):
        """
        Add additional information to bids and asks
        """
        for id_ in self.ids:
            self.asks[id] = {}
            self.bids[id] = {}



    def AcTickFood(self):
        """
        """
        #sorts asks and bids that have and matches them ?
        

        for marketID in self.ids:
            asks = self.asks[marketID]
            bids = self.bids[marketID]

            #ROADMAP iterate over all asks and bids
            #so that proper market matching is done, 
            #current realization is simple random matching and is done in 
            #one pass only
            for i in range(min(len(asks), len(bids))):
                ask = asks[core_tools.random.randrange(0,len(asks))]
                bid = bids[core_tools.random.randrange(0,len(bids))]
                
                #check that ids are the same
                if ask["id"] == bid["id"]:
                    #
                    q_ = min(ask["q"], bid["q"])

                    #check for inf prices 
                    if ask["p"] == core_tools.math.copysign(core_tools.math.inf, 1.0):
                        if bid["p"] == core_tools.math.copysign(core_tools.math.inf, 1.0):
                            p_ = core_tools.DEFAULT_P
                        else:
                            p_ = bid["p"]
                    else:
                        if bid["p"] == core_tools.math.copysign(core_tools.math.inf, 1.0):
                            p_ = ask["p"]
                        else:
                            p_ = core_tools.np.average([ask["p"], bid["p"]])

                    q_PS = q_ * p_ 
                    #request payment
                    transaction = self.paymentSystem.RequestTransaction({
                        "payee":ask["agent"], 
                        "payer":bid["agent"], 
                        "q":q_PS,
                        "currency":core_tools.ContractTypes.SCMoney})
                    

                    if transaction.IsValid:
                        #tell that there was a sale 
                        ask["agent"].MarketSettleContract(q_, ask, bid)
                        self.history["p"] = p_

        if not self.w.ui.params["DebugMode"]:
            #removes all bids and asks to keep market interactions simple
            #ROADMAP might decide to remove bids and asks if they are cleared for example
            self.bids = []
            self.asks = []




class MarketResourceFoodW(Market):
    """
    """
    def __init__(self, w):
        super().__init__(w)
        self.marketType = core_tools.AgentTypes.MarketResourceFoodW
        #type of market is part of an id
        self.ids = [("Food", "Wheat", "Generic", "AW")]
        self.AcTick = self.AcTickFood




class MarketResourceFood(Market):
    """
    Market for Seed generally
    Here G sells seeds if needed and F buy it
    """
    def __init__(self, w):
        super().__init__(w)
        self.marketType = core_tools.AgentTypes.MarketResourceFood
        self.ids = [("Food", "Wheat", "Generic")]
        self.AcTick = self.AcTickFood
        




class MarketIntermediateFood(Market):
    """
    Market where Farm sells raw food to the Firm that owns Stores
    """
    def __init__(self, w):
        super().__init__(w)
        self.marketType = core_tools.AgentTypes.MarketIntermediateFood
        #what gs are on the market at the moment
        #ROADMAP will be updated when new gs are added to the simulation
        self.ids = [("Food", "Bread", "Generic")]
        self.AcTick = self.AcTickFood
        




class MarketFinalFood(Market):
    """
    Handles stores and final sales to H 
    """
    def __init__(self, w):
        super().__init__(w)
        self.marketType = core_tools.AgentTypes.MarketFinalFood
        self.stores = []
        self.w = w

    def StartStage01(self):
        for f in self.w.firms:
            if hasattr(f, 'stores'):
                self.stores.extend(f.stores)

    def GetStore(self, agent):
        #pick random store for now 
        randomStore = core_tools.random.randrange(0, len(self.stores))
        return self.stores[randomStore]




class MarketHK(Market):
    def __init__(self, w):
        super().__init__(w)
        self.marketType = core_tools.AgentTypes.MarketHK
        self.params = {}
        #FIXME check that Contract Length and Frequency are reasonable, so that all 
        #payment that are required actually happen and no contract is deleted without payment
        #if there is enough money
        #FIXME decide if names of parameters should start with the small letter or with the
        #big letter, right here are two options used at the same time
        self.params["ContractLength"] = core_tools.WTime.N_TICKS_DAY
        self.params["FrequencyPayment"] = core_tools.WTime.N_TOTAL_TICKS_WEEK
        self.w = w


    def AcTick(self):
        """
        """
        for i in range(min(len(self.asks), len(self.bids))):
            ask = self.asks[core_tools.random.randrange(0,len(self.asks))]
            bid = self.bids[core_tools.random.randrange(0,len(self.bids))]
            
            if ((ask["state"] == core_tools.ContractStates.Active) and 
                (bid["state"] == core_tools.ContractStates.Active)):

                
                q_ = min(ask['q'], bid['q'])
                if ((abs(ask['p']) < core_tools.math.inf) and (abs(bid['p']) < core_tools.math.inf)):
                    p_ = core_tools.np.average(ask['p'], bid['p'])
                else:
                    #here at least one of them is inf - pick smaller number
                    #assume that could be -inf and inf - pick an actual number 
                    p_ = min(abs(ask['p']), abs(bid['p']))

                data = {'p':p_,
                        'q':q_,
                        'employer':bid['employer'],
                        ('employer','agent'):bid['agent'],
                        'employee':ask['agent'],
                        'type':core_tools.ContractTypes.HKContract
                        }

                ask['agent'].CreateContract(data, self.w)
                #save to history
                self.history["p"] = p_

                #to keep it simple and mark that ask is no longer active
                ask["state"] = core_tools.ContractStates.Closed

        #remove all bids and asks
        if not self.w.ui.params["DebugMode"]:
            #ROADMAP change to cleaning when something was done with them 
            self.bids = []
            self.asks = []




class MarketCredit(Market):
    def __init__(self, w):
        super().__init__(w)
        self.marketType = core_tools.AgentTypes.MarketCredit
        self.params = {}
        self.params["ContractLength"] = core_tools.WTime.N_TOTAL_TICKS_WEEK
        self.params["FrequencyPayment"] = core_tools.WTime.N_TOTAL_TICKS_WEEK
        self.w = w
        self.history["i"] = core_tools.DEFAULT_i/core_tools.WTime.N_TOTAL_TICKS_MONTH


    def AcTick(self):
        #sort asks
        def interestRateSort(marketOrder):
            return marketOrder['i']

        self.asks.sort(key = interestRateSort, reverse = True)

        print(self.asks)

        #start from highest ask (with the lowest interest rate), connect to bidders randomly for now
        for i in range(min(len(self.asks), len(self.bids))):
            ask = self.asks[i]
            bid = self.bids[core_tools.random.randrange(0,len(self.bids))]

            q_ = min(ask['q'], bid['q'])
            if ((abs(ask['i']) < core_tools.math.inf) and (abs(bid['i']) < core_tools.math.inf)):
                i_ = core_tools.np.average(ask['i'], bid['i'])
            else:
                #here at least one of them is inf - pick smaller number
                #assume that could be -inf and inf - pick an actual number 
                i_ = min(abs(ask['i']), abs(bid['i']))


            data = {'qTotal':q_,
                    'qOutstanding':q_,
                    'interestRate':i_,
                    'bidAgent':bid['agent'],
                    'type':core_tools.ContractTypes.CreditContract
                    }

            #create contract
            ask['agent'].CreateContract(data, self.w)
            #save to history
            self.history["i"] = i_
            #update ask and bid
            ask['q'] -= q_
            bid['q'] -= q_


        #remove all bids and asks
        if not self.w.ui.params["DebugMode"]:
            #ROADMAP change to cleaning when something was done with them 
            self.bids = []
            self.asks = []



