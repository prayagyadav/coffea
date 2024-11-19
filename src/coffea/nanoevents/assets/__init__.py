import yaml
import os
path = os.path.abspath('src/coffea/nanoevents/assets/edm4hep.yaml')
with open(path) as f:
    edm4hep = yaml.safe_load(f)
