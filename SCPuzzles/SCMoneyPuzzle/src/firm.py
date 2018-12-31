import core_tools
import agent







class Logistics(agent.Agent):
    def __init__(self, template, agent_):
        self.agent = agent_
        self.params = {}
        self.params['TimeTravel'] = 10.0
        
        

    def SendLG(self):
        #create logistic order 
        pass

    def GetLogisticMessage(self, lgOrder):
        #current use case - Farm produced goods and they are delivered to the central storage
        #Factory produces from raw food and it is delivered to the central storage
        #sends goods to other firm
        if lgOrder[('destination', 'agent')] != self.agent:
            self.agent.w.GetLogisticMessage(lgOrder)
            return
        
        #if for the main storage
        if lgOrder[('destination', 'location')] == self.agent:
            for gs in self.agent.gs:
                if self.IsSame(gs, lgOrder):
                    gs['q'] += lgOrder['q']
                    break
            #create new gs if there is no gs to match
            keys = ['type', 'subtype']
            if 'brand' in lgOrder:
                keys.append('brand')
            gs = {}
            for key in keys:
                gs[key] = lgOrder[key]
            #store goods
            gs['q'] = lgOrder['q']
            self.agent.gs.append(gs)
        else:
            #tell management to figure out where to send
            self.agent.management.GetLogisticMessage(lgOrder, self.agent)
        
        
            





    def IsSame(self, rhs, lhs):
        """
        compares type and subtype for equality 
        compares brand only if there is brand in the originator 
        """
        #compare type
        if 'type' in rhs:
            if 'type' in lhs:
                if rhs['type'] == lhs['type']:
                    #compare subtype 
                    if 'subtype' in rhs:
                        if 'subtype' in lhs:
                            if rhs['subtype'] == lhs['subtype']:
                                #compare brand
                                if 'brand' in rhs:
                                    if 'brand' in lhs:
                                        if rhs['brand'] == lhs['brand']:
                                            return True
                                        else:
                                            return False
                                    else:
                                        #in this case any good would do, because the request does not have a brand in it,
                                        #which means that brand isn't important, so return true
                                        return True
                                else:
                                    if 'brand' in lhs:
                                        return False
                                    else:
                                        return True
                            else:
                                return False
                        else:
                            return False
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False



class Store(agent.Facility):
    """
    Responsible for retail sales for FtoH firms, not all F have stores
    """

    def __init__(self, template, agent_):
        self.paymentSystem = agent_.w.paymentSystem
        #has simplified inventory where only quantity is stored 
        self.inventory = {}
        self.prices = {}
        self.building = agent.Building()
        self.state = core_tools.AgentStates.Closed
        self.agent = agent_

        if len(template['inventory']) > 0:
            for key, value in template['inventory'].items():
                self.inventory[core_tools.GetID(key)] = value


    #determines how much money H has
    def GetPSMoney(self):
        return self.agent.GetPSMoney()

    def GetLocation(self):
        return self.building.GetLocation()



    def GetLogisticMessage(self, lgOrder):
        """
        lg_order id = (type, subtype, brand) i.e. (Food, Bread, Generic)
        """

        id_ = core_tools.GetIdFrom(lgOrder)
        self.inventory[id_] += lgOrder['q']



    def GetBid(self, bid):
        """
        sells goods according to the bid, does not use market, instead the sale is direct
        """
        #id is a tuple
        #("Food", "Bread", "Generic")
        id_ = bid["id"] 
        #extract quantity
        q_ = min(self.inventory[id_], bid['q'])
        #reserve goods
        self.inventory[id_] -= q_
        #extract what is it and get price
        q_PS = self.prices[id_] * q_
        
        #request payment
        transaction = self.paymentSystem.RequestTransaction({
                                'payee':self, 
                                'payer':bid['agent'], 
                                'q':q_PS, 
                                'currency':core_tools.ContractTypes.SCMoney})

        if transaction.IsValid:
            lgOrder = bid.copy()
            #remove 'type'
            lgOrder.pop('type', None)
            #change agent to self from the buyer that was in the bid
            lgOrder['agent'] = self
            #update quantity
            lgOrder['q'] = q_ 
            #set locations properly
            lgOrder[('destination', 'location')] = bid['agent']
            lgOrder[('destination', 'agent')] = bid['agent']
            #give agent quantity
            bid['agent'].GetLogisticMessage(lgOrder)
        else:
            #return reserved goods
            self.inventory[id_] += q_
            #tell agent what went wrong 
            bid['agent'].GetErrorTransaction(bid)


