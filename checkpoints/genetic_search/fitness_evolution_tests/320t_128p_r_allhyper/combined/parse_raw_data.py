import pandas as pd
import plotly.express as px
import numpy as np
import os
import sys



d = {}
i=0
# print(os.listdir(folder))
with open("rez_generation_0_s", 'r') as r:
    for line in reversed(r.readlines()):
        l = []
        for x in line.split("|")[1].strip()[1:-1].split(","):
            l.append(float(x))
        n = np.array(l)
        d["y%d"%i] = n
        i+=1

df = pd.DataFrame(d)
df.to_csv("data.csv", index=False)


