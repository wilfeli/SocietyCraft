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
        if len(data) > 0.0:
            sizes = data
            labels = tuple(i for i in range(len(data)))
        else:
            sizes = [15, 30, 45, 10]
            labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
        explode = [0.0,] * len(sizes)
        explode[1] = 0.1 # only "explode" the 2nd slice (i.e. 'Hogs')
        

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        canvas = FigureCanvasAgg(fig1)      #This needs to remain for savefig or print_png command

        fig1.savefig("test.png", format='png', dpi=300)     #Produces all white background



    def TSPlot(self, data = [], params = {}):
        """
        ['seaborn-dark',
        'seaborn-darkgrid',
        'seaborn-ticks',
        'fivethirtyeight',
        'seaborn-whitegrid',
        'classic',
        '_classic_test',
        'fast',
        'seaborn-talk',
        'seaborn-dark-palette',
        'seaborn-bright',
        'seaborn-pastel',
        'grayscale',
        'seaborn-notebook',
        'ggplot',
        'seaborn-colorblind',
        'seaborn-muted',
        'seaborn',
        'Solarize_Light2',
        'seaborn-paper',
        'bmh',
        'seaborn-white',
        'dark_background',
        'seaborn-poster',
        'seaborn-deep']
        """
        #Linear plot for as many lines as there are
        with plt.style.context('seaborn-whitegrid'):
        #plt.style.use('seaborn-bright')
            if len(data) > 0.0:
                ts = data
                if "x_labels" in params:
                    x_labels = params["x_labels"]
                else:
                    x_labels = [x for x in range(0, len(ts[0]), 1)]

                if "y_labels" in params:
                    y_labels = params["y_labels"]
                else:
                    y_labels = [x for x in range(0, len(ts), 1)]

            else: 
                ts = [[10, 20, 30, 40], 
                        [0.0, 10.0, 20.0, 30.0],
                        [5.0, 15.0, 25.0, 35.0]]
                x_labels = [x for x in range(0, len(ts[0]), 1)]
                y_labels = [x for x in range(0, len(ts), 1)]
            
            fig1, ax1 = plt.subplots()
            i = 0
            for datat in ts:
                ax1.plot(x_labels, datat, label = y_labels[i], alpha=.7)
                i += 1
            
            ax1.legend()
            canvas = FigureCanvasAgg(fig1)      #This needs to remain for savefig or print_png command


            fig1.savefig("test.png", format='png', transparent=True)     #Produces all white background



if __name__ == "__main__":
    plot = PlotComponent()
    plot.TSPlot()
