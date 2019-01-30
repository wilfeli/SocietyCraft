#
# Part interacts with the simulated world 
#
#




import helper_w
import core_tools
import uiPlotter

N_SIMUL_TICKS = 16
SIMUL_TIME_TICK = 1000/core_tools.WTime.N_TICKS_DAY #1 second in miliseconds has 4 simulation ticks

class UI(object):
    def __init__(self, w):
        self.w = w
        self.simulData = {}
        self.accTime = 0.0

        self.params = {}
        self.params["DebugMode"] = True

        #initialize
        self.simulData["ProductionPerTick"] = []
        self.simulData["HKSupplyPerTick"] = []
        self.simulData["HKDemandPerTick"] = []
        self.simulData["IncomePerTick"] = []
        self.simulData["CreditOutstanding"] = []



    def AcTick(self, deltaTime):
        """
        """

        self.accTime += deltaTime

        N_TICKS = self.accTime//SIMUL_TIME_TICK

        if N_TICKS > 0.0:
            #figure out how many ticks it needs to add
            for i in range(N_TICKS):
                self.w.tickQueue.put(1.0)

            self.accTime = 0.0

        if not self.w.signalQueue.empty():
            signal = self.w.signalQueue.get()
            if signal == core_tools.SimulSignals.CreateHuman:
                agent_ = helper_w.CreateHuman(self.w.templates["Human"])
                self.w.humans.append(agent_)


        #TODO have drop frame mechanizm, when if the queue is long 
        #do not add +1 tick to the world, wait until it is clear, 
        #to let W catch up 



    def GetView(self):
        """
        """
        #process data 
        data = []
        while not self.w.dataQueue.empty():
            dataPpoint = self.w.dataQueue.get()
            for key, value in dataPpoint.items():
                data[-1].append(value[0])
            data.append([])
        uiPlotter.PlotComponent().TestPlot(data)


    @core_tools.deprecated
    def Life(self):
        for i in range(N_SIMUL_TICKS):
            #run world
            self.w.LifeDebug(core_tools.WTime.N_TICKS_DAY)
            #collect data
            self.EstimatePotentialData()



    def EstimatePotentialData(self):
        """
        """
        #potential production for a period
        managementType = "ManagementRawFood"
        def IsManagingFirm(agent_):
            return managementType in type(agent_.management).__name__

        firms = [firm for firm in self.w.firms if IsManagingFirm(firm)]

        #check Growth requirement on HK
        qPerTick = 0.0
        for agent_ in firms:
            for farm in agent_.farms:
                hkRequired = farm.actionF["GrowthF"][("HK",)] 
                if hkRequired <= 0.0:
                    #calculate final production and convert into per tick production 
                    qPerTick += ((farm.resources[("Food", "Wheat", "Generic")] 
                    * farm.actionF["GrowthF"][("Theta0",)]
                    * farm.params["MaxTicks"]
                    * farm.actionF["ProductionF"][("Theta0",)])
                    / farm.params["MaxTicks"])

                else:
                    #FIXME think how to calculate max production if there are HK requirements
                    pass

        print("production per tick {0:.2}".format(qPerTick))
        print("production per H per tick {0:.2}".format(qPerTick/len(self.w.humans)))
        self.simulData["ProductionPerTick"].append(qPerTick)


        #how much H there are with their HK
        qTotalHK = 0.0
        for agent_ in self.w.humans:
            qTotalHK += agent_.decisions[("dec", "HK")]["q"]
        
        print("potential hk supply per tick {0:.2}".format(qTotalHK))
        self.simulData["HKSupplyPerTick"].append(qTotalHK)


        #who hires H
        managementType = "ManagementBtoH"
        firms = [firm for firm in self.w.firms if IsManagingFirm(firm)]
        qTotal = 0.0
        pqTotal = 0.0
        for agent_ in firms:
            qTotal += agent_.management.decisions[("dec","HK")]["q"]
            pqTotal += (agent_.management.decisions[("dec","HK")]["q"]
                        * agent_.management.decisions[("dec","HK")]["p"])

        print("potential hk demand per tick {0:.2}".format(qTotal))
        print("potential hk income per HK unit per tick {0:.2}".format(pqTotal/qTotalHK))
        self.simulData["HKDemandPerTick"].append(qTotal)


        #disposable income
        incomePotentialPerHKUnit = pqTotal/qTotalHK
        incomeDisposable = 0.0
        for agent_ in self.w.humans:
            incomePotential = incomePotentialPerHKUnit * agent_.decisions[("dec", "HK")]["q"]
            expensesContract = agent_.EstimateContractPS()
            incomeDisposable += (incomePotential 
                                - expensesContract)

        print("disposable income per tick {0:.2}".format(incomeDisposable))
        self.simulData["IncomePerTick"].append(incomeDisposable)


        banks = self.w.banks
        creditOutstanding = 0.0
        for agent_ in banks:
            for fi in agent_.fi:
                if fi["type"] == core_tools.ContractTypes.CreditContract:
                    creditOutstanding += fi["qOutstanding"]

        print("total credits outstanding {0:.2}".format(creditOutstanding))
        self.simulData["CreditOutstanding"].append(creditOutstanding)




        #TODO
        #save data for being displayed in historical figures





def InitAndRunSimulation():
    ui = InitSimulation()
    RunSimulation(ui, 16)


def InitSimulation():
    w = helper_w.CreateWorld()
    helper_w.CreateAgents(w)
    helper_w.CreateInstitutions(w)
    helper_w.CreatePhysicalMap(w)

    #initialize everything
    helper_w.StartStages(w)

    ui = UI(w)
    w.SetUI(ui)
    return ui

def RunSimulation(ui, nSimulTicks = 16):
    N_SIMUL_TICKS = nSimulTicks
    ui.Life()






if __name__ == "__main__":
    InitAndRunSimulation()