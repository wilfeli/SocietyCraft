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
        #extract id as a tuple
        id_ = bid['type'], bid['subtype'], bid['brand'] 
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
    def __init__(self, template):
        self.params = template['params'].copy()
        self.location = template['location'].copy()


class Factory(agent.Facility):

    def __init__(self, template, agent_):
        super().__init__()
        self.params = template['params'].copy()
        temp = self.params['resources']
        self.params['resources'] = {}
        for key, value in temp.items():
            keyInternal = core_tools.GetID(key)
            self.params['resources'][keyInternal] = value

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
        #reserve energy
        #check how many people have reported to work
        #check how much capital has 
        #produce GS if it is reasonable 
        

        if self.params['ProductionTicks'] <= 0.0:
            #start production
            #reserve Wheat 
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
            if self.params['ProductionTicks'] >= self.params['MaxTicks']:
                self.params['q'] += self.params['ProductionF'][0] * \
                                    self.params['resources'][("Food", "Wheat")]
                keys = ['q', 'type', 'subtype', 'brand']
                lgOrder = {}
                for key in keys:
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


    def AcPS(self, wTime, deltaTime, agent_):
        """
        """
        
        freq = agent_.w.markets(core_tools.AgentTypes.MarketHK).params['FrequencyPayment']
        if ((self.acTimes['PS'] + freq) <= wTime) and (self.acTimes['PS'] < wTime):

            #assume all contracts are active
            for contract in agent_.hkContracts:

                #time of previous payment 
                psTimeT_1 = self.acTimes['PS']
                #time of current payment
                psTimeT = wTime
                #length of payment period in ticks
                if contract['BeginTime'] <= psTimeT:
                    if contract['EndTime'] >= psTimeT_1:
                        paymentPeriod = min(psTimeT, contract['EndTime']) - max(psTimeT_1, contract['BeginTime']) 
                        q_PS = paymentPeriod * contract['p'] * contract['q']

                        transaction = agent_.w.paymentSystem.RequestTransaction({
                            'payee':contract['employee'], 
                            'payer':contract['employer'], 
                            'q':q_PS,
                            'currency':core_tools.ContractTypes.SCMoney})
                        if contract['EndTime'] < wTime:
                            #mark that all payments are done or not
                            contract['PSTransaction'] = transaction.IsValid
                    else:
                        #FIXME: here just drop contract for which didn't have enough money to pay
                        contract['PSTransaction'] = True

            #remove inactive orders
            def IsInactiveContract(contract):
                return contract['EndTime'] < wTime and contract['PSTransaction']

            agent_.hkContracts[:] = core_tools.filterfalse(IsInactiveContract, agent_.hkContracts)
            self.acTimes['PS'] = wTime


class ManagementRawFood(ManagementF):
    """
    manages food production on the farm and production from raw food on the Food Factory
    """
    def __init__(self, template):
        super().__init__(template)


    def AcTick(self, wTime, deltaTime, agent_):
        """
        All sub actions 
        """
        self.AcPS(wTime, deltaTime, agent_)
        self.AcMarket(wTime, deltaTime, agent_)
        


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


    def UpdateDecMarket(self, id_, dec_type, dec):
        """
        dec, type, subtype, brand; subdecision
        """

        #have fixed price for now 
        dec[id_[-1]][dec_type[0]] = 1.0



class ManagementBtoH(ManagementF):
    """
    manages sale of GS to H in a store
    """
    def __init__(self, template):
        super().__init__(template)

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



    def AcTick(self, wTime, deltaTime, agent_):
        """
        All sub actions 
        """
        self.AcPS(wTime, deltaTime, agent_)
        self.AcMarket(wTime, deltaTime, agent_)
        self.AcStores(agent_)


    def AcMarket(self, wTime, deltaTime, agent_):
        """
        action for the MarketRawFood for the firm that owns stores and sells goods 
        """
        #purchase of food on the market
        for store in agent_.stores:
            for key, value in store.inventory.items():
                #request to buy additional goods for inventory
                id_ = ('dec', *key, 'Bid')
                dec = agent_.decisions[id_]
                bid  = dec['bid']
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
                self.UpdateDecStore(id_, ['p'], dec)
                store.prices[key] = dec['p']



        #hire labor for stores 
        #FIXME: employer is used in the marketOrder and in the contract, but not used in assigning workers to locations
        for store in agent_.stores:
            id_ = ('dec', 'HK')
            dec = agent_.decisions[id_]
            self.UpdateDecHKMarket(id_, ['q', 'p'], dec)
            marketOrder = {'type': core_tools.FITypes.Bid, \
                            'id':('HK',),\
                            'q':dec['q'],\
                            'p':dec['p'],\
                            'employer':store,\
                            'agent':agent_}
            #assume that market discarded old market order
            agent_.w.GetMarketMessage(marketOrder)


    def UpdateDecStore(self, id_, dec_type, dec):
        """
        """
        dec['p'] = 1.0


    def UpdateDecGSMarket(self, id_, dec_type, dec):
        """
        dec, type, subtype, brand; subdecisions 
        """

        #have fixed price for now 
        dec['p'] = 1.0
        #have fixed q for now 
        dec['q'] = max(dec['q'], 10.0)


    def UpdateDecHKMarket(self, id_, dec_type, dec):
        """
        dec, FIType
        """
        dec['p'] = 1.0
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

        #setup market decisions based on what Farms/Stores have
        self.management.SetupDecMarket(self)

    
    
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
                facility = Farm(templ)
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





    def StartStage1(self, w):
        """
        """
        #get random bank
        bankID = core_tools.random.randrange(0, len(w.banks))
        psMoney = {'type':core_tools.FITypes.PSMoney,
                    'currency':core_tools.ContractTypes.SCMoney,
                    'q':10.0,
                    'issuer':w.banks[bankID]}
        self.fi.append(psMoney)
        w.banks[bankID].GetPSContract(psMoney)

    
    #determines how much money H has
    def GetPSMoney(self):
        return [x for x in self.fi if x['type'] == core_tools.FITypes.PSMoney]



    def AcTick(self, wTime, deltaTime):
        """
        """
        #calls production depending on type 
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
            #update for number of ticks
            farm.params['ProductionTicks'] += deltaTime
            #check if it is harvest time
            if farm.params['ProductionTicks'] >= farm.params['MaxTicks']:
                farm.params['q'] += farm.params['ProductionQ']
                keys = ['q', 'type', 'subtype']
                lgOrder = {}
                for key in keys:
                    lgOrder[key] = farm.params[key]
                    lgOrder[('destination', 'location')] = self
                    lgOrder[('destination', 'agent')] = self
                self.logistics.GetLogisticMessage(lgOrder)
                farm.params['q'] = 0.0
                farm.params['ProductionTicks'] = 0.0


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
        self.hkContracts.append(contract)



    def GetLocationContract(self, hkContract):
        """
        Return place of work for the contract
        """
        return self.management.GetLocationContract(hkContract, self)


    def GetLogisticMessage(self, lgOrder):
        self.logistics.GetLogisticMessage(lgOrder)