import core_tools
import agent 



class Market(agent.Agent):
    def __init__(self, w):
        super().__init__()
        self.asks = []
        self.bids = []
        self.paymentSystem = w.paymentSystem
        self.history = {"p":core_tools.DEFAULT_P, 
                        "currency":core_tools.ContractTypes.SCMoney}


    def GetBidAsk(self, offer):
        if offer['type'] == core_tools.FITypes.Ask:
            self.asks.append(offer)
        elif offer['type'] == core_tools.FITypes.Bid:
            self.bids.append(offer)

    def AcTick(self):
        """
        """
        pass

    def StartStage01(self):
        """
        """
        pass



class MarketRawFood(Market):
    """
    Market for Seed generally
    """
    def __init__(self, w):
        super().__init__(w)
        self.marketType = core_tools.AgentTypes.MarketRawFood



class MarketIntermediateFood(Market):
    """
    Market where Farm sells raw food to the Firm that owns Stores
    """
    def __init__(self, w):
        super().__init__(w)
        self.marketType = core_tools.AgentTypes.MarketIntermediateFood

        

    

    def AcTick(self):
        """
        """
        #sorts asks and bids that have and matches them ?
        #TODO iterate over all asks and bids
        for i in range(min(len(self.asks), len(self.bids))):
            ask = self.asks[core_tools.random.randrange(0,len(self.asks))]
            bid = self.bids[core_tools.random.randrange(0,len(self.bids))]
            
            #check that ids are the same
            if ask['id'] == bid['id']:
                #
                q_ = min(ask['q'], bid['q'])

                #FIXME: add check for inf prices 

                p_ = core_tools.np.average([ask['p'], bid['p']])

                q_PS = q_ * p_ 
                #request payment
                transaction = self.paymentSystem.RequestTransaction({
                    'payee':ask['agent'], 
                    'payer':bid['agent'], 
                    'q':q_PS,
                    'currency':core_tools.ContractTypes.SCMoney})
                

                if transaction.IsValid:
                    #tell that there was a sale 
                    ask['agent'].MarketSettleContract(q_, bid)
                    self.history["p"] = p_

        #FIXME remove all bids and asks
#        self.bids = []
#        self.asks = []




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
        self.params['ContractLength'] = core_tools.WTime.N_TICKS_DAY
        self.params['frequencyPayment'] = core_tools.WTime.N_TOTAL_TICKS_WEEK
        self.w = w


    def AcTick(self):
        """
        """
        for i in range(min(len(self.asks), len(self.bids))):
            ask = self.asks[core_tools.random.randrange(0,len(self.asks))]
            bid = self.bids[core_tools.random.randrange(0,len(self.bids))]
            
            if ((ask['State'] == core_tools.ContractStates.Active) and 
                (bid['State'] == core_tools.ContractStates.Active)):

                
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
                ask['State'] = core_tools.ContractStates.Closed

        #remove all bids and asks
        #FIXME: change to cleaning when something was done with them 
        self.bids = []
        self.asks = []




class MarketCredit(Market):
    def __init__(self, w):
        super().__init__(w)
        self.marketType = core_tools.AgentTypes.MarketCredit
        self.params = {}
        self.params['ContractLength'] = core_tools.WTime.N_TOTAL_TICKS_WEEK
        self.params['frequencyPayment'] = core_tools.WTime.N_TOTAL_TICKS_WEEK
        self.w = w
        self.history["i"] = 0.05/core_tools.WTime.N_TOTAL_TICKS_MONTH


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
        #FIXME: change to cleaning when something was done with them 
        self.bids = []
        self.asks = []



