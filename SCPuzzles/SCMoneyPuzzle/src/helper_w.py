#creates basic agents 
import core_tools
import world
import human
import bank
import firm
import institutions
import json
import os

import initSCPuzzle001



def CreateWorld():
    w = world.World()

    #create sub worlds
    w.islands["A"] = world.Island("A", w)
    w.islands["D"] = world.Island("D", w)

    return w


def CreateAgents(w):
    CreateHumans(w)
    CreateFirms(w)
    CreateBanks(w)


def CreateInstitutions(w):
    #create government for island A
    w.government = institutions.Government({"office":{"island":"A"}}, w)

    #create government for island D
    w.islands["D"].government = institutions.Government({"office":{"island":"D"}}, w)
    w.islands["D"].government.management.params["type"] = core_tools.AgentTypes.GovernmentW

    #setup initial pile of resources
    initSCPuzzle001.CreateResourceBanks(w)

    #create regulations for island A only for now
    #TODO maybe add regulations for island D too
    initSCPuzzle001.CreateRegulations(w)



#create humans
def CreateHumans(w):
    #open file 
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    TemplateFile = 'Human.json'
    file = os.path.join(main_dir, '..', 'examples', 'SCMoneyPuzzle', TemplateFile)
    

    with open(file) as tFile:
        templates = json.load(tFile)
        #pick one template for each new H
        templateNames = list[templates.keys()]
        w.humans = [CreateHuman(templates[templateNames[core_tools.random.randrange(0, len(templateNames))]]) \
                        for i in range(initSCPuzzle001.N_HUMANS)]
        w.templates["Human"] = templates



def CreateHuman(template):
    return human.Human(template)


def CreateFirms(w):
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    TemplateFile = 'FirmBtoH.json'
    file = os.path.join(main_dir, '..', 'examples', 'SCMoneyPuzzle', TemplateFile)
    

    with open(file) as tFile:
        template = json.load(tFile)
        w.firms.extend([CreateFirm(template, w) for i in range(initSCPuzzle001.N_FIRMS)])


    TemplateFile = 'FirmFarm.json'
    file = os.path.join(main_dir, '..', 'examples', 'SCMoneyPuzzle', TemplateFile)

    with open(file) as tFile:
        template = json.load(tFile)
        w.firms.extend([CreateFirm(template, w) for i in range(initSCPuzzle001.N_FIRMS)])



def CreateFirm(template, w):
    return firm.Firm(template, w)




def CreateBanks(w):
    #open file 
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    TemplateFile = 'Bank.json'
    file = os.path.join(main_dir, '..', 'examples', 'SCMoneyPuzzle', TemplateFile)
    

    with open(file) as tFile:
        template = json.load(tFile)
        w.banks = [CreateBank(template, w) for i in range(initSCPuzzle001.N_BANKS)]

def CreateBank(template, w):
    return bank.Bank(template, w)


def CreatePhysicalMap(w):
    initSCPuzzle001.CreateBuildings(w)



def StartStages(w):
    """
    """

    #prepare firms for production, before initializations stage
    initSCPuzzle001.SetupStage01Firms(w)

    #initialize markets
    for market in w._markets:
        market.StartStage01(w)

    #TODO initialize other institutions
    w.government.StartStage01()
    w.islands["D"].government.StartStage01(w)

    #initialize banks
    for agent_ in w.banks:
        agent_.StartStage01(w)
    
    #initialize firms
    for agent_ in w.firms:
        agent_.StartStage01(w)

    #initialize H
    for agent_ in w.humans:
        agent_.StartStage01(w)


    