class Farm(agent.Facility):
    def __init__(self, template, agent_):
        self.params = template['params'].copy()

        #read resources
        self.resources = core_tools.ReadJsonTupleName(template["resources"])
        self.actionF = core_tools.ReadJsonDict(template["actionF"])
        
        self.location = template['location'].copy()
        self.agent = agent_


    def AcTick(self, wTime, deltaTime, w):
        self.AcProductionResources(wTime, deltaTime, w)

    @core_tools.deprecated
    def AcProductionNoResources(self, wTime, deltaTime, w):
        """
        Uses only time to produce required good
        """

        #update for number of ticks
        self.params['ProductionTicks'] += deltaTime
        #check if it is harvest time
        if self.params['ProductionTicks'] >= self.params['MaxTicks']:
            self.params['q'] += self.params['ProductionQ']
            keys = ['q', 'type', 'subtype']
            lgOrder = {}
            for key in keys:
                lgOrder[key] = self.params[key]
            lgOrder[('destination', 'location')] = self
            lgOrder[('destination', 'agent')] = self
            self.agent.logistics.GetLogisticMessage(lgOrder)
            self.params['q'] = 0.0
            self.params['ProductionTicks'] = 0.0
    
    
    def AcProductionResources(self, wTime, deltaTime, w):
        """
        Uses resources from the specification to produce goods 
        """
        if self.params['ProductionTicks'] <= 0.0:
            #start production
            #reserve Wheat
            #FIXME replace with taking resources from the factory specification 
            id_ = ("Food", "Wheat")
            gs = self.agent.GetGS(id_)
            if gs:
                if gs['q'] > 0.0:
                    #FIXME assume only one Unit for now = one m2
                    qResource = min(
                        gs['q'], 
                        self.params["MaxQPerM2"])
                    self.resources[("Food", "Wheat")] = qResource
                    gs['q'] -= qResource
            
        self.AcProductionTick(wTime, deltaTime, w)
        if self.params['ProductionTicks'] >= self.params['MaxTicks']:
            self.AcFinalProductionTick()
        


    def AcProductionTick(self, wTime, deltaTime, w):
        #advance production ticks 
        self.params['ProductionTicks'] += deltaTime

        if self.actionF["GrowthF"][("HK",)] > 0.0:
            #find how much could serve with the amount of labor that has
            #GrowthF = production per tick from specified amount of resources, e.g. [1.0, 1.0,0.0] 
            #would produce 1 unit of qGrowth from 1 unit of raw q, not using any labor at all
            qRaw = min(
                self.resources[("Food", "Wheat")], 
                self.resources[("HK",)]/self.actionF["GrowthF"][("HK",)]/self.actionF["GrowthF"][("Food","Wheat")])
        else:
            qRaw = self.resources[("Food", "Wheat")]
        #amount that could potentially harvest before the end, in terms of raw plant mass
        self.params["qPotential"] += self.actionF["GrowthF"][("Theta0",)] * qRaw * deltaTime

        
        
    def AcFinalProductionTick(self):
        #after harvesting, uses raw plant mass and other resources for harvesting
        if self.actionF["ProductionF"][("HK",)] <= 0.0:
            qRaw = self.params["qPotential"]
        else:
            #FIXME finish for the case when uses labor for harvesting, or machines
            qRaw = min(
                self.params["qPotential"], 
                self.resources[("HK",)]/self.actionF["ProductionF"][("HK",)]/self.actionF["ProductionF"][("Food","Wheat")])

        self.params['q'] += self.actionF["ProductionF"][("Theta0",)] * \
                            qRaw 
        #remove raw resources 
        self.params["qPotential"] = 0.0

        keys = ['q', 'type', 'subtype', 'brand']
        lgOrder = {}
        for key in keys:
            #here marks what factory is producing, which is encoded in its params
            if key in self.params:
                lgOrder[key] = self.params[key]
        lgOrder[('destination', 'location')] = self.agent
        lgOrder[('destination', 'agent')] = self.agent
        self.agent.logistics.GetLogisticMessage(lgOrder)
        self.params["q"] = 0.0
        self.resources = {}
        self.params['ProductionTicks'] = 0.0    
        
        
      

class Factory(agent.Facility):

    def __init__(self, template, agent_):
        super().__init__()
        self.params = template['params'].copy()
        self.resources = core_tools.ReadJsonTupleName(template['resources'])
        self.location = template['location'].copy()
        
        if "Food" in self.params['type']:
            self.AcProduction = self.AcProductionFood
        else:
            #defaults to producing machinery on the factory
            self.AcProduction = self.AcProductionMachinery
        
        self.agent = agent_


    def AcTick(self, wTime, deltaTime, w):
        self.AcProduction(wTime, deltaTime)


    


    def AcProductionFood(self, wTime, deltaTime):
        """
        produces processed food
        
        """

        #FIXME code for farm is updated to more streamlined version, need to replace this implementation
        #with that code

        #FIXME in the next iteration will have more resources to consider
        #reserve energy
        #check how many people have reported to work
        #check how much capital has 
        #produce GS if it is reasonable 
        

        if self.params['ProductionTicks'] <= 0.0:
            #start production
            #reserve Wheat
            #FIXME: replace with taking resources from the factory specification 
            id_ = ("Food", "Wheat")
            gs = self.agent.GetGS(id_)
            if gs:
                if gs['q'] > 0.0:
                    self.params['resources'][("Food", "Wheat")] = gs['q']
                    gs['q'] = 0.0

                    #start producing 
                    self.params['ProductionTicks'] += deltaTime
        else:
            #advance tick
            self.params['ProductionTicks'] += deltaTime
            #check that it is still producing
            #if not - send produced good to storage
            if self.params['ProductionTicks'] >= self.params['MaxTicks']:
                self.params['q'] += self.params['ProductionF'][0] * \
                                    self.params['resources'][("Food", "Wheat")]
                keys = ['q', 'type', 'subtype', 'brand']
                lgOrder = {}
                for key in keys:
                    #here marks what factory is producing, which is encoded in its params
                    lgOrder[key] = self.params[key]
                    lgOrder[('destination', 'location')] = self.agent
                    lgOrder[('destination', 'agent')] = self.agent
                self.agent.logistics.GetLogisticMessage(lgOrder)
                self.params['q'] = 0.0
                self.params['resources'][("Food", "Wheat")] = 0.0
                self.params['ProductionTicks'] = 0.0

        


    def AcProductionMachinery(self, wTime, deltaTime):
        """
        produces machines - GoodK
        """
        pass

