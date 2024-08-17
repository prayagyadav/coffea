import copy
import re

from coffea.nanoevents.methods import vector
from coffea.nanoevents.schemas.base import BaseSchema, zip_forms

_all_collections = re.compile(r".*[\/]+.*")  # Any name with a forward slash /
_trailing_under = re.compile(
    r".*_[0-9]"
)  # Any name with a trailing underscore and an integer _n
_idxs = re.compile(r".*[\#]+.*")  # Any name with a hashtag #
_square_braces = re.compile(r".*\[.*\]")  # Any name with [ and ]
__dask_capable__ = True


def sort_dict(d):
    """Sort a dictionary by key"""
    return {k: d[k] for k in sorted(d)}


class FCCSchema(BaseSchema):
    """FCC schema builder

    The FCC schema is built from all branches found in the supplied file,
    based on the naming pattern of the branches.

    All collections are zipped into one `base.NanoEvents` record and
    returned.
    """

    __dask_capable__ = True

    event_ids = [
        "col_metadata",
        "evt_metadata",
        "metadata",
        "run_metadata",
    ]
    """List of FCC event IDs (Spring2021)
    """

    mixins_dictionary = {
        "Jet": "RecoParticle",
        "Particle": "MCTruthParticle",
        "ReconstructedParticles": "RecoParticle",
        "MissingET": "RecoParticle",
    }

    _momentum_fields_e = {
        "energy": "E",
        "momentum.x": "px",
        "momentum.y": "py",
        "momentum.z": "pz",
    }
    _replacement = {**_momentum_fields_e}
    _threevec_fields = {
        "position": ["position.x", "position.y", "position.z"],
        "directionError": ["directionError.x", "directionError.y", "directionError.z"],
        "vertex": ["vertex.x", "vertex.y", "vertex.z"],
        "endpoint": ["endpoint.x", "endpoint.y", "endpoint.z"],
        "referencePoint": ["referencePoint.x", "referencePoint.y", "referencePoint.z"],
        "momentumAtEndpoint": [
            "momentumAtEndpoint.x",
            "momentumAtEndpoint.y",
            "momentumAtEndpoint.z",
        ],
        "spin": ["spin.x", "spin.y", "spin.z"],
    }
    _non_empty_composite_objects = [
        "EFlowNeutralHadron",
        "Particle",
        "ReconstructedParticles",
        "EFlowPhoton",
        "MCRecoAssociations",
        "MissingET",
        "ParticleIDs",
        "Jet",
        "EFlowTrack",
    ]

    def __init__(self, base_form, version="latest"):
        super().__init__(base_form)

        self._form["fields"], self._form["contents"] = self._build_collections(
            self._form["fields"], self._form["contents"]
        )

    def _idx_collections(self, output, branch_forms, all_collections):
        field_names = list(branch_forms.keys())

        idxs = {k.split("/")[0] for k in all_collections if _idxs.match(k)}

        # Remove grouping branches which are generated from BaseSchema and contain no usable info
        _grouping_branches = {
            k: branch_forms.pop(k)
            for k in field_names
            if _idxs.match(k) and "/" not in k
        }

        for idx in idxs:
            repl = idx.replace("#", "idx")
            idx_content = {
                k[2 * len(idx) + 2 :]: branch_forms.pop(k)
                for k in field_names
                if k.startswith(f"{idx}/{idx}.")
            }
            output[repl] = zip_forms(
                sort_dict(idx_content),
                idx,
                self.mixins_dictionary.get(idx, "NanoCollection"),
            )

        return output, branch_forms

    def _main_collections(self, output, branch_forms, all_collections):
        field_names = list(branch_forms.keys())
        collections = {
            collection_name
            for collection_name in all_collections
            if not _idxs.match(collection_name)
            and not _trailing_under.match(collection_name)
        }

        # create the main collections (Eg. ReconstructedParticle, Particle, etc)
        for name in collections:
            mixin = self.mixins_dictionary.get(name, "NanoCollection")
            if name not in self._non_empty_composite_objects:
                continue

            collection_content = {
                k[(2 * len(name) + 2) :]: branch_forms.pop(k)
                for k in field_names
                if k.startswith(f"{name}/{name}.")
            }

            # Change the name of some fields to facilitate vector and other type of object's construction
            collection_content = {
                (k.replace(k, self._replacement[k]) if k in self._replacement else k): v
                for k, v in collection_content.items()
            }

            output[name] = zip_forms(sort_dict(collection_content), name, mixin)
            output[name]["content"]["parameters"].update(
                {
                    # "__doc__": branch_forms[coll_name]["parameters"]["__doc__"],
                    "collection_name": name,
                }
            )
            # Remove the grouping branch
            if name in field_names:
                branch_forms.pop(name)

        return output, branch_forms

    def _trailing_underscore_collections(self, output, branch_forms, all_collections):
        collections = {
            collection_name
            for collection_name in all_collections
            if _trailing_under.match(collection_name)
        }
        singletons = {
            collection_name
            for collection_name in branch_forms.keys()
            if _trailing_under.match(collection_name)
            and not _all_collections.match(collection_name)
        }

        for name in collections:
            mixin = self.mixins_dictionary.get(name, "NanoCollection")

            field_names = list(branch_forms.keys())
            content = {
                k[(2 * len(name) + 2) :]: branch_forms.pop(k)
                for k in field_names
                if k.startswith(f"{name}/{name}.")
            }

            output[name] = zip_forms(sort_dict(content), name, mixin)
            output[name]["content"]["parameters"].update(
                {
                    # "__doc__": branch_forms[coll_name]["parameters"]["__doc__"],
                    "collection_name": name,
                }
            )

        for name in singletons:
            output[name] = branch_forms.pop(name)

        return output, branch_forms

    def _unknown_collections(self, output, branch_forms, all_collections):
        unlisted = copy.deepcopy(branch_forms)
        for name, content in unlisted.items():
            if content["class"] == "ListOffsetArray":
                if content["content"]["class"] == "RecordArray":
                    if len(content["content"]["fields"]) == 0:  # Remove empty branches
                        # print(f"{name} ('RecordArray inside a ListOffsetArray') was empty ")
                        branch_forms.pop(name)
                        continue
                elif content["content"]["class"] == "RecordArray":
                    if len(content["contents"]) == 0:  # Remove empty branches
                        # print(f"{name} ('NumpyArray') was empty ")
                        continue
            elif content["class"] == "RecordArray":
                if len(content["contents"]) == 0:  # Remove empty branches
                    # print(f"{name} ('RecordArray') was empty ")
                    continue
                else:
                    # print(f"{name} ('RecordArray') is not empty")
                    record_name = name.split("/")[0]
                    contents = {
                        k[2 * len(record_name) + 2 :]: branch_forms.pop(k)
                        for k in unlisted.keys()
                        if k.startswith(record_name + "/")
                    }
                    output[record_name] = zip_forms(
                        sort_dict(contents),
                        record_name,
                        self.mixins_dictionary.get(record_name, "NanoCollection"),
                    )
            else:  # Singletons
                # print(f'{name} is a singleton')
                output[name] = content

        return output, branch_forms

    def _create_subcollections(self, branch_forms, all_collections):
        """Create 3-vectors, zip _begin and _end branches, zip colorFlow.a and colorFlow.a branches"""
        field_names = list(branch_forms.keys())

        # Replace square braces in a name for python naming compatibility ex. covMatrix[n] with covMatrix_n_
        for name in field_names:
            if _square_braces.match(name):
                new_name = name.replace("[", "_")
                new_name = new_name.replace("]", "_")
                branch_forms[new_name] = branch_forms.pop(name)

        # Zip _begin and _end branches
        begin_end_collection = set({})
        for name in field_names:
            if name.endswith("_begin"):
                begin_end_collection.add(name.split("_begin")[0])
            elif name.endswith("_end"):
                begin_end_collection.add(name.split("_end")[0])
        for name in begin_end_collection:
            begin_end_content = {
                k[len(name) + 1 :]: branch_forms.pop(k)
                for k in field_names
                if k.startswith(name)
            }
            branch_forms[name] = zip_forms(sort_dict(begin_end_content), name)

        # Zip colorFlow.a and colorFlow.b branches
        color_collection = set({})
        for name in field_names:
            if name.endswith("colorFlow.a"):
                color_collection.add(name.split(".a")[0])
            elif name.endswith("colorFlow.b"):
                color_collection.add(name.split(".b")[0])
        for name in color_collection:
            color_content = {
                k[len(name) + 1 :]: branch_forms.pop(k)
                for k in field_names
                if k.startswith(name)
            }
            branch_forms[name] = zip_forms(sort_dict(color_content), name)

        # Three_vectors
        for name in all_collections:
            for threevec_name, subfields in self._threevec_fields.items():
                if all(
                    f"{name}/{name}.{subfield}" in field_names for subfield in subfields
                ):
                    content = {
                        "x": branch_forms.pop(f"{name}/{name}.{threevec_name}.x"),
                        "y": branch_forms.pop(f"{name}/{name}.{threevec_name}.y"),
                        "z": branch_forms.pop(f"{name}/{name}.{threevec_name}.z"),
                    }
                    branch_forms[f"{name}/{name}.{threevec_name}"] = zip_forms(
                        sort_dict(content), threevec_name, "ThreeVector"
                    )
        return branch_forms

    def _build_collections(self, field_names, input_contents):
        branch_forms = {k: v for k, v in zip(field_names, input_contents)}

        all_collections = {
            collection_name.split("/")[0]
            for collection_name in field_names
            if _all_collections.match(collection_name)
        }

        output = {}

        branch_forms = self._create_subcollections(branch_forms, all_collections)

        output, branch_forms = self._idx_collections(
            output, branch_forms, all_collections
        )

        output, branch_forms = self._trailing_underscore_collections(
            output, branch_forms, all_collections
        )

        output, branch_forms = self._main_collections(
            output, branch_forms, all_collections
        )

        output, branch_forms = self._unknown_collections(
            output, branch_forms, all_collections
        )

        # sort the output by key
        output = sort_dict(output)

        return output.keys(), output.values()

    @classmethod
    def behavior(cls):
        """Behaviors necessary to implement this schema"""
        from coffea.nanoevents.methods import base, fcc

        behavior = {}
        behavior.update(base.behavior)
        behavior.update(vector.behavior)
        behavior.update(fcc.behavior)
        return behavior


class FCC:
    """
    Class to choose the required variant of FCCSchema
    """

    def __init__(self, version="latest"):
        self._version = version

    @classmethod
    def get_schema(cls, version="latest"):
        if version == "latest":
            return FCCSchema
        else:
            pass
