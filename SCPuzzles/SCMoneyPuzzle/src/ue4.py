#
# Part interacts with the UE4 engine 
#
#



import time
import ui
import threading


class UE4(object):
    def __init__(self, ui_handler):
        self.ui = ui_handler


    def Life(self, runningTime = 1000):
        """

        """
        beginTimeStamp = time.process_time()
        endTimeStamp = beginTimeStamp + runningTime/1000
        currentTimeStamp = beginTimeStamp

        while currentTimeStamp < endTimeStamp:
            #tell ui how much time has passed 
            #in seconds
            deltaTime = time.process_time() - currentTimeStamp

            self.ui.AcTick(deltaTime * 1000)

            currentTimeStamp += deltaTime




if __name__ == "__main__":
    ui_handler = ui.InitSimulation()

    #start separate thread for W
    threads = []
    t = threading.Thread(target=ui_handler.w.Life)
    threads.append(t)
    t.start()


    #time is in miliseconds
    ue4 = UE4(ui_handler)
    ue4.Life(3000)

    #TODO add termination of threads 
    #see https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/


    #plot data
    ue4.ui.GetView()