class ManagementF(agent.Agent):
    """
    """
    def __init__(self, template):
        super().__init__()
        self.acTimes = {}
        self.acTimes['PS'] = 0.0 #FIXME: initialize to zero for now, change to relative time
        

    def StartStage01(self, agent_):
        """
        """
        self.hkLocations = []
        for facility in agent_.facilities:
            if ("Factory" in type(facility).__name__ 
                or "Farm" in type(facility).__name__
                or "Store" in type(facility).__name__):
                self.hkLocations.append(facility)

        self.SetupDecMarket(agent_)


    def AcPS(self, wTime, deltaTime, agent_):
        """
        """
        
        #HK contracts payment
        #get general frequency of payments for the HK contracts 
        freq = agent_.w.markets(core_tools.AgentTypes.MarketHK).params['frequencyPayment']
        #FIXME: works only with one type of payment with respect to tracking time of payment
        if ((self.acTimes['PS'] + freq) <= wTime) and (self.acTimes['PS'] < wTime):

            #assume all contracts are active
            for contract in agent_.hkContracts:

                #time of previous payment 
                psTimeT_1 = self.acTimes['PS']
                #time of current payment
                psTimeT = wTime
                #length of payment period in ticks
                if contract['timeBegin'] <= psTimeT:
                    if contract['timeEnd'] >= psTimeT_1:
                        paymentPeriod = min(psTimeT, contract['timeEnd']) - max(psTimeT_1, contract['timeBegin']) 
                        q_PS = paymentPeriod * contract['p'] * contract['q']

                        transaction = agent_.w.paymentSystem.RequestTransaction({
                            'payee':contract['employee'], 
                            'payer':contract['employer'], 
                            'q':q_PS,
                            'currency':core_tools.ContractTypes.SCMoney})
                        if contract['timeEnd'] < wTime:
                            #mark that all payments are done or not
                            contract['PSTransaction'] = transaction.IsValid
                    else:
                        #FIXME: here just drop contract for which didn't have enough money to pay
                        #with this tag it will be dropped in the next stage
                        contract['PSTransaction'] = True

            #remove inactive orders
            def IsInactiveContract(contract):
                return contract['timeEnd'] < wTime and contract['PSTransaction']

            agent_.hkContracts[:] = core_tools.filterfalse(IsInactiveContract, agent_.hkContracts)
            self.acTimes['PS'] = wTime


        #credit contract
        #make payment on contracts
        for contract in agent_.fi:
            if contract["type"] == core_tools.ContractTypes.CreditContract:
                self.AcPSCredit(contract, wTime, deltaTime, agent_)    

        #remove inactive orders
        def IsInactiveCreditContract(contract):
            return (contract["timeEnd"] < wTime 
                    and contract["PSTransaction"] 
                    and contract["type"] == core_tools.ContractTypes.CreditContract) 

        agent_.fi[:] = core_tools.filterfalse(IsInactiveCreditContract, agent_.fi)
        agent_.acTimes['PS'] = wTime

    

    def AcPSCredit(self, contract, wTime, deltaTime, agent_):
        """
        """
        agent.PaymentSystemAgent.AcPSCredit(agent_, contract, wTime, deltaTime, agent_.w)




