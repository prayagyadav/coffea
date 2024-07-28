import re

import copy

from coffea.nanoevents import transforms
from coffea.nanoevents.methods.fcc import RecoParticle
from coffea.nanoevents.schemas.base import BaseSchema, nest_jagged_forms, zip_forms
from coffea.nanoevents.util import concat

# magic numbers currently used to define cross references
# this will be updated later to make it more general
RECO_PARTICLES = 0
MC_PARTICLES = 1

TRACKSTATE_XREF = 1

_base_collection = re.compile(r".*[\#\/]+.*")
_trailing_under = re.compile(r".*_[0-9]")
_idxs = re.compile(r".*[\#]+.*")


class FCCSchema(BaseSchema):
    """FCC schema builder

    The FCC schema is built from all branches found in the supplied file,
    based on the naming pattern of the branches. There are two steps of to the
    generation of array collections:

    - Objects with vector-like quantities (momentum, coordinate points) in the
      TreeMaker ntuples are stored using ROOT PtEtaPhiEVectors and XYZPoint
      classes with maximum TTree splitting. These variable branches are grouped
      into a single collection with the original object name, with the
      corresponding coordinate variables names mapped to the standard variable
      names for coffea.nanoevents.methods.vector behaviors. For example:
      - The "Jets" branch in a TreeMaker Ntuple branch stores 'PtEtaPhiEVector's
        corresponding to the momentum of AK4 jets. The resulting collection after
        this first step would contain the vector variables in the form of
        Jets.pt, Jets.eta, Jets.phi, Jets.energy, and additional vector quantities
        (px) can be accessed via the usual vector behavior methods.
      - The "PrimaryVertices" branch in a TreeMaker Ntuple branch stores
        'XYZPoint's corresponding to the coordinates of the primary vertices, The
        resulting collection after this first step would contain the coordinate
        variables in the form of PrimaryVertices.x, PrimaryVertices.y,
        PrimaryVertices.z.

    - Extended quantities of physics objects are stored in the format
      <Object>_<variable>, such as "Jets_jecFactor". Such variables will be
      merged into the collection <Object>, so the branch "Jets_jetFactor" will be
      access to in the array format as "Jets.jecFactor". An exception to the??

    All collections are then zipped into one `base.NanoEvents` record and
    returned.
    """

    __dask_capable__ = True

    mixins_dictionary={
        "EFlowTrack":"Cluster",
        "Jet":"RecoParticle",
        "Particle":"MCTruthParticle",
        "ReconstructedParticles":"RecoParticle",
        "MissingET":"RecoParticle"
    }

    _momentum_fields_e = {"energy":"E", "momentum.x":"x", "momentum.y":"y", "momentum.z":"z"}
    _replacement = {**_momentum_fields_e}
    _non_empty_composite_objects = [
        'EFlowNeutralHadron',
        'Particle',
        'ReconstructedParticles',
        'EFlowPhoton',
        'MCRecoAssociations',
        'MissingET',
        'ParticleIDs',
        'Jet',
        'EFlowTrack'
    ]

    def __init__(self, base_form, *args, **kwargs):
        super().__init__(base_form, *args, **kwargs)
        self._form["fields"], self._form["contents"] = self._build_collections(self._form["fields"], self._form["contents"])

    def _build_collections(self, field_names, input_contents):
        branch_forms = {
            k: v for k, v in zip(field_names, input_contents)
        }
        output = {}

        # Turn any special classes into the appropriate awkward form
        collections = {
            k
            for k in field_names
            if not _base_collection.match(k) and not _trailing_under.match(k)
        }

        #create idxs
        idxs = {
            k.split("/")[0]
            for k in field_names
            if _idxs.match(k)
        }

        repls = {idx.replace("#","idx") for idx in idxs}
        for idx, repl in zip(idxs, repls):
            repl = idx.replace("#","idx")
            content = {
                k[2*len(idx)+2:]:branch_forms.pop(k)
                for k in field_names
                if k.startswith(f"{idx}/{idx}.")
            }
            output[repl] = zip_forms(content, repl, self.mixins_dictionary.get(repl, "NanoCollection"))
        # Merge idxs of the same variable
        idx_collection = {k.split("#")[0]+"idx" for k in idxs}
        out = output.copy()
        for idx_c in idx_collection:
            content = {
                k:output.pop(k)
                for k in out
                if k.startswith(idx_c)
            }
            output[idx_c] = zip_forms(content, idx_c, self.mixins_dictionary.get(idx_c, "NanoCollection"))

        # Create other collections
        for name in collections:
            mixin = self.mixins_dictionary.get(name, "NanoCollection")
            if name not in self._non_empty_composite_objects:
                continue
            content = {
                k[(2*len(name) + 2) :]: branch_forms.pop(k)
                for k in field_names
                if k.startswith(f"{name}/{name}.")
            }

            #Change the name of some fields to facilitate vector and other type of object's construction
            content = {(k.replace(k,self._replacement[k]) if k in self._replacement else k):v for k,v in content.items() }

            output[name] = zip_forms(
                content, name, mixin
            )
            output[name]["content"]["parameters"].update(
                {
                    "__doc__": branch_forms[name]["parameters"]["__doc__"],
                    "collection_name": name,
                }
            )

        # Unlisted Collections
        unlisted = {k:v for k,v in branch_forms.items() if k not in output.keys() and not _idxs.match(k)}
        for name, content in unlisted.items():
            if content["class"] == 'ListOffsetArray':
                if content["content"]["class"] == 'RecordArray':
                    if len(content["content"]["fields"]) == 0: # Remove empty branches
                        continue
            elif content["class"] == 'RecordArray':
                if len(content["contents"]) == 0 : # Remove empty branches
                    continue
                else:
                    record_name = name.split("/")[0]
                    contents = {
                        k[2*len(record_name)+2:]:branch_forms.pop(k)
                        for k in unlisted.keys()
                        if k.startswith(record_name+"/")
                    }
                    output[record_name] = zip_forms(contents, record_name, self.mixins_dictionary.get(record_name, "NanoCollection"))
            else: # Singletons
                output[name] = content

        return output.keys(), output.values()

    @classmethod
    def behavior(cls):
        """Behaviors necessary to implement this schema"""
        from coffea.nanoevents.methods import base, fcc, vector

        behavior = {}
        behavior.update(base.behavior)
        behavior.update(vector.behavior)
        behavior.update(fcc.behavior)
        return behavior
