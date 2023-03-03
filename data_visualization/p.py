import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot 

default_linewidth = 2
highlighted_linewidth = 3

df = pd.read_csv('data.csv')

fig = go.FigureWidget()
fig.layout.hovermode = 'closest'
fig.layout.hoverdistance = -1

for k in df.keys():
    fig.add_trace(go.Scatter(y=df[k], mode='lines', opacity=0.3, line={ 'width': default_linewidth }))

fig.add_trace(go.Scatter(y=df["y%d"%(df.shape[1]-1)], mode='lines',opacity=0.3, line={ 'width': default_linewidth }) )

def update_trace(trace, points, selector):
    if len(points.point_inds)==1:
        i = points.trace_index
        for x in range(0,len(fig.data)):
            fig.data[x]['line']['color'] = 'grey'
            fig.data[x]['opacity'] = 0.3
            fig.data[x]['line']['width'] = default_linewidth
        fig.data[i]['line']['color'] = 'red'
        fig.data[i]['opacity'] = 1
        fig.data[i]['line']['width'] = highlighted_linewidth

for x in range(0,len(fig.data)):
    fig.data[x].on_click(update_trace)



plot(fig)