class ManagementRawFood(ManagementF):
    """
    manages food production on the farm and production from raw food on the Food Factory
    """
    def __init__(self, template):
        super().__init__(template)
        self.freeHK = []
        


    def StartStage01(self, agent_):
        """
        """
        super().StartStage01(agent_)


    def AcTick(self, wTime, deltaTime, agent_):
        """
        All sub actions 
        """
        self.AcPS(wTime, deltaTime, agent_)
        self.AcMarket(wTime, deltaTime, agent_)
        self.AcReserveProduction(wTime, deltaTime, agent_)
        


    def AcReserveProduction(self, wTime, deltaTime, agent_):
        """
        """
        #prepare HK resources
        #pick at random where to assign them 

        for hkLocation in self.hkLocations:
            #assume that no HK is reserved in the beginning of the tick
            hkLocation.resources[("HK",)] = 0.0 


        #first check previous assignments 
        for contract in agent_.hkContracts:
            if contract["EndTime"] >= wTime:
                #check if "employer" is assigned and needs labor
                hkLocation = contract["employer"]
                if hkLocation:
                    qCurrent = hkLocation.resources[("HK",)]
                    qRequired = self.EstimateRequiredHK(agent_, hkLocation)

                    if qCurrent >= qRequired:
                        #do not assign HK here
                        contract["employer"] = None
                        self.freeHK.append(contract)
                    else:
                        #check if wants to work this tick 
                        if agent_.w.IsEAtLocation(contract[("employer", "agent")].GetLocation(), 
                                                contract["employee"]):
                            hkLocation.resources[("HK",)] += contract["q"]
                else:
                    #it is new contract without assignment
                    self.freeHK.append(contract)

        #assign new contracts
        for contract in self.freeHK:
            randomNumber = core_tools.random.randrange(0, len(self.hkLocations))
            hkLocation = self.hkLocations[randomNumber]
            #current amount 
            qCurrent = hkLocation.resources[("HK",)] 
            #required amount for productions:
            qRequired = self.EstimateRequiredHK(
                            agent_,
                            hkLocation)

            if qCurrent < qRequired:
                contract["employer"] = hkLocation
                hkLocation.resources[("HK",)] += 1.0

        #do only one pass at contracts
        self.freeHK = []


                


                




    def EstimateRequiredHK(self, agent_, facility):
        """
        """
        #calculation is not exact, it shows how much they would need 
        #given the production at the previous tick
        if "Farm" in type(facility).__name__:
            #here uses direct estimation, might change to the estimation based on
            #what management planned for this Farm to have
            qRequired = (facility.params["qPotential"]
                        /facility.actionF["ProductionF"][("HK",)])
        elif "Factory" in type(facility).__name__:
            #assume that management decides how much capital needs
            qRequired = agent_.decisions[("dec", "HK")]["q"]

        return qRequired



    def SetupDecMarket(self, agent_):
        """
        creates place for decisions
        """
        if hasattr(agent_, 'farms'):
            for farm in agent_.farms:
                #TODO check what happens when have multiple farms with the same production
                #in this case need multiple asks for them or add to the old ask, maybe?
                id_ = ('dec', farm.params['type'], farm.params['subtype'])
                agent_.decisions[id_] = {}
                #collection of brands that will be used
                agent_.decisions[id_]['brands']=['Generic']
                #setup decision for 'Generic' brand
                agent_.decisions[id_]['Generic'] = {'q':core_tools.math.inf, 
                                                    'p':-core_tools.math.inf, 
                                                    'ask':{'id':(*id_[1:], 'Generic')}}
        
        #if can produce something else
        for facility in agent_.facilities:
            if "Factory" in type(facility).__name__:
                id_ = ('dec', facility.params['type'], facility.params['subtype'])
                agent_.decisions[id_] = {}
                agent_.decisions[id_]['brands']=['Generic']
                agent_.decisions[id_]['Generic'] = {'q':core_tools.math.inf, 
                                                    'p':-core_tools.math.inf, 
                                                    'ask':{'id':(*id_[1:], 'Generic')}}

                #setup factory to produce the brand
                facility.params['brand'] = "Generic"


        #create space for HK decisions
        agent_.decisions[('dec','HK')] = {'q':10.0, 'p':core_tools.DEFAULT_P}






    def AcMarket(self, wTime, deltaTime, agent_):
        """
        action for the market for the firm that produces raw food on the farm and sells it 
        """
        #updates ask 
        #get amount of goods that has in inventories 
        for dec_id, dec in agent_.decisions.items():
            #use first brand for now 
            brand = dec['brands'][0]
            #check how much can sell 
            id_ = dec_id[1:]
            #returns record about stored goods from inventory 
            gs = agent_.GetGS(id_)

            if gs:
                if gs['q'] > 0.0:
                    ask  = dec[brand]['ask']
                    ask['q'] = gs['q']
                    self.UpdateDecMarket((*dec_id, brand), ['p'], dec)
                    ask['p'] = dec[brand]['p']
                    ask['agent'] = agent_
                    ask['type'] = core_tools.FITypes.Ask

                    #assume that market discarded old ask
                    agent_.w.GetMarketMessage(ask)

        #request HK for farm and factory
        #FIXME: requests HK too often, every tick here
        for hkLocation in self.hkLocations:
            id_ = ('dec', 'HK')
            dec = agent_.decisions[id_]
            self.UpdateDecHKMarket(id_, ['q', 'p'], dec)
            marketOrder = {'type': core_tools.FITypes.Bid, \
                            'id':('HK',),\
                            'q':dec['q'],\
                            'p':dec['p'],\
                            'employer':hkLocation,\
                            'agent':agent_}
            #assume that market discarded old market order
            agent_.w.GetMarketMessage(marketOrder)



    def UpdateDecMarket(self, id_, dec_type, dec):
        """
        dec, type, subtype, brand; subdecision
        """

        #have fixed price for now 
        dec[id_[-1]][dec_type[0]] = core_tools.DEFAULT_P

    def UpdateDecHKMarket(self, id_, dec_type, dec):
        """
        dec, FIType
        """
        #FIXME: dummy value for now for each farm and factory
        dec['p'] = core_tools.DEFAULT_P
        dec['q'] = max(dec['q'], 10.0)



