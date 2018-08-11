import helper_w


class UI():
    def __init__(self, w):
        self.w = w
        pass


    def Life(self):
        self.w.Life()



    def EstimatePotentialData(self):
        """
        """
        #potential production for a period
        managementType = "ManagementRawFood"
        def IsManagingFirm(agent_):
            return managementType in type(agent_.management).__name__

        firms = [firm for firm in w.firms if IsManagingFirm(firm)]

        #check Growth requirement on HK
        qPerTick = 0.0
        for agent_ in firms:
            for farm in agent_.farms:
                hkRequired = farm.actionF["GrowthF"][("HK",)] 
                if hkRequired <= 0.0:
                    #calculate final production and convert into per tick production 
                    qPerTick += ((farm.resources[("Food", "Wheat")] 
                    * farm.actionF["GrowthF"][("Theta0",)]
                    * farm.params["MaxTicks"]
                    * farm.actionF["ProductionF"][("Theta0",)])
                    / farm.params["MaxTicks"])

                else:
                    #FIXME think how to calculate max production if there HK requirements
                    pass

        print("production per tick {0:.2}".format(qPerTick))
        print("production per H per tick {0:.2}".format(qPerTick/len(w.humans)))


        #how much H there are with their HK
        qTotalHK = 0.0
        for agent_ in w.humans:
            qTotalHK += agent_.decisions[("dec", "HK")]["q"]
        
        print("potential hk supply per tick {0:.2}".format(qTotalHK))


        #who hires H
        managementType = "ManagementBtoH"
        firms = [firm for firm in w.firms if IsManagingFirm(firm)]
        qTotal = 0.0
        pqTotal = 0.0
        for agent_ in firms:
            qTotal += agent_.management.decisions[("dec","HK")]["q"]
            pqTotal += (agent_.management.decisions[("dec","HK")]["q"]
                        * agent_.management.decisions[("dec","HK")]["p"])

        print("potential hk demand per tick {0:.2}".format(qTotal))
        print("potential hk income per HK unit per tick {0:.2}".format(pqTotal/qTotalHK))


        #disposable income
        incomePotentialPerHKUnit = pqTotal/qTotalHK
        incomeDisposable = 0.0
        for agent_ in w.humans:
            incomePotential = incomePotentialPerHKUnit * agent_.decisions[("dec", "HK")]["q"]
            expensesContract = agent_.EstimateContractPS()
            incomeDisposable += (incomePotential 
                                - expensesContract)

        print("potential hk supply per tick {0:.2}".format(incomeDisposable))







        




if __name__ == "__main__":
    w = helper_w.CreateWorld()
    helper_w.CreateAgents(w)
    helper_w.CreateInstitutions(w)
    helper_w.CreatePhysicalMap(w)

    #initialize everything
    helper_w.StartStages(w)

    ui = UI(w)
    ui.Life()