import agent
import core_tools

class Bank(agent.Agent):

    def __init__(self, template, w):
        #what financial instruments has
        self.fi = []
        self.balanceSheet = {}
        self.profit = {
            "timeBegin":0.0,
            "timeEnd":0.0,
            "income_t":0.0,
            "expences_t":0.0,
            "income_t1":0.0,
            "expences_t1":0.0
            }
        self.w = w
        self.decisions = {}

        self.SetupDecMarket()

        self.counterUI = self.w.simulParameters["FrequencyAcTickUI"]
        self.simulData = {}

        #TODO make it a nice name, not only id
        self.id = core_tools.ID_COUNTER
        core_tools.ID_COUNTER += 1.0


    def StartStage01(self, w):
        """
        """
        self.profit["timeBegin"] = w.wTime
        self.profit["timEnd"] = w.wTime + self.w.government.regulations["FrequencyBAccounting"]



    def SetupDecMarket(self):
        """
        creates place for decisions
        """

        #decision for FI 
        self.decisions[("dec", "FI", "credit")] = {'i':core_tools.DEFAULT_i/core_tools.WTime.N_TOTAL_TICKS_MONTH}



    def AcTick(self, wTime, deltaTime):
        """
        All sub actions 
        """

        self.AcMarket(wTime, deltaTime)
        self.AcLegalSystem(wTime, deltaTime)
        self.AcPS(wTime, deltaTime)
        self.counterUI -= 1.0
        if self.counterUI <= 0.0:
            self.AcTickUI(wTime)
            self.counterUI = self.w.simulParameters["FrequencyAcTickUI"]



    def AcPS(self, wTime, deltaTime):
        """
        """
        #remove inactive orders
        def IsInactiveCreditContract(contract):
            return (contract["timeEnd"] < wTime 
                    and contract["PSTransaction"] 
                    and contract["type"] == core_tools.ContractTypes.CreditContract) 

        self.fi[:] = core_tools.filterfalse(IsInactiveCreditContract, self.fi)

    def AcTickUI(self, wTime):
        """
        """
        self.simulData[wTime:[self.balanceSheet["capital"]]]


    def AcMarket(self, wTime, deltaTime):
        """
        Check here how much credit could give and give it 
        """

        #update credit decision
        id_ = ("dec", "FI", "credit")
        dec = self.decisions[id_]
        self.UpdateDecFIMarket(id_, ['q', 'i'], dec)


        marketOrder = {'type': core_tools.FITypes.Ask, \
                            'id':('FI','credit'),\
                            'q':dec['q'],\
                            'i':dec['i'],\
                            'agent':self}


        self.w.GetMarketMessage(marketOrder)



    def UpdateDecFIMarket(self, id_, dec_type, dec):
        """
        """
        qMax = self.balanceSheet["capital"]/self.w.government.regulations["MinCapitalRatio"]
        qCurrent = self.EstimateTotalAssets(core_tools.ContractTypes.CreditContract)

        dec['q'] = max(0.0, qMax - qCurrent)


    def EstimateTotalAssets(self, id_):
        """
        """
        q_ = 0.0
        if id_ == core_tools.ContractTypes.CreditContract:
            for fi in self.fi:
                if fi["type"] == id_:
                    q_ += fi["qOutstanding"]



    def GetPSContract(self, contract):
        self.fi.append(contract)


    def GetContract(self, data):
        if data['type'] == core_tools.ContractTypes.CreditContract:
            self.fi.append(data)
        else:
            print("{0}: wrong contract type no handler".format(type(self).__name__))


    def CreateContract(self, data, w):
        """
        Create contract for credit 
        """

        if data["type"] == core_tools.ContractTypes.CreditContract:
            #TODO for now gives total requested amount without second check, might need to actually check
            #if can and want to do it still 
            market = w.markets(core_tools.AgentTypes.MarketCredit, self)
            contract = data
            contract['ContractLength'] = market.params['ContractLength']
            contract['timeBegin'] = w.wTime
            contract['timeEnd'] = contract['timeBegin'] + contract['ContractLength']
            contract["frequencyPayment"] = market.params['frequencyPayment']
            contract["issuer"] = self
            contract['PSTransaction'] = False

            self.fi.append(contract)
            contract['bidAgent'].GetContract(contract)


    def AcLegalSystem(self, wTime, deltaTime):
        """
        """
        if wTime >= self.profit["timeEnd"]:
            self.UpdateCapital()
            #erase for now all 
            for key, value in self.profit.items():
                self.profit[key] = 0.0

            self.profit["timeBegin"] = wTime
            self.profit["timEnd"] = wTime + self.w.government.regulations["FrequencyBAccounting"]




    def UpdateCapital(self):
        """
        Updates calculations for the amount of capital
        """

        #capital increases if had profit 
        #profit comes from interest payment
        #add interest payments
        self.balanceSheet["capital"] += self.profit["income_t"]
        self.balanceSheet["capital"] -= self.profit["expences_t"]


        #capital decreases if had losses
        #losses come from not paying off the contract
        #light bankruptcy, when firms and humans might fail to pay, 
        #is handled right when the message is received


    



    def ReceiveMessage(self, data):
        """
        """
        #save to the log? or directly add to the capital estimation 
        if data["id"] == ("credit","interest"):
            self.profit["income_t"] += data["q"]
        else:
            print("{0}: wrong message type no handler".format(data["id"]))

        



    def ReceiveMessageLS(self, data):
        """
        """
        #receives message that this contract is bankrupt 
        #decrease amount of capital for the outstanding amount - direct write off
        self.balanceSheet["capital"] -= data["qOutstanding"]