class ManagementBtoH(ManagementF):
    """
    manages sale of GS to H in a store
    """
    def __init__(self, template):
        super().__init__(template)


    def CreateWm(self):
        """
        """
        self.wm = {}
        #estimate of the demand function for the market
        #q_t = theta_0 + theta_1 * p_t 
        self.wm[core_tools.AgentTypes.MarketFood] = [100.0, -0.1]

        #regularization term for the negative cash flow
        self.wm["ThetaProfitMaxRegularization"] = 1.0




    def SetupDecMarket(self, agent_):
        """
        creates place for decisions
        """
        if hasattr(agent_, 'stores'):
            for store in agent_.stores:
                for key, value in store.inventory.items():
                    id_ = ('dec', *key, 'Bid')
                    if id_ in agent_.decisions:
                        #update decision
                        agent_.decisions[id_]['q'] += 10.0
                    else:
                        #setup decision
                        agent_.decisions[id_] = {'q':10.0, 'p':1.0, 'bid':{'id':key}}
                    if not(id_ in self.acTimes):
                        self.acTimes[id_] = 0.0
                    id_ = ('dec', *key, 'Ask')
                    if id_ in agent_.decisions:
                        #update decision
                        agent_.decisions[id_]['p'] = 1.0
                    else:
                        #setup decision for stores
                        agent_.decisions[id_] = {'p':1.0, 'ask':{'id':key}}


        #create place for decision on HK 
        agent_.decisions[('dec','HK')] = {'q':10.0, 'p':1.0}

        #also decisions for prices for goods

        #decision for FI 
        agent_.decisions[("dec", "FI", "credit")] = {'q':10.0, 'i':core_tools.math.inf}


    def AcTick(self, wTime, deltaTime, agent_):
        """
        All sub actions 
        """
        self.AcPS(wTime, deltaTime, agent_)
        self.AcMarket(wTime, deltaTime, agent_)
        self.AcStores(agent_)


        def DecisionsCondition():
            condition = False

            if (wTime > core_tools.WTime.N_TOTAL_TICKS_WEEK) \
                or (self.acTimes["Life"] > core_tools.WTime.N_TOTAL_TICKS_WEEK):
                condition = True

            return condition
                
                
                
        if DecisionsCondition():
            #update decisions and try to use max profit
            self.decProfitMax001(agent_)
            self.acTimes["Life"] = wTime


    def decProfitMax001(self, agent_):
        """
        """
        #get 3 prices to try and pick best
        #create state
        # TODO add picking id from what is already belongs to the firm 


        #here needs "ids_" what is available to the firm to sell
        #use all possible ids in this version 
        ids_ = core_tools.energySourcesGS



        state = {}
        self.WmState(state)
        decs = []
        for i in range(0,3,1):
            dec = {}
            #prepare decision
            #explore 0.5p_t ; 1.0p_t; 1.5p_t
            for id in ids_:
                dec[(*id_, "pStore")] = dec[(*id_, "pStore")] \
                                        * (0.5 + 0.5 * i)
            #length of the forecasting horizon in ticks = one season
            dec["t1t0"] = core_tools.WTime.N_TOTAL_TICKS_MONTH
            #how many ticks are used as a buffer in decisions
            dec["safeguardt"] = core_tools.WTime.N_TOTAL_TICKS_WEEK
            #HK decision 
            dec["qHK"] = agent_.decisions[('dec','HK')]["q"]
            self.DecProfitF(dec, state)
            #save it into decision
            dec["profitt1t0"] = state["F"]["profitt1t0"] 
            decs.append(dec)

            #clean states between requests
            state["F"] = {}
            #clean dec between requests ?


        #TODO 
        #pick best among decisions 
        #store decision and how well expected to be doing with it - compare to reality
        self.DecSelectAndStore(decs, agent_, {"ids":ids_})



    def DecSelectAndStore(self, decs, agent_, data):
        """
        """
        optDec = max(decs, key=lambda item:item["profitt1t0"])[0]

        #save decision from it 
        #assume that makes decisions for only 1 GS
        id_ = data["ids_"][0]
        agent_.decisions[("dec", *id_, "Ask")]["p"] = optDec[(*id_, "pStore")]
        agent_.decisions[("dec", *id_, "Bid")]["q"] = optDec[(*id_, "qInv")]
        agent_.decisions[("dec", "FI", "credit")]["q"] = optDec[("qBMoney", "credit")]




    def WmState(self, dec, state, agent_):
        """
        Creates state 
        """
        #get inventory for the store
        id_ = dec["ids_"][0]
        wm_id = (*id_, "qInvt0")
        state[wm_id] = 0.0
        if hasattr(agent_, 'stores'):
            for store in agent_.stores:
                state[wm_id] += store.inventory[id_]

        #update current price 
        wm_id = (*id_, "pStore")   
        if wm_id in agent_.decisions:
            state[wm_id] = agent_.decisions[wm_id]
        else:
            #use default price of 1.0
            state[wm_id] = core_tools.DEFAULT_P

        #get money
        state["qBMoneyt0"] = 0.0 
        for account in self.agent_.GetPSMoney():
            state["qBMoneyt0"] += account["q"]


        #gets prices from the market 
        state[core_tools.AgentTypes.MarketHK]["p"] = agent_.w.markets(core_tools.AgentTypes.MarketHK).history["p"]
        state[core_tools.AgentTypes.MarketCredit]["i"] = agent_.w.markets(core_tools.AgentTypes.MarketCredit).history["i"]



    def DecProfitF(self, dec, state):
        """
        dec includes price 
        """
        id_ = dec["ids_"][0]
        wm_id = (*id_, "pStore")        
        #add current price to the state
        state["F"][wm_id] = dec[wm_id]
        
        #request expected sales for the price
        #could be random if needed, in that case could request multiple estimates
        #right now it is non-random profit max estimation
        self.WmGSMarket(state, id_)

        #estimate how much need 
        self.DecInventoryManagementF(dec, state, id_)

        #call down the line to estimate other decisions
        self.DecFinanceManagement(dec, state, id_)

    

        #estimate average profit 
        state["F"]["profitt1t0"] = 0.0
        #income per tick
        state["F"]["profitt1t0"] += \
            state[(*id_, "qStore")] \
            * dec[wm_id]
        #expences per tick for HK
        state["F"]["profitt1t0"] -= \
            state["qHK"] \
            * self.wm[core_tools.AgentTypes.MarketHK]["p"]
        #expences for credit per tick, here interest is already accounted with 
        #the proper sign
        state["F"]["profitt1t0"] += \
            state[("qBMoney", "it")]

        #expences for inventory per tick 
        state["F"]["profitt1t0"] -= \
            state[(*id_, "qStore")] \
            * self.wm[core_tools.AgentTypes.MarketRawFood][(*id_, "pInv")]

        
        #in the version1.0 it will he the place to
        #estimate average risk per tick 
        #mean , dispersion = get utility estimate for this decision
        #as Int(u(x) * dF)

        #for version0.1
        #estimate cash flow - in chuncks of safeguard length, to simplify calculations
        # in this simple case each period is similar in terms of ticks and could simply 
        # multiply by the length of the safeguard period to get the cash flow estimate
        # after the calculation for cash flow is made 
        # count each period that is in the red 
        # add regularization term to the profit - that is theta * N of red segments
        # this will help pick best decently safe profit 
        # and it separates mean estimation from partial variance estimation
        # doing it together is basically creating a model in the model 
        # impossible to do 
        # because all models would need to change after one small change 
        # this way majority of changes will be ignored as they are not  
        # modelled anyway  
        # in this simple case the number of red periods will be 
        # the total forecast length/safeguard length

        # + income from sales
        # - HK expenses
        # + interest expences (they are already with the proper sign)
        # - inventory expences
        state[("qBMoney", "qFlowt")] = \
                state[(*id_, "qStore")] \
                * dec[wm_id] \
                - state["qHK"] \
                * self.wm[core_tools.AgentTypes.MarketHK]["p"] \
                + state[("qBMoney", "it")] \
                - state[(*id_, "qStore")] \
                * self.wm[core_tools.AgentTypes.MarketRawFood][(*id_, "pInv")]

        # estimate total cash flow for the chunk (simplified)
        qFlowt1t0 = state[("qBMoney", "qFlowt")] \
                    * dec["safeguardt"] 
        #estimate N of periods
        N = (int) (dec["t1t0"] / dec["safeguardt"])

        #add regularization term 
        #TODO 
        state["F"]["profitt1t0"] += \
                                self.wm["ThetaProfitMaxRegularization"] \
                                * N \
                                * core_tools.math.copysign(1, qFlowt1t0)









    def DecInventoryManagementF(self, dec, state, id_):
        """
        Estimate how much inventory need
        """
        #assume that sales are per tick 
        qInvt = state[(*id_, "qStore")]
        qInvt1t0 = qInvt * dec["t1t0"]
        qInvSafeguardt = qInvt * dec["safeguardt"]
        #how much have now
        qBalancet1 = state[(*id_, "qInvt0")] - qInvt1t0 - qInvSafeguardt

        if qBalancet1 >= 0.0:
            dec[(*id_, "qInv")] = 0.0
        elif qBalancet1 < 0.0:
            #how much need to buy given the estimates
            dec[(*id_, "qInv")] = -qBalancet1

            

    def DecFinanceManagement(self, dec, state, id_):
        """
        Estimate how much money needs
        """
        #estimate average money balance

        #estimate if need credit to finance inventory purchase and how much 
        qBMoneyDec = dec[(*id_, "qInv")] \
                    * self.wm[core_tools.AgentTypes.MarketRawFood][(*id_, "pInv")]
        #buffer to have 
        #estimate expences
        qBMoneySafeguardt = state["qHK"] \
                            * self.wm[core_tools.AgentTypes.MarketHK]["p"] \
                            * dec["safeguardt"]
        #need 
        qBalancet1 = state["qBMoneyt0"] - qBMoneyDec - qBMoneySafeguardt
        if qBalancet1 >= 0.0:
            dec[("qBMoney", "credit")] = 0.0
        elif qBalancet1 < 0.0:
            dec[("qBMoney", "credit")] = -qBalancet1


    def DecCreditManagement(self, dec, state, id_):
        """
        Estimate how much will be paying
        """ 
        if dec[("qBMoney", "credit")] >= 0.0:
            #add payments per tick on average
            state[("qBMoney", "it")] = \
                - dec[("qBMoney", "credit")] \
                * state[core_tools.AgentTypes.MarketCredit]["i"] \
                / 2.0




    def WmGSMarket(self, state, id_):
        """
        estimates the sales given the price
        """
        #FIXME think about using specific for the particular GS id here 
        # or just use the general form of the demand function 

        state["F"][(*id_, "qStore")] = self.wm[core_tools.AgentTypes.MarketFood][id_][0] \
                            + self.wm[core_tools.AgentTypes.MarketFood][id_][1] \
                            * state[(*id_, "pStore")]

        return state




    def AcMarket(self, wTime, deltaTime, agent_):
        """
        actions for markets for the firm that owns stores and sells goods 
        """


        #set frequency of decisions
        #purchase of food on the market
        for store in agent_.stores:
            for key, value in store.inventory.items():
                #request to buy additional goods for inventory
                id_ = ('dec', *key, 'Bid')
                dec = agent_.decisions[id_]
                bid  = dec['bid']
                if self.acTimes["Life"] <= 0.0:
                    self.UpdateDecGSMarket(id_, ['q', 'p'], dec)
                bid['q'] = dec['q']
                bid['p'] = dec['p']
                #TODO check if there is id for the GS in here, and what is it
                bid['agent'] = agent_
                bid['type'] = core_tools.FITypes.Bid
                bid[('destination', 'location')] = store

                #assume that market discarded old bid
                agent_.w.GetMarketMessage(bid)



        #review prices for goods in the store
        for store in agent_.stores:
            for key, value in store.inventory.items():
                id_ = ('dec', *key, 'Ask')
                dec = agent_.decisions[id_]
                if self.acTimes["Life"] <= 0.0:
                    self.UpdateDecStore(id_, ['p'], dec)
                store.prices[key] = dec['p']



        #hire labor for stores 
        #FIXME: employer is used in the marketOrder and in the contract, but not used in assigning workers to locations
        for store in agent_.stores:
            id_ = ('dec', 'HK')
            dec = agent_.decisions[id_]
            if self.acTimes["Life"] <= 0.0:
                self.UpdateDecHKMarket(id_, ['q', 'p'], dec)
            marketOrder = {'type': core_tools.FITypes.Bid, \
                            'id':('HK',),\
                            'q':dec['q'],\
                            'p':dec['p'],\
                            'employer':store,\
                            'agent':agent_}
            #assume that market discarded old market order
            agent_.w.GetMarketMessage(marketOrder)

        #update credit decision
        id_ = ("dec", "FI", "credit")
        dec = agent_.decisions[id_]
        if self.acTimes["Life"] <= 0.0:
            self.UpdateDecFIMarket(id_, ['q', 'i'], dec)


        marketOrder = {'type': core_tools.FITypes.Bid, \
                            'id':('FI','credit'),\
                            'q':dec['q'],\
                            'i':dec['i'],\
                            'agent':agent_}

        agent_.w.GetMarketMessage(marketOrder)


    def UpdateDecStore(self, id_, dec_type, dec):
        """
        At what price to sell inventory in the store
        """
        dec['p'] = core_tools.DEFAULT_P


    def UpdateDecStoreEFG(self, id_, dec_type, dec):
        """
        Here setup price to maximize expected profit 
        """
        pass


    def UpdateDecGSMarket(self, id_, dec_type, dec):
        """
        dec, type, subtype, brand; subdecisions 

        How much and what to buy for the store inventory
        """

        #have fixed price for now 
        dec['p'] = core_tools.DEFAULT_P
        #have fixed q for now 
        dec['q'] = max(dec['q'], 10.0)


    def UpdateDecFIMarket(self, id_, dec_type, dec):
        """
        """
        dec['q'] = 10.0
        dec['i'] = core_tools.math.inf


    def UpdateDecHKMarket(self, id_, dec_type, dec):
        """
        dec, FIType
        """
        dec['p'] = core_tools.DEFAULT_P
        dec['q'] = max(dec['q'], 10.0)



    def GetLogisticMessage(self, lgOrder, agent_):
        """
        """
        storeID = core_tools.random.randrange(0, len(agent_.stores))
        agent_.stores[storeID].GetLogisticMessage(lgOrder)
        



    def GetLocationContract(self, contract, agent_):
        """
        contract will also have original store - maybe 
        """
        return agent_.stores[-1].building.GetLocation()


    def AcStores(self, agent_):
        """
        Will update store for the day if it is open or not
        """
        for store in agent_.stores:
            #check that has enough labor for the day 
            qHK = 0.0
            for contract in agent_.hkContracts:
                qHK += contract['q']
            if qHK > 0.0:        
                store.state = core_tools.AgentStates.Open 
            else:
                store.state = core_tools.AgentStates.Closed










