import pandas as pd
import plotly.express as px
import numpy as np
import os
import plotly.graph_objs as go

default_linewidth = 1

folder1 = "128_320\\128pop_320tries_rand"
folder2 = "128_320\\128pop_320tries_rand_1tr"    
folder3 = "128_320\\128pop_320tries_rand2"
folder4 = "320pop_1000tries_rand"
folder_5 = "320t_128p_r_allhyper"
folders_128_320 = [folder1, folder2, folder3]

chunk_size = 10

def plot_data(folder):
    df = pd.read_csv(os.path.join(folder, 'data.csv'))
    print(df.shape)
    all = go.FigureWidget()
    for k in range(0, df.shape[1], chunk_size):
        fig = go.FigureWidget()
        start = k
        end = k+chunk_size
        if end > df.shape[1] - 2:
            #-2 because we add [-1] below
            end = df.shape[1] - 2

        for k in df.keys()[start:end]:
            fig.add_trace(go.Scatter(y=df[k], mode='lines', opacity=1, line={ 'width': default_linewidth }))
            all.add_trace(go.Scatter(y=df[k], mode='lines', opacity=1, line={ 'width': default_linewidth }))
            
        fig.add_trace(go.Scatter(y=df["y%d"%(df.shape[1]-1)], mode='lines',opacity=1, line={ 'width': default_linewidth }) )

        fig.show()
    
    all.add_trace(go.Scatter(y=df["y%d"%(df.shape[1]-1)], mode='lines',opacity=1, line={ 'width': default_linewidth }) )
    all.show()

plot_data(folder_5)
