import helper_w


class UI():
    def __init__(self, w):
        self.w = w
        pass


    def Life(self):
        self.w.Life()
        




if __name__ == "__main__":
    w = helper_w.CreateWorld()
    helper_w.CreateHumans(w)
    helper_w.CreateFirms(w)
    helper_w.CreateBanks(w)
    #initialize everything
    helper_w.StartStages(w)

    ui = UI(w)
    ui.Life()