import core_tools

class Agent(object):
    pass

class Building(object):
    def __init__(self):
        self.locationX = 0.0
        self.locationY = 0.0
        self.params = {}
        self.inventory = {}

    def GetLocation(self):
        return self.locationX, self.locationY


class Facility(Building):
    pass

class Residence(Building):
    def __init__(self):
        super().__init__()

class Depot(Building):
    """
    Place to store different things
    #TODO move storage for F into Depots 
    """
    def __init__(self):
        super().__init__()

class Office(Building):
    """
    Place where services are provided, like CB, B, G etc. 
    ROADMAP add this building as a location to B, CB, G etc.
    """
    def __init__(self, template):
        super().__init__()
        self.island = template["island"]


class PaymentSystemAgent(object):
    def __init__(self):
        pass

    @classmethod
    def AcPSCredit(cls, self_, agent_, contract, wTime, deltaTime, w):
        """
        """
        #time of previous payment 
        psTimeT_1 = self_.acTimes["PSFI"]
        #time of current payment
        psTimeT = wTime
        #length of payment period in ticks
        if contract['timeBegin'] <= psTimeT:
            if contract['timeEnd'] >= psTimeT_1:
                paymentPeriod = min(psTimeT, contract['timeEnd']) - max(psTimeT_1, contract['timeBegin']) 
                qPS = paymentPeriod * contract["interestRate"] * contract['qOutstanding']

                #interest payment
                transactionInterest = w.paymentSystem.RequestTransaction({
                    'payee':contract["issuer"], 
                    'payer':agent_, 
                    'q':qPS,
                    'currency':core_tools.ContractTypes.SCMoney})


                if transactionInterest.IsValid:
                    contract["issuer"].ReceiveMessage({
                        "q":qPS, 
                        "id": ("credit","interest"), 
                        "wTime": wTime})


                #body payment
                #FIXME doesn't care about the currency of the payment, add multiple currencies
                qPerTick = contract["qTotal"]/(contract["timeEnd"] - contract["timeBegin"])
                qPS = paymentPeriod * qPerTick

                transactionBody = w.paymentSystem.RequestTransaction({
                    'payee':contract["issuer"], 
                    'payer':agent_, 
                    'q':qPS,
                    'currency':core_tools.ContractTypes.SCMoney})


                if transactionBody.IsValid:
                    contract["qOutstanding"] -= qPS

                if contract['timeEnd'] < wTime:
                    #mark that all payments are done or not
                    #FIXME doesn't handle missing some, but not all payment gracefully
                    contract['PSTransaction'] = (transactionInterest.IsValid and transactionBody.IsValid)
            else:
                #FIXME: here just drop contract for which didn't have enough money to pay
                contract['PSTransaction'] = True
                contract['issuer'].ReceiveMessageLS(contract) 


    @classmethod
    def AcPSHK(cls, self_, agent_, contract, wTime, deltaTime, w):
        """
        """
        #time of previous payment 
        psTimeT_1 = self_.acTimes["PSHK"]
        #time of current payment
        psTimeT = wTime
        #length of payment period in ticks
        if contract["timeBegin"] <= psTimeT:
            if contract["timeEnd"] >= psTimeT_1:
                paymentPeriod = min(psTimeT, contract["timeEnd"]) - max(psTimeT_1, contract["timeBegin"]) 
                q_PS = paymentPeriod * contract["p"] * contract["q"]

                transaction = agent_.w.paymentSystem.RequestTransaction({
                    "payee":contract["employee"], 
                    "payer":contract["employer"], 
                    "q":q_PS,
                    "currency":core_tools.ContractTypes.SCMoney})
                if contract["timeEnd"] < wTime:
                    #mark that all payments are done or not
                    contract["PSTransaction"] = transaction.IsValid
            else:
                #FIXME: here just drop contract for which didn't have enough money to pay
                #with this tag it will be dropped in the next stage
                contract["PSTransaction"] = True