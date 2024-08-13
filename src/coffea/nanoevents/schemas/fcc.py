import re

import copy
from sys import version
from dask_awkward.lib.core import dask_method, dask_property

from coffea.nanoevents import transforms
from coffea.nanoevents.methods.fcc import RecoParticle
from coffea.nanoevents.schemas.base import BaseSchema, nest_jagged_forms, zip_forms
from coffea.nanoevents.util import concat
from numba.cuda.args import Out

_all_collections = re.compile(r".*[\/]+.*")
# _base_collection = re.compile(r".*[\#\/]+.*")
_trailing_under = re.compile(r".*_[0-9]")
_idxs = re.compile(r".*[\#]+.*")
__dask_capable__ = True

def sort_dict(d):
    """Sort a dictionary by key"""
    return {k:d[k] for k in sorted(d)}

class FCCSchema(BaseSchema):
    """FCC schema builder

    The FCC schema is built from all branches found in the supplied file,
    based on the naming pattern of the branches.

    All collections are zipped into one `base.NanoEvents` record and
    returned.
    """

    __dask_capable__ = True

    mixins_dictionary={
        "Jet":"RecoParticle",
        "Particle":"MCTruthParticle",
        "ReconstructedParticles":"RecoParticle",
        "MissingET":"RecoParticle"
    }

    _momentum_fields_e = {"energy":"E", "momentum.x":"px", "momentum.y":"py", "momentum.z":"pz"}
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

    def __init__(self, base_form, version="latest"):
        super().__init__(base_form)

        self._form["fields"], self._form["contents"] = self._build_collections(
            self._form["fields"],
            self._form["contents"]
        )

    def _build_collections(self, field_names, input_contents):
        branch_forms = {
            k: v for k, v in zip(field_names, input_contents)
        }

        output = {}

        all_collections = {
            collection_name.split("/")[0]
            for collection_name in field_names
            if _all_collections.match(collection_name)
        }
        # print("All Collections: ", all_collections)
        collections = {
                    collection_name
                    for collection_name in all_collections
                    if not _idxs.match(collection_name) and not _trailing_under.match(collection_name)
                }
        # print("Collection: ", collections)

        #create idxs
        idxs = {
            k.split("/")[0]
            for k in all_collections
            if _idxs.match(k)
        }
        # print("idxs: ", idxs)

        for idx in idxs:
            repl = idx.replace("#","idx")
            idx_content = {
                k[2*len(idx)+2:]:branch_forms.pop(k)
                for k in field_names
                if k.startswith(f"{idx}/{idx}.")
            }
            for idx_name, idx_fill in idx_content.items():
                output[repl+"_"+idx_name] = idx_fill

        # Create other collections
        for coll_name in collections:
            print(coll_name)
            mixin = self.mixins_dictionary.get(coll_name, "NanoCollection")
            if coll_name not in self._non_empty_composite_objects:
                continue
            collection_content = {
                k[(2*len(coll_name) + 2) :]: branch_forms.pop(k)
                for k in field_names
                if k.startswith(f"{coll_name}/{coll_name}.")
            }

            #Change the name of some fields to facilitate vector and other type of object's construction
            collection_content = {(k.replace(k,self._replacement[k]) if k in self._replacement else k):v for k,v in collection_content.items() }

            output[coll_name] = zip_forms(
                sort_dict(collection_content), coll_name, mixin
            )
            output[coll_name]["content"]["parameters"].update(
                {
                    # "__doc__": branch_forms[coll_name]["parameters"]["__doc__"],
                    "collection_name": coll_name,
                }
            )

        # Unlisted Collections
        # print("Output keys before unlisted: ",output.keys())
        unlisted = {k:v for k,v in branch_forms.items() if ((k not in output.keys()) and (k not in collections)) and not _idxs.match(k)}
        # print(unlisted)
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
                    output[record_name] = zip_forms(sort_dict(contents), record_name, self.mixins_dictionary.get(record_name, "NanoCollection"))
            else: # Singletons
                output[name] = content

        #sort the output by key
        output = sort_dict(output)

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

class FCCSchema_zip_missing(BaseSchema):
    """FCC schema builder

    The FCC schema is built from all branches found in the supplied file,
    based on the naming pattern of the branches.

    All collections are zipped into one `base.NanoEvents` record and
    returned.
    """

    __dask_capable__ = True

    mixins_dictionary={
        "Jet":"RecoParticle",
        "Particle":"MCTruthParticle",
        "ReconstructedParticles":"RecoParticle",
        "MissingET":"RecoParticle"
    }

    _momentum_fields_e = {"energy":"E", "momentum.x":"px", "momentum.y":"py", "momentum.z":"pz"}
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

    def __init__(self, base_form, version="latest"):
        super().__init__(base_form)

        self._form["fields"], self._form["contents"] = self._build_collections(
            self._form["fields"],
            self._form["contents"]
        )

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

        for idx in idxs:
            repl = idx.replace("#","idx")
            # print(idx)
            content = {
                k[2*len(idx)+2:]:branch_forms.pop(k)
                for k in field_names
                if k.startswith(f"{idx}/{idx}.")
            }
            # print({k:v["offsets"] for k,v in content.items()})
            output[repl] = zip_forms(sort_dict(content), repl, self.mixins_dictionary.get(repl, "NanoCollection"))

        # Merge idxs of the same variable
        idx_collection = {k.split("#")[0]+"idx" for k in idxs}
        out = output.copy()
        for idx_c in idx_collection:
            content = {
                k:output.pop(k)
                for k in out
                if k.startswith(idx_c)
            }
            output[idx_c] = zip_forms(sort_dict(content), idx_c, self.mixins_dictionary.get(idx_c, "NanoCollection"))



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
                sort_dict(content), name, mixin
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
                    output[record_name] = zip_forms(sort_dict(contents), record_name, self.mixins_dictionary.get(record_name, "NanoCollection"))
            else: # Singletons
                output[name] = content

        #sort the output by key
        output = sort_dict(output)

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

class FCC():
    def __init__(self, version="latest", zip_missing=False):
        self._version = version
        self._zip_missing = zip_missing

    @classmethod
    def get_schema(cls, version="latest", zip_missing=False):
        if zip_missing:
            if version == "latest":
                return FCCSchema_zip_missing
            else:
                pass
        else:
            if version == "latest":
                return FCCSchema
            else:
                pass
