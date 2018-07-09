from enum import IntEnum
import math
import numpy as np
from itertools import filterfalse
import random 

#has correspodence str -> tuple that produced it
names_mapping = {}


def GetID(str):
    id_ = names_mapping.get(str)
    if id_ == None:
        id_ = tuple(str.split(':'))
        names_mapping[str] = id_
    return id_

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


def GetStr(seq):
    return ':'.join(seq)


#markets
class AgentTypes(IntEnum):
    #market for processed food
    MarketFood = 0
    MarketGoodC = 1
    MarketDwelling = 2
    #market for farm's production
    MarketRawFood = 3
    MarketHK = 4 


class FITypes(IntEnum):
    PSMoney = 0
    BMoney = 1
    Bond = 2
    Bid = 3
    Ask = 4

class ContractTypes(IntEnum):
    SCMoney = 0
    HKContract = 1

class ContractStates(IntEnum):
    Active = 0
    Inactive = 1
    Closed = 2 

class AgentStates(IntEnum):
    Idle = 0
    Busy = 1
    Open = 2
    Closed = 3




class WTime(object):
    
    N_TICKS_DAY = 4
    N_DAYS_MONTH = 32
    N_DAYS_WEEK = 8
    N_WEEKS_MONTH = 4
    N_SEASONS_YEAR = 4
    N_TOTAL_TICKS_WEEK = N_TICKS_DAY * N_DAYS_WEEK
    N_TOTAL_TICKS_MONTH = N_TICKS_DAY * N_DAYS_WEEK * N_WEEKS_MONTH
    N_TOTAL_TICKS_YEAR = N_TOTAL_TICKS_MONTH * N_SEASONS_YEAR

    def __init__(self):
        pass
        
