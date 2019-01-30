from enum import IntEnum
import math
import numpy as np
from itertools import filterfalse
import random 

import warnings
import functools



energyContents = {
    ("Food", "Bread", "Generic"):10.0
}

energySourcesGS = [
    ("Food", "Bread", "Generic")
]


DEFAULT_P = 1.0


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)
    return new_func


ID_COUNTER = 0.0

#has correspodence str -> tuple that produced it
names_mapping = {}


def GetID(str):
    """
    splits string into internal tuple representation for an id
    """
    id_ = names_mapping.get(str)
    if id_ == None:
        id_ = tuple(str.split(':'))
        names_mapping[str] = id_
    return id_

def ReplaceKeys(content):
    """
    changes keys from string representation to the tuple representation
    """
    keysToDelete = []
    for key, value in content.items():
        content[GetID(key)] = value
        keysToDelete.append(key)

    content = { k:v for k,v in content.items() if k not in keysToDelete }

    return content


def GetIdFrom(mes):
    """
    extracts ID from the message, returns tuple
    """
    if 'brand' in mes:
        id_ = mes['type'], mes['subtype'], mes['brand']
    elif ('type' in mes) and ('subtype' in mes):
        id_ = mes['type'], mes['subtype']
    elif 'id' in mes:
        id_ = mes['id']
    else:
        id_ = None

    return id_


def GetGSFromID(gs, id_):
    """
    Returns all gs that meet the criteria 

    ("Food", "Bread", "Generic")
    ("Food", "Bread")
    ("Food",)
    """
    items = []

    #depending on the length of the id 
    for key, value in gs.items():
        if key[0:len(id_)] == id_:
            items.append(value)

    return items 


def GetDecFromID(decs, id_):
    """
    Returns all decs that meet the criteria 

    ("Food", "Bread", "Generic")
    ("Food", "Bread")
    ("Food",)
    """


    items = []

    #depending on the length of the id 
    for key, value in decs.items():
        if key[1:len(id_)] == id_:
            items.append(value)

    return items 




def GetStr(seq):
    return ':'.join(seq)



def ReadJsonTupleName(template):
    res = {}
    for key, value in template.items():
            keyInternal = GetID(key)
            res[keyInternal] = value
    return res

def ReadJsonDict(template):
    res = {}
    for key, value in template.items():
        res[key] = {}
        for keyItem, valueItem in value.items():
            keyInternal = GetID(keyItem)
            res[key][keyInternal] = valueItem
    return res


#markets
class AgentTypes(IntEnum):
    #market for packaged food
    MarketFinalFood = 0
    MarketGoodC = 1
    MarketDwelling = 2
    #market for factory's production
    MarketIntermediateFood = 3
    MarketHK = 4 
    MarketCredit = 5
    Government = 6
    MarketRawFood = 7


class FITypes(IntEnum):
    PSMoney = 0
    BMoney = 1
    Bond = 2
    Bid = 3
    Ask = 4

class ContractTypes(IntEnum):
    SCMoney = 0
    HKContract = 1
    CreditContract = 2
    PropertyContract = 3

class ContractStates(IntEnum):
    Active = 0
    Inactive = 1
    Closed = 2 

class AgentStates(IntEnum):
    Idle = 0
    Busy = 1
    Open = 2
    Closed = 3
    Dead = 4

class SimulSignals(IntEnum):
    CreateHuman = 0
    HarvestStart = 1
    HarvestEnd = 2



class WTime(object):
    
    N_TICKS_DAY = 4
    N_DAYS_MONTH = 32
    N_DAYS_WEEK = 8
    N_WEEKS_MONTH = 4
    N_SEASONS_YEAR = 4
    N_TOTAL_TICKS_WEEK = N_TICKS_DAY * N_DAYS_WEEK
    N_TOTAL_TICKS_MONTH = N_TICKS_DAY * N_DAYS_WEEK * N_WEEKS_MONTH #4*32=128 
    N_TOTAL_TICKS_YEAR = N_TOTAL_TICKS_MONTH * N_SEASONS_YEAR

    def __init__(self):
        pass
        