class Firm(agent.Agent):
    def __init__(self, template, w):
        self.w = w
        self.logistics = Logistics(template['logistics'], self)
        self.gs = []
        self.fi = []
        self.facilities = []
        self.decisions = {}
        self.hkContracts = []
        self.CreateFacilities(template['facilities'])
        self.management = self.CreateManagement(template)

        #setup production
        if hasattr(self, 'farms'):
            self.actionProduction = [self.AcProductionOnFarm, 
                                    self.AcProductionOnFactory]
        else:
            self.actionProduction = [self.AcProductionOnFactory]

        
    
    
    def CreateManagement(self, template):
        """
        makes decision which management to create based on the type of facilities that own and other parameters
        """
        if hasattr(self, 'farms'):
            return ManagementRawFood(template['management'])
        elif hasattr(self, 'stores'):
            return ManagementBtoH(template['management'])


    def CreateFacilities(self, template):
        for templ in template:
            if 'Farm' in templ['type']:
                if not hasattr(self, 'farms'):
                    self.farms = []
                facility = Farm(templ, self)
                self.facilities.append(facility)
                self.farms.append(facility)
            elif 'Store' in templ['type']:
                if not hasattr(self, 'farms'):
                    self.stores = []
                    facility = Store(templ, self)
                    self.facilities.append(facility)
                    self.stores.append(facility)
            elif 'Factory' in templ['type']:
                facility = Factory(templ, self)
                self.facilities.append(facility)





    def StartStage01(self, w):
        """
        """
        #setup market decisions based on what Farms/Stores have
        self.management.StartStage01(self)


        #get random bank
        bankID = core_tools.random.randrange(0, len(w.banks))
        psMoney = {'type':core_tools.FITypes.PSMoney,
                    'currency':core_tools.ContractTypes.SCMoney,
                    'q':10.0,
                    'issuer':w.banks[bankID]}
        self.fi.append(psMoney)
        w.banks[bankID].GetPSContract(psMoney)

    
    #determines how much money has
    def GetPSMoney(self):
        return [x for x in self.fi if x['type'] == core_tools.FITypes.PSMoney]



    def AcTick(self, wTime, deltaTime):
        """
        """
        #calls production depending on type 
        self.management.AcProduction(wTime, deltaTime, self)
        for action in self.actionProduction:
            action(wTime, deltaTime)
        self.management.AcTick(wTime, deltaTime, self)






    



    def GetGS(self, id_):
        """
        """

        def GetIDDict(id_):
            """
            """
            id_dict = {'type':id_[0], 'subtype':id_[1]}
            if len(id_) > 2:
                id_dict['brand'] = id_[2]
            return id_dict

        id_dict = GetIDDict(id_)
        for gs in self.gs:
                if self.logistics.IsSame(gs, id_dict):
                    return gs
        return None



    def AcProductionOnFarm(self, wTime, deltaTime):
        """
        grows food 
        """
        #for each farm checks the state of the crop and advances it, if it is ready for being harvested - harvest
        #have deliver harvested to the storages as LgOrders 

        for farm in self.farms:
            farm.AcTick(wTime, deltaTime, self.w)


    def AcProductionOnFactory(self, wTime, deltaTime):
        """
        produces goods 
        """
        for facility in self.facilities:
            if "Factory" in type(facility).__name__:
                facility.AcTick(wTime, deltaTime, self.w)



    def AcProductionFacility(self, wTime, deltaTime):
        """
        builds new facility 
        """
        pass



    def MarketSettleContract(self, q_, bid_):
        """
        for now only gets an order to send goods to the buys
        """
        #sell good from inventory
        gs = self.GetGS(bid_['id'])
        gs['q'] -= q_

        lgOrder = bid_.copy()
        #change agent to self from the buyer that was in the bid
        lgOrder['agent'] = self
        #update quantity
        lgOrder['q'] = q_ 
        #update destination
        if ('destination', 'location') in bid_:
            lgOrder[('destination', 'location')] = bid_[('destination', 'location')]
        else:
            lgOrder[('destination', 'location')] = bid_['agent']
        lgOrder[('destination', 'agent')] = bid_['agent']
        #send into world logistics
        self.w.GetLogisticMessage(lgOrder)



    def GetContract(self, contract):
        if contract['type'] == core_tools.ContractTypes.HKContract:
            self.hkContracts.append(contract)
        else:
            print("Firm: wrong contract type, no handler")



    def GetLocationContract(self, hkContract):
        """
        Return place of work for the contract
        """
        return self.management.GetLocationContract(hkContract, self)


    def GetLogisticMessage(self, lgOrder):
        self.logistics.GetLogisticMessage(lgOrder)