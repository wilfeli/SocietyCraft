import agent
import core_tools
from core_tools import GetStr as GetStr


class Body(object):
    def __init__(self, template):
        self.params = template['params'].copy()
        self.state = core_tools.AgentStates.Idle
        self.utility = {'health':0.0, 'energy':0.0, 'mood':0.0}
        self.locationX = 0.0
        self.locationY = 0.0

    def GetLocation(self):
        return self.locationX, self.locationY

class HLogistics(object):
    def __init__(self, template):
        self.params = template['params'].copy()


class Human(agent.Agent):


    def __init__(self, template):

        super().__init__()

        #financial instruments 
        self.fi = []
        #will return list of PSMoney when called
        self.money = self.GetPSMoney
        #physical parameters of an agent 
        self.body = Body(template['body'])
        #mind in a way / ghost representation
        self.ghost = HLogistics(template['logistics'])
        #decisions 
        self.decisions = {}
        #TODO there are two versions of decisions, one with long id, one with dictionary with details
        self.decisions[('dec','Food','q')] = 10
        self.decisions[('dec', 'HK')] = {'p': - core_tools.math.inf, 'q': 1.0}
        #has action and data that agents wants to do, for w to tick on it and move the ghost
        #to the intended place 
        self.intentions = {}
        #inventory of GS, simplified with only quantity stored
        self.inventory = {}
        #will have Residence later, like House or something else with location
        self.residence = agent.Residence()
        #HK contracts
        self.hkContracts = []

        #last time decision was made
        self.acTimes = {}
        self.acTimes['Life'] = 0.0
        self.acTimes['PS'] = 0.0

    #TODO setter and getter for money


    def StartStage01(self, w):
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



    def AcTick(self, wTime, deltaTime, w):
        if (deltaTime > 4) or (wTime - self.acTimes['Life']) > 4:
            #buy food 
            self.BuyFood(w)
            self.AcOfferHK(w)
            self.acTimes['Life'] = wTime
        else:
            #go to work 
            self.GoToWorkF(w)
        
        self.DecHK(w)
        self.DecFI(w)

        #call rarely
        freq = w.markets(core_tools.AgentTypes.MarketHK).params['FrequencyPayment']
        if ((self.acTimes['PS'] + freq) <= wTime) and (self.acTimes['PS'] < wTime):
            self.AcPS(wTime, deltaTime, w)
            self.acTimes['PS'] = wTime



    def AcPS(self, wTime, deltaTime, w):
        #remove incactive orders
        def IsInactiveContract(contract):
            return contract['EndTime'] < wTime and contract['PSTransaction']

        self.hkContracts[:] = core_tools.filterfalse(IsInactiveContract, self.hkContracts)





    def AcOfferHK(self, w):
        """
        """
        #checks if wants to work
        #supplies ask to the market
        id_ = ('HK',)
        dec = self.decisions[('dec', *id_)]
        marketOrder = {'id':id_,\
                'type':core_tools.FITypes.Ask,\
                'agent':self,\
                'q':dec['q'], \
                'p':dec['p']}

        w.GetMarketMessage(marketOrder)




    def BuyFood(self, w):
        #go to the store 
        market = w.markets(core_tools.AgentTypes.MarketFood, self)
        #pick where want to shop
        store = market.GetStore(self)

        #pick what want to buy 
        #record intention
        #FIXME: here uses explicit id in other places uses tuple as id with positional meaning
        self.intentions = {'location': store.GetLocation(), \
                            'action': store.GetBid, \
                            'data': {'agent':self, \
                                    'q':self.decisions[('dec','Food','q')],\
                                    'type':'Food',\
                                    'subtype':'Bread',\
                                    'brand':'Generic'}}
    

    def GoToWorkF(self, w):
        """
        Get to the place of work 
        """
        #get where to work
        contract = None
        if self.hkContracts:
            contract = self.hkContracts[-1]
        if contract:
            locationWork = contract[('employer', 'agent')].GetLocationContract(contract)
            #mark intention 
            self.intentions = {'location': locationWork, 
                            'action': self.WorkF, 
                            'data':{}}
        else:
            locationHome = self.residence.GetLocation()
            self.intentions = {'location':locationHome,
                                'action': self.Leisure,
                                'data':{}}

    def WorkF(self, data):
        """
        Actually work somewhere
        """
        pass

    def Leisure(self, data):
        """
        Rest and improve mood
        """
        self.body.utility['mood'] += 1.0

    def AcIntention(self):
        """
        implements intention - calls action with the data for it
        """
        self.intentions['action'](self.intentions['data'])
        self.AcUpdateIntention()


    def GetErrorTransaction(self, transaction):
        """
        """
        #attempt to buy failed 
        #repeat at smaller q
        self.decisions[('dec','Food','q')] -= max(0.0, self.decisions[('dec','Food','q')]/2)


    def GetLogisticMessage(self, lgOrder):
        """
        When at the store - this method is called and returns home with the purchase
        """
        #change intention to going back home 
        self.intentions = {'location': (self.residence.locationX, self.residence.locationY), \
                            'action': self.DeliverLG, \
                            'data':lgOrder}
    

    def DeliverLG(self, lg_order):
        """
        """
        id_ = core_tools.GetIdFrom(lg_order)
        #add GS from lg_order to the inventories 
        self.inventory[id_] += lg_order['q']

    def AcUpdateIntention(self):
        """
        cleans after the intention is realized 
        """
        #clean from previous intention for now 
        self.intentions = {}
    



    def DecFI(self, w):
        pass
        #here will check if need more credit 



        #or if want to deposit some money
        #or buy FI later 

    def DecHK(self, w):
        """
        """
        pass


    def CreateContract(self, data, w):
        """
        Create contract for HK, i.e. labor contract
        """
        market = w.markets(core_tools.AgentTypes.MarketHK, self)
        contract = data
        contract['ContractLength'] = market.params['ContractLength']
        contract['BeginTime'] = w.wTime
        contract['EndTime'] = contract['BeginTime'] + contract['ContractLength']
        self.hkContracts.append(contract)
        contract[('employer', 'agent')].GetContract(contract)
        contract['PSTransaction'] = False