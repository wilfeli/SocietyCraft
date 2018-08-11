#creates basic agents 
import world
import human
import bank
import firm
import institutions
import json
import os

import initSCPuzzle001



def CreateWorld():
    return world.World()


def CreateAgents(w):
    CreateHumans(w)
    CreateFirms(w)
    CreateBanks(w)

def CreateInstitutions(w):
    w.government = institutions.Government(w)


#create humans
def CreateHumans(w):
    #open file 
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    TemplateFile = 'Human.json'
    file = os.path.join(main_dir, '..', 'examples', 'SCMoneyPuzzle', TemplateFile)
    

    with open(file) as tFile:
        template = json.load(tFile)
        w.humans = [CreateHuman(template) for i in range(initSCPuzzle001.N_HUMANS)]



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

    #prepare firms for production
    initSCPuzzle001.SetupStage01Firms(w)


    #initialize markets
    for market in w._markets:
        market.StartStage01()

    for agent_ in w.firms:
        agent_.StartStage01(w)

    for agent_ in w.humans:
        agent_.StartStage01(w)
