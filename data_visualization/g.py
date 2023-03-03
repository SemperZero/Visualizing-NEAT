import webbrowser
import dash
from dash.exceptions import PreventUpdate
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import json
import plotly.graph_objs as go
app = dash.Dash(__name__)
default_linewidth = 2
highlighted_linewidth = 3

df = pd.read_csv('data.csv')

fig = go.FigureWidget()
fig.layout.hovermode = 'closest'
fig.layout.hoverdistance = -1

for k in df.keys():
    fig.add_trace(go.Scatter(y=df[k], mode='lines', opacity=0.3, line={ 'width': default_linewidth }))

fig.add_trace(go.Scatter(y=df["y%d"%(df.shape[1]-1)], mode='lines',opacity=0.3, line={ 'width': default_linewidth }) )

def update_trace(trace_index):
   # if len(points.point_inds)==1:
    i = trace_index
    print(i)
    for x in range(0,len(fig.data)):
        fig.data[x]['line']['color'] = 'grey'
        fig.data[x]['opacity'] = 0.3
        fig.data[x]['line']['width'] = default_linewidth
    fig.data[i]['line']['color'] = 'red'
    fig.data[i]['opacity'] = 1
    fig.data[i]['line']['width'] = highlighted_linewidth

for x in range(0,len(fig.data)):
    fig.data[x].on_click(update_trace)
  #  print(fig.data[x])


app.layout = html.Div(
   [
      dcc.Graph(
         id="graph_interaction",
         figure=fig,
      ),
      html.Pre(id='data')
   ]
)

@app.callback(
   Output('data', 'children'),
   Input('graph_interaction', 'clickData'))
def open_url(clickData):
   if clickData:
        update_trace(clickData["points"][0]["curveNumber"])
        #webbrowser.open(clickData["points"][0]["customdata"][0])
   else:
      raise PreventUpdate
      # return json.dumps(clickData, indent=2)
      
if __name__ == '__main__':
   app.run_server(debug=True)
   
