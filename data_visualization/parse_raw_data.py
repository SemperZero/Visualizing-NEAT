import pandas as pd
import plotly.express as px
import numpy as np
import os
import sys




folder1 = "128_320\\128pop_320tries_rand"
folder2 = "128_320\\128pop_320tries_rand_1tr"    
folder3 = "128_320\\128pop_320tries_rand2"
folder4 = "320pop_1000tries_rand"
folder5 = "320pop_100tries_15x15"
folder6 = "320t_128p_r_allhyper"

folders_128_320 = [folder1, folder2, folder3]


def parse_raw_data(folder):
    d = {}
    i=0
   # print(os.listdir(folder))
    with open(os.path.join(folder, "rez_generation_0"), 'r') as r:
        for line in reversed(r.readlines()):
            l = []
            for x in line.split("|")[1].strip()[1:-1].split(","):
                l.append(float(x))
            n = np.array(l)
            d["y%d"%i] = n
            i+=1

    df = pd.DataFrame(d)
    df.to_csv(os.path.join(folder,"data.csv"), index=False)

#for f in folders_128_320:
#    parse_raw_data(f)
parse_raw_data(folder6)




# fig = px.line(df, y="y%d"%k, line={ 'width': default_linewidth })
# for k in df.keys()[k:k+10]:
#     fig.add_scatter(y=df[k], line={ 'width': default_linewidth })
# fig.add_scatter(y=df["y%d"%(df.shape[1]-1)], line={ 'width': default_linewidth })
#fig.add_scatter(y=df["y0"])
