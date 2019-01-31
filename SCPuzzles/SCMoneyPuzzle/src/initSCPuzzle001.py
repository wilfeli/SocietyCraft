#
# Here goes additional setting up of the simulation
#
#
#



import random

import core_tools
import agent



N_FIRMS = 3
N_HUMANS = 10
N_BANKS = 1


N_HOUSES_FIRM = 5
N_HOUSES_H = 2
N_HOUSES_LOAN = 3
N_HOUSES_G = 1



def CreateBuildings(w):
    """
    create houses for H

    assume that all humans are already created
    """

    #create buildings
    w.map.buildings = [agent.Building() for i in range(N_HOUSES_FIRM + N_HOUSES_H + N_HOUSES_LOAN + N_HOUSES_G)]

    #assign parameters
    for i in range(0,N_HOUSES_FIRM):
        #pick firm at random 
        #print(type(w.firms[0].management))

        def IsManagingFirm(agent_):
            return "ManagementBtoH" in type(agent_.management).__name__
        
        building = w.map.buildings[i]
        firms = [firm for firm in w.firms if IsManagingFirm(firm)]
        randomNumber = random.randrange(0, len(firms))

        firms[randomNumber].facilities.append(building)
        building.params['PropertyRights'] = firms[randomNumber]
        building.params['type'] = 'SFH'


    #some are occupied without loan 
    for i in range(N_HOUSES_FIRM,N_HOUSES_FIRM + N_HOUSES_H):
        #pick human at random 
        #print(type(w.firms[0].management))
        building = agent.Residence()
        #replace with residence
        w.map.buildings[i] = building
        agents = w.humans
        randomNumber = random.randrange(0, len(firms))

        #
        agents[randomNumber].residence = building
        building.params['PropertyRights'] = agents[randomNumber]
        building.params['type'] = 'SFH' 


    #some are occupied with loan 
    for i in range(N_HOUSES_FIRM + N_HOUSES_H, N_HOUSES_FIRM + N_HOUSES_H + N_HOUSES_LOAN):
        #pick human at random 
        #print(type(w.firms[0].management))
        building = agent.Residence()
        #replace with residence
        w.map.buildings[i] = building
        agents = w.humans
        randomNumber = random.randrange(0, len(firms))

        agents[randomNumber].residence = building
        agent_ = agents[randomNumber]
        building.params['PropertyRights'] = agents[randomNumber]
        building.params['type'] = 'SFH' 


        #pick random bank 
        randomNumber = random.randrange(0, len(w.banks))
    
        #FIXME no holder is assigned 
        contract = {'type':core_tools.ContractTypes.CreditContract, 
                    'qTotal': 100.0,
                    'qOutstanding': 100.0,
                    "frequencyPayment":core_tools.WTime.N_TOTAL_TICKS_WEEK,
                    "timeBegin":0,
                    "timeEnd":0 + core_tools.WTime.N_TOTAL_TICKS_MONTH,
                    "interestRate": core_tools.DEFAULT_i/core_tools.WTime.N_TOTAL_TICKS_MONTH,
                    "issuer":w.banks[randomNumber]}

        agent_.GetContract(contract)
        w.banks[randomNumber].GetContract(contract)

    #assign others to the MFH that is owned by G
    building = agent.Residence()
    #replace with residence
    w.map.buildings[N_HOUSES_FIRM + N_HOUSES_H + N_HOUSES_LOAN] = building
    building.params['PropertyRights'] = w.government
    building.params['type'] = 'MFH'


    for agent_ in w.humans:
        if agent_.residence != None:
            agent_.residence = building
            #rent contract
            contract = {"type":core_tools.ContractTypes.PropertyContract,
                        "q": 10.0,
                        "frequencyPayment":core_tools.WTime.N_TOTAL_TICKS_WEEK}

            w.government.GetContract(contract)



def CreateRegulations(w):
    """
    """
    w.government.regulations["MinCapitalRatio"] = 0.1
    w.government.regulations["FrequencyBAccounting"] = core_tools.WTime.N_TOTAL_TICKS_WEEK



def SetupStage01Firms(w):
    """
    Prepare them for production,
    including giving seeds
    """
    firms = [firm for firm in w.firms if "ManagemenRawFood" in type(firm.management)]

    for firm in firms:
        firm.gs.append({
            "type":"Food",
            "subtype":"Wheat",
            "brand":"Generic",
            "q":10.0
        })