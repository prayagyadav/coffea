import json
import copy
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--file",
    help="Enter the ipynb file to be split.",
    type=str
)

inputs = parser.parse_args()

nb_name = inputs.file
outdir = nb_name.split('.')[0]+'_export'

with open(nb_name,'r') as f:
    data = f.read()
js = json.loads(data)

if not os.path.exists(outdir):
    os.makedirs(outdir)

n_cell = 1
out_nb = copy.deepcopy(js)
for cell in js['cells']:
    out_nb['cells'] = [cell]
    with open(outdir+'/'+nb_name.split('.')[0]+f'_{n_cell}.ipynb','w') as out:
        out.write(json.dumps(out_nb, indent=1))
    n_cell += 1
