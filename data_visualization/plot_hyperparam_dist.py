import pandas as pd
import plotly.express as px
import numpy as np
import os
import plotly.graph_objs as go



import plotly.figure_factory as ff
import numpy as np


df = pd.read_csv('distribution.csv')
print(df.shape)

hist_data = [df[k] for k in df]


group_labels = ["bias_mutate_power","bias_mutate_rate","node_add_prob","node_delete_prob","weight_mutate_power","weight_mutate_rate","survival_threshold"]

fig = ff.create_distplot(hist_data, group_labels, bin_size=.2)
fig.show()