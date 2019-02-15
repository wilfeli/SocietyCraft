import agent
import core_tools
from core_tools import GetStr as GetStr


class Body(object):
    def __init__(self, template):
        self.params = template['params'].copy()
        self.state = core_tools.AgentStates.Idle
        self.inventory = {}
        if "utility" in template:
            self.utility = template["utility"].copy()
        else:
            self.utility = {'health':0.0, 'energy':0.0, 'mood':0.0}
        self.locationX = 0.0
        self.locationY = 0.0

    def GetLocation(self):
        return self.locationX, self.locationY


    def AcTick(self, wTime, deltaTime, w):
        """
        tick physical parameters
        #TODO think if will do it once per world tick or would tick as the UE4 engine goes
        """
        #use energy
        self.utility["energy"] -= self.params["energyRequirementPerTick"] * deltaTime
        #age the agent
        self.params["Age"] += deltaTime



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
        self.mind = HLogistics(template['logistics'])
        #decisions 
        self.decisions = {}
        
        self.decisions[("dec","Food")] = {"qEnergy":10.0}
        self.decisions[("dec", "HK")] = {'p': - core_tools.math.inf, 'q': 1.0}
        #has action and data that agents wants to do, for w to tick on it and move the ghost
        #to the intended place 
        self.intentions = {}
        self.aiIntentionst_1 = []

        self.teamIntentionst_1 = []

        #will have Residence later, like House or something else with location
        self.residence = None
        #HK contracts
        self.hkContracts = []

        self.wm = template["wm"].copy()
        core_tools.ReplaceKeys(self.wm)
        


        #last time decision was made
        self.acTimes = {}
        self.acTimes['Health'] = 0.0
        self.acTimes['Work'] = 0.0
        self.acTimes['PS'] = 0.0
        self.acTimes['Leisure'] = 0.0
        self.acTimes['Life'] = 0.0


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



    def UpdateHKContracts(self, wTime):
        def IsInactiveContract(contract):
            return contract['timeEnd'] < wTime and contract['PSTransaction']

        self.hkContracts[:] = core_tools.filterfalse(IsInactiveContract, self.hkContracts)


    def AcTick(self, wTime, deltaTime, w):
        #tick physical parameters
        self.body.AcTick(wTime, deltaTime, w)
        #update intentions 
        self.intentions = self.aiIntentionst_1
        #future AI intentions
        self.aiIntentionst_1 = []


        #behavioral tree 
        #Check if has health need (like need to eat)
        def HealthCondition():
            condition = False

            if (deltaTime > 4) or (wTime - self.acTimes["Health"]) > 4:
                condition = True 

            #also if Energy is depleted 
            if self.body.utility["energy"] <= self.body.params["energyRequirementPerTick"]:
                condition = True

            #check if intentions are already set 
            if len(self.aiIntentionst_1) > 0.0:
                condition = False

            return condition



        def WorkCondition():
            condition = False

            if (deltaTime > 4) or (wTime - self.acTimes["Work"]) > 4:
                #check if there is an outstanding contract 
                self.UpdateHKContracts(wTime)

                #check if there are contracts left after cleaning
                if len(self.hkContracts)>0.0:
                    condition = True
                    #pick last contract
                    contract = self.hkContracts[-1]

            return condition

        def TeamCommand():
            condition = False
            if len(self.teamIntentionst_1) > 0.0:
                condition = True

            return condition

        def LifeCondition():
            #here is a placeholder for future expansion of the tree 
            condition = True
            return condition


        #check if have orders from the team first
        if TeamCommand():
            #handle team command first 
            self.AcTeamCommand(wTime, deltaTime, w)

        if HealthCondition():
            #speed of movement will be greatly reduced if is very low on energy 
            # (i.e.) it is zero 
            self.AcHealth(wTime, deltaTime, w)

        if len(self.aiIntentionst_1) <= 0.0:
            #there is nothing 
            #so nothing is already planned for the next step (important because it is health related)
            #can make decisions 
            if WorkCondition():
                self.AcWork()
            elif LifeCondition():
                self.AcLeisure()


        #here make decisions and act on them if needed
        def DecisionsCondition():
            condition = False
            if (deltaTime > 4) or (wTime - self.acTimes["Life"]) > 4:
                condition = True
            return condition

        if DecisionsCondition():
            #Here will make decisions
            self.DecHealth(wTime, w)
            self.DecHK(wTime, w)
            self.DecFI(w)
            self.acTimes["Life"] = wTime


        #call rarely
        freq = min(w.markets(core_tools.AgentTypes.MarketHK).params["FrequencyPayment"],
                    w.markets(core_tools.AgentTypes.MarketCredit).params["FrequencyPayment"])

        if ((self.acTimes['PS'] + freq) <= wTime) and (self.acTimes['PS'] < wTime):
            self.AcPS(wTime, deltaTime, w)
            self.acTimes['PS'] = wTime





    def AcTeamCommand(self, wTime, deltaTime, w):
        """
        """
        #have new command from the Team 
        #make it a priority and skip other conditions 
        #FIXME sort through possible commands from the Team
        self.aiIntentionst_1 = self.teamIntentionst_1
        self.teamIntentionst_1 = []


    def IsAtHome(self, bodyLocation):
        """
        Checks if is at home
        """
        if bodyLocation == self.residence.GetLocation():
            return True
        else:
            return False


    def AcHealth(self, wTime, deltaTime, w):
        """
        Here needs to take care of Health part, mostly eat food
        """

        


        #checks how much Energy has stored at Home 
        #if have above the threshold and not at home 
        #go home 
        #if below threshold - go shopping to buy food

        def HasRequiredEnergy():
            condition = False
            availableEnergy = self.EnergyContents()
            qConsumeEnergy = min(self.body.params["maxEnergy"], availableEnergy)
            if qConsumeEnergy > self.body.params["energyRequirementPerTick"]:
                condition = True
            else:
                #need to go shopping
                condition = False

        if HasRequiredEnergy():
            if self.IsAtHome(self.body.GetLocation()):
                self.AcConsumeEnergy(wTime, deltaTime, w)
            else:
                self.AcMoveHome(wTime, deltaTime, w)
        else:
            self.AcBuyFood(w)


    def AcMoveHome(self, wTime, deltaTime, w):
        """
        Decides to move home 
        """
        self.aiIntentionst_1.append({"location": self.residence.GetLocation(), \
                            "action": None})



    def EnergyContents(self, gs = None):
        """
        Estimates how much energy has stored
        """

        #check if has food at home 
        #FIXME now has new way of handling inventory
        #inventory in the Residence
        #inventory on the H itself 

        totalEnergy = 0.0
        if gs is None:
            #inventory in the Residence
            foods = core_tools.GetGSFromID(self.residence.inventory, ("Food",))
        else:
            foods = gs 

        for food in foods:
            energy = core_tools.energyContents[food["id"]]
            totalEnergy += food["q"] * energy 

        return totalEnergy


    def AcConsumeEnergy(self, wTime, deltaTime, w):
        """
        """
        foods = core_tools.GetGSFromID(self.residence.inventory, ("Food",))

        def ConsumeEnergy(q):
            """
            Eats actual food the required amount
            """
            consumedEnergy = 0.0
            qRemaining = q
            for food in foods:
                energy = core_tools.energyContents[food["id"]]
                availableForConsumption = food["q"] * energy
                qConsumeEnergy = min(qRemaining, availableEnergy)
                qConsume = qConsumeEnergy/energy
                food["q"] -= qConsume
                #add to the current energy 
                self.body.utility["energy"] += qConsume
                qRemaining -= qConsumeEnergy 
                if (qRemaining <= 0.0):
                    break
            

        availableEnergy = self.EnergyContents()
        qConsumeEnergy = min(self.body.params["maxEnergy"], availableEnergy)
        if qConsumeEnergy > 0.0:
            ConsumeEnergy(qConsumeEnergy)

        #mark that took action with respect to Health 
        self.acTimes['Health'] = wTime



    def DecHealth(self, wTime, w):
        """
        Decides how much and what to buy for Food (Energy) sources

        ("Food", "Bread", "Generic")

        #later might pick between options based on the lowest cost per energy unit    
        #price per Energy Unit
        pPerEU = p/core_tools.energyContents[id_]
        """
        self.UpdateHKContracts(wTime)

        def EstimateEIncome():
            """
            """
            eIncome = 0.0
            #see if has an outstanding labor contract - pick it as an income per tick
            # otherwise pick % of current money    
            if len(self.hkContracts)>0.0:
                #pick last contract
                contract = self.hkContracts[-1] 
                eIncome = contract["p"]
            else:
                eIncome = self.GetPSMoney()[0]/core_tools.WTime.N_TOTAL_TICKS_WEEK

            return eIncome

        #buy Food for 1 week
        requiredEnergy = self.body.params["energyRequirementPerTick"] \
                            * core_tools.WTime.N_TOTAL_TICKS_WEEK

        availableFoods = core_tools.energySourcesGS

        #pick first in the list
        id_ = availableFoods[0]

        #pick where to go to buy food
        market = w.markets(core_tools.AgentTypes.MarketFinalFood, self)
        store = market.GetStore(self)
        p = store.prices[id_]
        eIncome = EstimateEIncome()
        #check how much money is making as an income and decide to spend 
        availableIncome = eIncome \
                            * core_tools.WTime.N_TOTAL_TICKS_WEEK \
                            * self.wm[("dec", "Health")]["Theta0"]
        qRequired = requiredEnergy/core_tools.energyContents[id_]
        qAvailable = availableIncome/p

        qToBuy = min(qRequired, qAvailable)

        self.decisions[("dec",*id_,"q")] = qToBuy


        



        

        



    def AcBuyFood(self, wTime, deltaTime, w):

        #go to the store 
        market = w.markets(core_tools.AgentTypes.MarketFinalFood, self)
        #pick where want to shop
        store = market.GetStore(self)

        #already purchased food and is going back home
        if self.intentions[0]["action"] == self.DeliverLG:
            gs = core_tools.GetGSFromID(self.body.inventory, ("Food",))
            energy = self.EnergyContents(gs)
            if energy > 0.0:
                if w.IsAtLocation(self.residence.GetLocation(), 
                                    self.body.GetLocation()): 
                    #deliver gs
                    self.AcIntention()

                    #eat
                    self.AcConsumeEnergy(wTime, deltaTime, w)
                else:
                    #keep going home 
                    self.aiIntentionst_1.append(self.intentions[0])

                    

        #check if is at the store
        if w.IsAtLocation(store, self.body.GetLocation()):
            #check if there is already intention 
            if len(self.intentions) > 0.0:
                #assume that purchases in bulk - so only one intention
                self.AcIntention()
        else:
            #pick what want to buy 
            #record intention
            #FIXME: keep decision ids consistent here and when make purchase decision for food
            #here picks to buy? what 

            decs = core_tools.GetDecFromID(self.decs, ("Food"))

            if len(self.aiIntentionst_1) <= 0.0:
                self.aiIntentionst_1 = []
            self.aiIntentionst_1.append({"location": store.GetLocation(), \
                                "action": self.AcBuyFoodStore, \
                                "data002": store.GetBid, \
                                "data": [{'agent':self, \
                                        'q':self.decisions[("dec",k[1:4],"q")],\
                                        "id":k[1:4]} for k, v in decs.items()]})


    def AcBuyFoodStore(self, data_, intention_):
        """
        here will submit bids to the market 

        and return home after that 
        """
        #submit all bids 
        for dataItem in data_:
            intention_["data002"](dataItem) 

        #change intention to going back home 
        self.intentionst_1.append({"location": self.residence.GetLocation(), \
                            "action": self.DeliverLG})



    def AcPS(self, wTime, deltaTime, w):
        #remove inactive orders or contracts
        def IsInactiveContract(contract):
            return contract['timeEnd'] < wTime and contract['PSTransaction']

        self.hkContracts[:] = core_tools.filterfalse(IsInactiveContract, self.hkContracts)


        #make payment on contracts
        for contract in self.fi:
            if contract["type"] == core_tools.ContractTypes.CreditContract:
                self.AcPSCredit(contract, wTime, deltaTime, w)
            elif contract["type"] == core_tools.ContractTypes.PropertyContract:
                self.AcPSProperty(contract, wTime, deltaTime, w)


        #remove inactive orders
        def IsInactiveCreditContract(contract):
            return (contract["timeEnd"] < wTime 
                    and contract["PSTransaction"] 
                    and contract["type"] == core_tools.ContractTypes.CreditContract) 

        self.fi[:] = core_tools.filterfalse(IsInactiveCreditContract, self.fi)
        self.acTimes['PS'] = wTime


    def AcPSCredit(self, contract, wTime, deltaTime, w):
        """
        """
        agent.PaymentSystemAgent.AcPSCredit(self, contract, wTime, deltaTime, w)

        
    def AcPSProperty(self, contract, wTime, deltaTime, w):
        #time of previous payment 
        psTimeT_1 = self.acTimes['PS']
        #time of current payment
        psTimeT = wTime
        #length of payment period in ticks
        paymentPeriod = psTimeT - psTimeT_1
        qPerTick = contract["q"]/contract["FrequencyPayment"]
        qPS = paymentPeriod * qPerTick

        transaction = w.paymentSystem.RequestTransaction({
                    'payee':contract["issuer"], 
                    'payer':self, 
                    'q':qPS,
                    'currency':core_tools.ContractTypes.SCMoney})




    def EstimateContractPS(self):
        """
        Estimates how much needs to pay per tick
        """

        qContractPS = 0.0

        for contract in self.fi:
            if contract["type"] == core_tools.ContractTypes.CreditContract:
                qContractPS += self.EstimateCreditContractPS(contract)
            elif contract["type"] == core_tools.ContractTypes.PropertyContract:
                qContractPS += self.EstimatePropertyContractPS(contract)

        return qContractPS


    def EstimateCreditContractPS(self, contract):
        """
        """
        qBodyPerTick = contract["qTotal"]/(contract["timeEnd"] - contract["timeBegin"])
        qInterestPerTick = contract["interestRate"] * contract["qOutstanding"]

        return qBodyPerTick + qInterestPerTick


    def EstimatePropertyContractPS(self, contract):
        """
        """
        qPerTick = contract["q"]/contract["FrequencyPayment"]

        return qPerTick




    def AcOfferHK(self, w):
        """
        """
        #checks if wants to work
        #supplies ask to the market
        id_ = ("HK",)
        dec = self.decisions[("dec", *id_)]
        marketOrder = {'id':id_,\
                'type':core_tools.FITypes.Ask,\
                'agent':self,\
                'q':dec['q'], \
                'p':dec['p']}

        w.GetMarketMessage(marketOrder)





    

    def AcWorkF(self, data_, intention_):
        """
        Actually work somewhere
        """
        #increases fatigue level
        self.body.utility['mood'] -= 1.0
        self.acTimes['Work'] = data_["wTime"]
        
        

    def AcWork(self, wTime, deltaTime, w):
        """
        Get to the place of work 
        """
        #get where to work

        contract = None
        if self.hkContracts:
            contract = self.hkContracts[-1]
        if contract:
            locationWork = contract[('employer', 'agent')].GetLocationContract(contract)

        def IsAtWork():
            #check if is at the work place 
            condition = False
            bodyLocation = self.body.GetLocation()
            if bodyLocation == locationWork:
                condition = True
            return condition

        if IsAtWork():
            if self.intentions[0]["action"] == self.AcWorkF:
                #work at the place
                    self.AcIntention()
            else:
                #keep going to Work
                self.aiIntentionst_1.append(self.intentions[0])

        else:
            #mark intention to go to Work
            self.intentionst_1 = {'location': locationWork, 
                            'action': self.AcWorkF, 
                            'data':{"wTime":wTime}}

        






    def AcLife(self, wTime, deltaTime, w):
        """
        Here is a node for handling other possible actions, for now it is rest
        """
        if self.IsAtHome(self.body.GetLocation()):
            self.AcLeisure(wTime, deltaTime, w)
        else:
            self.AcMoveHome(wTime, deltaTime, w)

    def AcLeisure(self, wTime, deltaTime, w):
        """
        Rest and improve mood
        """
        self.body.utility['mood'] += 1.0
        self.acTimes['Leisure'] = wTime



    def AcIntention(self):
        """
        implements intention - calls action with the data for it
        """
        #FIXME here uses only the first intention from the list
        #this first intention is used for moving the body also 

        self.intentions[0]["action"](self.intentions[0]["data"], self.intentions[0])
        self.AcUpdateIntention()


    def AcUpdateIntention(self):
        """
        cleans after the intention is realized 
        """
        #clean from previous intention for now 
        self.intentions.pop(0)


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

        #save into inventory 
        self.body.inventory.append(lgOrder)     

        #here check if has an intention to go home and unload there              
    

    def DeliverLG(self, lg_order):
        """
        """
        id_ = core_tools.GetIdFrom(lg_order)
        #add GS from lg_order to the residence inventories 
        self.residence.inventory[id_] += lg_order['q']


    



    def DecFI(self, w):
        pass
        #here will check if need more credit 



        #or if want to deposit some money
        #or buy FI later 
        #ROADMAP implement savings

    def DecHK(self, wTime, w):
        """
        """
        self.UpdateHKContracts(wTime)

        #check if there are contracts left after cleaning
        if len(self.hkContracts)<=0.0:
            #offer services on the market
            self.AcOfferHK()


    def CreateContract(self, data, w):
        """
        Create contract for HK, i.e. labor contract

        
        """

        if data['type'] == core_tools.ContractTypes.HKContract:
            market = w.markets(core_tools.AgentTypes.MarketHK, self)
            contract = data
            contract['ContractLength'] = market.params['ContractLength']
            contract['timeBegin'] = w.wTime
            contract['timeEnd'] = contract['timeBegin'] + contract['ContractLength']
            self.hkContracts.append(contract)
            contract[('employer', 'agent')].GetContract(contract)
            contract['PSTransaction'] = False


    def GetContract(self, data):
        """
        """
        if data['type'] == core_tools.ContractTypes.CreditContract:
            self.fi.append(data)
        elif data['type'] == core_tools.ContractTypes.PropertyContract:
            self.fi.append(data)