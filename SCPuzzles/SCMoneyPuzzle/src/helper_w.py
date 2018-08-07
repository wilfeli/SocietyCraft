#creates basic agents 
import world
import human
import bank
import firm
import json
import os


def CreateWorld():
    return world.World()


#create humans
def CreateHumans(w):
    #open file 
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    TemplateFile = 'Human.json'
    file = os.path.join(main_dir, '..', 'examples', 'SCMoneyPuzzle', TemplateFile)
    

    with open(file) as tFile:
        template = json.load(tFile)
        w.humans = [CreateHuman(template) for i in range(10)]



def CreateHuman(template):
    return human.Human(template)


def CreateFirms(w):
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    TemplateFile = 'FirmBtoH.json'
    file = os.path.join(main_dir, '..', 'examples', 'SCMoneyPuzzle', TemplateFile)
    

    with open(file) as tFile:
        template = json.load(tFile)
        w.firms.extend([CreateFirm(template, w) for i in range(3)])


    TemplateFile = 'FirmFarm.json'
    file = os.path.join(main_dir, '..', 'examples', 'SCMoneyPuzzle', TemplateFile)

    with open(file) as tFile:
        template = json.load(tFile)
        w.firms.extend([CreateFirm(template, w) for i in range(3)])



def CreateFirm(template, w):
    return firm.Firm(template, w)



#create humans
def CreateBanks(w):
    #open file 
    main_dir = os.path.split(os.path.abspath(__file__))[0]
    TemplateFile = 'Bank.json'
    file = os.path.join(main_dir, '..', 'examples', 'SCMoneyPuzzle', TemplateFile)
    

    with open(file) as tFile:
        template = json.load(tFile)
        w.banks = [CreateBank(template, w) for i in range(1)]

def CreateBank(template, w):
    return bank.Bank(template, w)


def StartStages(w):
    """
    """
    #initialize markets
    for market in w._markets:
        market.StartStage1()

    for agent_ in w.firms:
        agent_.StartStage1(w)

    for agent_ in w.humans:
        agent_.StartStage1(w)
