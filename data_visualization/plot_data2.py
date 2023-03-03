import pandas as pd
import plotly.express as px
import numpy as np
import os
import plotly.graph_objs as go


folder1 = "128_320\\128pop_320tries_rand"
folder2 = "128_320\\128pop_320tries_rand_1tr"    
folder3 = "128_320\\128pop_320tries_rand2"

folders_128_320 = [folder1, folder2, folder3]

default_linewidth = 2
highlighted_linewidth_delta = 2




# we need to add the on_click event to each trace separately       


def plot_data(folder):
    df = pd.read_csv(os.path.join(folder, 'data.csv'))
   
    print(df.shape)
    for k in range(0, df.shape[1], 10):
        f = go.FigureWidget()
        f.layout.hovermode = 'closest'
        

        for k in df.keys()[k:k+10]:
            f.add_scatter(go.Scatter(y=df[k], mode='lines', line={ 'width': default_linewidth }))
        
        f.add_scatter(go.Scatter(y=df["y%d"%(df.shape[1]-1)], mode='lines', line={ 'width': default_linewidth }) )
        #fig.add_scatter(y=df["y0"])
        def update_trace(trace, points, selector):
            # this list stores the points which were clicked on
            # in all but one trace they are empty
            if len(points.point_inds) == 0:
                return          
            for i,_ in enumerate(f.data):
                f.data[i]['line']['width'] = default_linewidth + highlighted_linewidth_delta * (i == points.trace_index)

        for i in range( len(f.data) ):
            f.data[i].on_click(update_trace)
        f.show()

plot_data(folder2)
