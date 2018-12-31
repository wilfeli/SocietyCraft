#%%

#
# Part that will be plotting (preparing data for UE4 to display plots)
#
#


import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
#matplotlib.use('Agg')

import matplotlib.pyplot as plt


class PlotComponent(object):


    def begin_play(self):
        width = 1024
        height = 1024
        dpi = 72.0

        fig = plt.figure(1)
        fig.set_dpi(dpi)
        fig.set_figwidth(width/dpi)
        fig.set_figheight(height/dpi)

        



    def TestPlot(self, data = [], params = {}):
        # Pie chart, where the slices will be ordered and plotted counter-clockwise:
        if length(data) > 0.0:
            sizes = data
            labels = tuple(i for i in range(length(data)))
        else:
            sizes = [15, 30, 45, 10]
            labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
        explode = (0.0,) * length(sizes)
        explode[1] = 0.1 # only "explode" the 2nd slice (i.e. 'Hogs')
        

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        canvas = FigureCanvasAgg(fig1)      #This needs to remain for savefig or print_png command

        fig1.savefig("test.png", format='png')     #Produces all white background



if __name__ == "__main__":
    plot = PlotComponent()
    plot.TestPlot()
