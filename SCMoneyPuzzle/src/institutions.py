
class PSTransaction(object):
    def __init__(self):
        self.IsValid = False


class PaymentSystem(object):
    def __init__(self, w):
        self.w = w


    def RequestTransaction(self, transaction):
        """
        """
        #FIXME: add implementation of payment system, for now it just acts directly on accounts
        response = PSTransaction()

        psAccountFrom = transaction['payer'].GetPSMoney()[0]
        psAccountTo = transaction['payee'].GetPSMoney()[0]

        q_PS = min(psAccountFrom['q'], psAccountTo['q'])

        if q_PS >= transaction['q']:
            psAccountFrom['q'] -= transaction['q']
            psAccountTo['q'] += transaction['q']
            response.IsValid = True


        return response