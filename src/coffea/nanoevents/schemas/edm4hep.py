<<<<<<< HEAD
import re

from coffea.nanoevents import transforms
from coffea.nanoevents.schemas.base import BaseSchema, nest_jagged_forms, zip_forms
from coffea.nanoevents.util import concat

# magic numbers currently used to define cross references
# this will be updated later to make it more general
RECO_PARTICLES = 0
MC_PARTICLES = 1

TRACKSTATE_XREF = 1

_base_collection = re.compile(r".*[\#\/]+.*")
_trailing_under = re.compile(r".*_[0-9]")


class EDM4HEPSchema(BaseSchema):
    """EDM4HEP schema builder

    The EDM4HEP schema is built from all branches found in the supplied file,
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
=======
import copy
import re
import warnings

from coffea.nanoevents import transforms
from coffea.nanoevents.methods import vector
from coffea.nanoevents.schemas.base import BaseSchema, zip_forms
from coffea.nanoevents.util import concat

# Load and Parse EDM4HEP.yaml


def parse_Members_and_Relations(Members_and_Relation_List, target_text=False):
    parsed = {}
    for i in Members_and_Relation_List:
        # Separate the declaration and the comment
        separated = i.split("//", 1)
        declaration = separated[0].strip()
        doc_str = ""
        if len(separated) > 1:
            doc_str = separated[1].strip()

        type_str = declaration.split()[0]
        name_str = declaration.split()[1]

        if ("::" in declaration) and ("<" in declaration) and (">" in declaration):
            type_str = declaration.split(">", 1)[0] + ">"
            name_str = declaration.split(">", 1)[1]

        parsed[name_str.strip()] = {"type": type_str.strip(), "doc": doc_str.strip()}
        if target_text:
            parsed[name_str.strip()] = {
                "type": type_str.strip(),
                "target": type_str.strip().split("::")[1],
                "doc": doc_str.strip(),
            }
    return parsed


from coffea.nanoevents.assets import edm4hep

# with open("coffea/nanoevents/assets/edm4hep.yaml") as f:
#     edm4hep = yaml.safe_load(f)

parsed_edm4hep = copy.deepcopy(edm4hep)
for key in edm4hep.keys():
    if not isinstance(edm4hep[key], dict):
        continue
    for subkey in edm4hep[key].keys():
        if not isinstance(edm4hep[key][subkey], dict):
            continue
        for subsubkey in edm4hep[key][subkey].keys():
            if subsubkey in ["Members", "VectorMembers"]:
                parsed_edm4hep[key][subkey][subsubkey] = parse_Members_and_Relations(
                    edm4hep[key][subkey][subsubkey]
                )
            elif subsubkey in ["OneToOneRelations", "OneToManyRelations"]:
                parsed_edm4hep[key][subkey][subsubkey] = parse_Members_and_Relations(
                    edm4hep[key][subkey][subsubkey], target_text=True
                )


# Add extra datatypes
parsed_edm4hep["datatypes"]["edm4hep::ObjectID"] = (
    {  # Actually from podio, but, for parsing compatibility, keep as edm4hep
        "Description": "The Monte Carlo particle - based on the lcio::MCParticle.",
        "Author": "Prayag Yadav",
        "Members": {
            "index": {"type": "int64", "doc": "indices to the target collection"},
            "collectionID": {
                "type": "int64",
                "doc": "indices to the target collection",
            },
        },
    }
)

# Collection Regex #
# Any branch name with a forward slash '/'
# Example: 'ReconstructedParticles/ReconstructedParticles.energy'
_all_collections = re.compile(r".*[\/]+.*")

# Any branch name with '[' and ']'
# Example: 'ReconstructedParticles/ReconstructedParticles.covMatrix[10]'
_square_braces = re.compile(r".*\[.*\]")


__dask_capable__ = True


def sort_dict(d):
    """Sort a dictionary by key"""
    return {k: d[k] for k in sorted(d)}


class EDM4HEPSchema(BaseSchema):
    """
    Schema-builder for EDM4HEP root file structure.
>>>>>>> 46794a71 (EDM4HEPSchema and Newstyle FCCSchema)
    """

    __dask_capable__ = True

<<<<<<< HEAD
    _momentum_fields_e = {"energy", "momentum.x", "momentum.y", "momentum.z"}
    _momentum_fields_m = {"mass", "momentum.x", "momentum.y", "momentum.z"}

    def __init__(self, base_form, *args, **kwargs):
        super().__init__(base_form, *args, **kwargs)
        old_style_form = {
            k: v for k, v in zip(self._form["fields"], self._form["contents"])
        }
        output = self._build_collections(old_style_form)
        self._form["fields"] = [k for k in output.keys()]
        self._form["contents"] = [v for v in output.values()]

    def _build_collections(self, branch_forms):
        # Turn any special classes into the appropriate awkward form
        composite_objects = [
            k
            for k in branch_forms
            if not _base_collection.match(k) and not _trailing_under.match(k)
        ]

        composite_behavior = {  # Dictionary for overriding the default behavior
            "Tracks": "LorentzVector"
        }
        for objname in composite_objects:
            if objname not in [
                "PandoraPFOs",
                "MCParticlesSkimmed",
                "MCTruthRecoLink",
                "RecoMCTruthLink",
                "PandoraClusters",
                "MCTruthClusterLink",
                "ClusterMCTruthLink",
                "MarlinTrkTracks",
                "MCTruthMarlinTrkTracksLink",
                "MarlinTrkTracksMCTruthLink",
            ]:
                continue
            # grab the * from "objname/objname.*"
            components = {
                k[2 * len(objname) + 2 :]
                for k in branch_forms
                if k.startswith(objname + "/")
            }

            # print(components)

            if all(comp in components for comp in self._momentum_fields_e):
                form = zip_forms(
                    {
                        "x": branch_forms.pop(f"{objname}/{objname}.momentum.x"),
                        "y": branch_forms.pop(f"{objname}/{objname}.momentum.y"),
                        "z": branch_forms.pop(f"{objname}/{objname}.momentum.z"),
                        "t": branch_forms.pop(f"{objname}/{objname}.energy"),
                        "charge": branch_forms.pop(f"{objname}/{objname}.charge"),
                        "pdgId": branch_forms.pop(f"{objname}/{objname}.type"),
                    },
                    objname,
                    composite_behavior.get(objname, "RecoParticle"),
                )
                form["content"]["parameters"]["collection_name"] = objname
                branch_forms[objname] = form
            elif all(comp in components for comp in self._momentum_fields_m):
                offset_form = {
                    "class": "NumpyArray",
                    "itemsize": 8,
                    "format": "i",
                    "primitive": "int64",
                    "form_key": concat(
                        *[
                            branch_forms[f"{objname}/{objname}.momentum.x"]["form_key"],
                            "!offsets",
                        ]
                    ),
                }

                branch_forms[f"G{objname}ParentsIndex"] = transforms.local2global_form(
                    branch_forms[
                        "_MCParticlesSkimmed_parents/_MCParticlesSkimmed_parents.index"
                    ],
                    offset_form,
                )

                form = zip_forms(
                    {
                        "x": branch_forms.pop(f"{objname}/{objname}.momentum.x"),
                        "y": branch_forms.pop(f"{objname}/{objname}.momentum.y"),
                        "z": branch_forms.pop(f"{objname}/{objname}.momentum.z"),
                        "mass": branch_forms.pop(f"{objname}/{objname}.mass"),
                        "charge": branch_forms.pop(f"{objname}/{objname}.charge"),
                        "pdgId": branch_forms.pop(f"{objname}/{objname}.PDG"),
                        "parents_counts": transforms.startsandstops2counts_form(
                            branch_forms.pop(f"{objname}/{objname}.parents_begin"),
                            branch_forms.pop(f"{objname}/{objname}.parents_end"),
                        ),
                        "children_counts": transforms.startsandstops2counts_form(
                            branch_forms.pop(f"{objname}/{objname}.daughters_begin"),
                            branch_forms.pop(f"{objname}/{objname}.daughters_end"),
                        ),
                    },
                    objname,
                    composite_behavior.get(objname, "MCTruthParticle"),
                )

                form["content"]["parameters"]["collection_name"] = objname

                branch_forms[objname] = form
            elif components == {
                "fCoordinates.fX",
                "fCoordinates.fY",
                "fCoordinates.fZ",
            }:
                form = zip_forms(
                    {
                        "x": branch_forms.pop(f"{objname}/{objname}.fCoordinates.fX"),
                        "y": branch_forms.pop(f"{objname}/{objname}.fCoordinates.fY"),
                        "z": branch_forms.pop(f"{objname}/{objname}.fCoordinates.fZ"),
                    },
                    objname,
                    composite_behavior.get(objname, "ThreeVector"),
                )
                form["content"]["parameters"]["collection_name"] = objname
                branch_forms[objname] = form
            elif objname == "MCTruthRecoLink" or objname == "RecoMCTruthLink":
                pfos_offsets_src = (
                    branch_forms["PandoraPFOs/PandoraPFOs.momentum.x"]
                    if "PandoraPFOs/PandoraPFOs.momentum.x" in branch_forms
                    else branch_forms["PandoraPFOs"]
                )
                pfos_offsets_form = {
                    "class": "NumpyArray",
                    "itemsize": 8,
                    "format": "i",
                    "primitive": "int64",
                    "form_key": concat(*[pfos_offsets_src["form_key"], "!offsets"]),
                }

                mc_offsets_src = (
                    branch_forms["MCParticlesSkimmed/MCParticlesSkimmed.momentum.x"]
                    if "MCParticlesSkimmed/MCParticlesSkimmed.momentum.x"
                    in branch_forms
                    else branch_forms["MCParticlesSkimmed"]
                )
                mc_offsets_form = {
                    "class": "NumpyArray",
                    "itemsize": 8,
                    "format": "i",
                    "primitive": "int64",
                    "form_key": concat(*[mc_offsets_src["form_key"], "!offsets"]),
                }

                Greco_index_form = transforms.local2global_form(
                    branch_forms["_MCTruthRecoLink_rec/_MCTruthRecoLink_rec.index"],
                    pfos_offsets_form,
                )
                Gmc_index_form = transforms.local2global_form(
                    branch_forms["_MCTruthRecoLink_sim/_MCTruthRecoLink_sim.index"],
                    mc_offsets_form,
                )

                form = zip_forms(
                    {
                        "Greco_index": Greco_index_form,
                        "Gmc_index": Gmc_index_form,
                        "weight_mc_reco": branch_forms[
                            "MCTruthRecoLink/MCTruthRecoLink.weight"
                        ],
                        "weight_reco_mc": branch_forms[
                            "RecoMCTruthLink/RecoMCTruthLink.weight"
                        ],
                        "reco_index": branch_forms[
                            "_MCTruthRecoLink_rec/_MCTruthRecoLink_rec.index"
                        ],  # only the weights vary between "MCTruthRecoLink" and "RecoMCTruthLink"
                        "reco_collectionID": branch_forms[
                            "_MCTruthRecoLink_rec/_MCTruthRecoLink_rec.collectionID"
                        ],
                        "mc_index": branch_forms[
                            "_MCTruthRecoLink_sim/_MCTruthRecoLink_sim.index"
                        ],
                        "mc_collectionID": branch_forms[
                            "_MCTruthRecoLink_sim/_MCTruthRecoLink_sim.collectionID"
                        ],
                    },
                    objname,
                    composite_behavior.get(objname, "ParticleLink"),
                )
                branch_forms[objname] = form
            elif objname == "MCTruthClusterLink" or objname == "ClusterMCTruthLink":
                cluster_offsets_src = (
                    branch_forms["PandoraClusters/PandoraClusters.energy"]
                    if "PandoraClusters/PandoraClusters.energy" in branch_forms
                    else branch_forms["PandoraClusters"]
                )
                cluster_offsets_form = {
                    "class": "NumpyArray",
                    "itemsize": 8,
                    "format": "i",
                    "primitive": "int64",
                    "form_key": concat(*[cluster_offsets_src["form_key"], "!offsets"]),
                }

                mc_offsets_src = (
                    branch_forms["MCParticlesSkimmed/MCParticlesSkimmed.momentum.x"]
                    if "MCParticlesSkimmed/MCParticlesSkimmed.momentum.x"
                    in branch_forms
                    else branch_forms["MCParticlesSkimmed"]
                )
                mc_offsets_form = {
                    "class": "NumpyArray",
                    "itemsize": 8,
                    "format": "i",
                    "primitive": "int64",
                    "form_key": concat(*[mc_offsets_src["form_key"], "!offsets"]),
                }

                Gcluster_index_form = transforms.local2global_form(
                    branch_forms[
                        "_MCTruthClusterLink_rec/_MCTruthClusterLink_rec.index"
                    ],
                    cluster_offsets_form,
                )
                Gmc_index_form = transforms.local2global_form(
                    branch_forms[
                        "_MCTruthClusterLink_sim/_MCTruthClusterLink_sim.index"
                    ],
                    mc_offsets_form,
                )

                form = zip_forms(
                    {
                        "Gcluster_index": Gcluster_index_form,
                        "Gmc_index": Gmc_index_form,
                        "weight_mc_cluster": branch_forms[
                            "MCTruthClusterLink/MCTruthClusterLink.weight"
                        ],
                        "weight_cluster_mc": branch_forms[
                            "ClusterMCTruthLink/ClusterMCTruthLink.weight"
                        ],
                        "cluster_index": branch_forms[
                            "_MCTruthClusterLink_rec/_MCTruthClusterLink_rec.index"
                        ],
                        "cluster_collectionID": branch_forms[
                            "_MCTruthClusterLink_rec/_MCTruthClusterLink_rec.collectionID"
                        ],
                        "mc_index": branch_forms[
                            "_MCTruthClusterLink_sim/_MCTruthClusterLink_sim.index"
                        ],
                        "mc_collectionID": branch_forms[
                            "_MCTruthClusterLink_sim/_MCTruthClusterLink_sim.collectionID"
                        ],
                    },
                    objname,
                    composite_behavior.get(objname, "ParticleLink"),
                )
                branch_forms[objname] = form
            elif (
                objname == "MCTruthMarlinTrkTracksLink"
                or objname == "MarlinTrkTracksMCTruthLink"
            ):
                trk_offsets_src = (
                    branch_forms[
                        "_MarlinTrkTracks_trackStates/_MarlinTrkTracks_trackStates.omega"
                    ]
                    if "_MarlinTrkTracks_trackStates/_MarlinTrkTracks_trackStates.omega"
                    in branch_forms
                    else branch_forms["MarlinTrkTracks"]
                )
                trk_offsets_form = {
                    "class": "NumpyArray",
                    "itemsize": 8,
                    "format": "i",
                    "primitive": "int64",
                    "form_key": concat(*[trk_offsets_src["form_key"], "!offsets"]),
                }

                mc_offsets_src = (
                    branch_forms["MCParticlesSkimmed/MCParticlesSkimmed.momentum.x"]
                    if "MCParticlesSkimmed/MCParticlesSkimmed.momentum.x"
                    in branch_forms
                    else branch_forms["MCParticlesSkimmed"]
                )
                mc_offsets_form = {
                    "class": "NumpyArray",
                    "itemsize": 8,
                    "format": "i",
                    "primitive": "int64",
                    "form_key": concat(*[mc_offsets_src["form_key"], "!offsets"]),
                }

                Gtrk_index_form = transforms.local2global_form(
                    branch_forms[
                        "_MCTruthMarlinTrkTracksLink_rec/_MCTruthMarlinTrkTracksLink_rec.index"
                    ],
                    trk_offsets_form,
                )
                Gmc_index_form = transforms.local2global_form(
                    branch_forms[
                        "_MCTruthMarlinTrkTracksLink_sim/_MCTruthMarlinTrkTracksLink_sim.index"
                    ],
                    mc_offsets_form,
                )

                form = zip_forms(
                    {
                        "Gtrk_index": Gtrk_index_form,
                        "Gmc_index": Gmc_index_form,
                        "weight_mc_trk": branch_forms[
                            "MCTruthMarlinTrkTracksLink/MCTruthMarlinTrkTracksLink.weight"
                        ],
                        "weight_trk_mc": branch_forms[
                            "MarlinTrkTracksMCTruthLink/MarlinTrkTracksMCTruthLink.weight"
                        ],
                        "trk_index": branch_forms[
                            "_MCTruthMarlinTrkTracksLink_rec/_MCTruthMarlinTrkTracksLink_rec.index"
                        ],
                        "trk_collectionID": branch_forms[
                            "_MCTruthMarlinTrkTracksLink_rec/_MCTruthMarlinTrkTracksLink_rec.collectionID"
                        ],
                        "mc_index": branch_forms[
                            "_MCTruthMarlinTrkTracksLink_sim/_MCTruthMarlinTrkTracksLink_sim.index"
                        ],
                        "mc_collectionID": branch_forms[
                            "_MCTruthMarlinTrkTracksLink_sim/_MCTruthMarlinTrkTracksLink_sim.collectionID"
                        ],
                    },
                    objname,
                    composite_behavior.get(objname, "ParticleLink"),
                )
                branch_forms[objname] = form
            elif objname == "PandoraClusters":
                form = zip_forms(
                    {
                        "pt": branch_forms[f"{objname}/{objname}.energy"],
                        "theta": branch_forms.pop(f"{objname}/{objname}.iTheta"),
                        "phi": branch_forms.pop(f"{objname}/{objname}.phi"),
                        "energy": branch_forms[f"{objname}/{objname}.energy"],
                    },
                    objname,
                    composite_behavior.get(objname, "Cluster"),
                )
                form["content"]["parameters"]["collection_name"] = objname
                branch_forms[objname] = form
            elif objname == "MarlinTrkTracks":
                form = zip_forms(
                    {
                        "omega": branch_forms.pop(
                            "_MarlinTrkTracks_trackStates/_MarlinTrkTracks_trackStates.omega"
                        ),
                        "phi": branch_forms.pop(
                            "_MarlinTrkTracks_trackStates/_MarlinTrkTracks_trackStates.phi"
                        ),
                        "tanLambda": branch_forms.pop(
                            "_MarlinTrkTracks_trackStates/_MarlinTrkTracks_trackStates.tanLambda"
                        ),
                    },
                    objname,
                    composite_behavior.get(objname, "Track"),
                )
                form["content"]["parameters"]["collection_name"] = objname
                branch_forms[objname] = form
            else:
                raise ValueError(
                    f"Unrecognized class with split branches: {components}"
                )

        # Generating collection from branch name
        collections = [
            k
            for k in branch_forms
            if k
            in [
                "PandoraPFOs",
                "MCParticlesSkimmed",
                "MCTruthRecoLink",
                "RecoMCTruthLink",
                "PandoraClusters",
                "MCTruthClusterLink",
                "ClusterMCTruthLink",
                "MarlinTrkTracks",
            ]
        ]
        collections = {
            "_".join(k.split("_")[:-1])
            for k in collections
            if k.split("_")[-1] != "AK8"
            # Excluding per-event variables with AK8 variants like Mjj and MT
        }

        subcollections = []

        for cname in collections:
            items = sorted(k for k in branch_forms if k.startswith(cname + "_"))
            if len(items) == 0:
                continue

            # Special pattern parsing for <collection>_<subcollection>Counts branches
            countitems = [x for x in items if x.endswith("Counts")]
            subcols = {x[:-6] for x in countitems}  # List of subcollection names
            for subcol in subcols:
                items = [
                    k for k in items if not k.startswith(subcol) or k.endswith("Counts")
                ]
                subname = subcol[len(cname) + 1 :]
                subcollections.append(
                    {
                        "colname": cname,
                        "subcol": subcol,
                        "countname": subname + "Counts",
                        "subname": subname,
                    }
                )

            if cname not in branch_forms:
                collection = zip_forms(
                    {k[len(cname) + 1]: branch_forms.pop(k) for k in items}, cname
                )
                branch_forms[cname] = collection
            else:
                collection = branch_forms[cname]
                if not collection["class"].startswith("ListOffsetArray"):
                    print(collection["class"])
                    raise NotImplementedError(
                        f"{cname} isn't a jagged array, not sure what to do"
                    )
                for item in items:
                    Itemname = item[len(cname) + 1 :]
                    collection["content"]["fields"].append(Itemname)
                    collection["content"]["contents"].append(
                        branch_forms.pop(item)["content"]
                    )

        for sub in subcollections:
            nest_jagged_forms(
                branch_forms[sub["colname"]],
                branch_forms.pop(sub["subcol"]),
                sub["countname"],
                sub["subname"],
            )

        return branch_forms
=======
    # EDM4HEP components mixins
    _components_mixins = {
        "Vector4f": "LorentzVector",
        "Vector3f": "ThreeVector",
        "Vector3d": "ThreeVector",
        "Vector2i": "TwoVector",
        "Vector2f": "TwoVector",
        "TrackState": "TrackState",
        "Quantity": "Quantity",
        "covMatrix2f": "covMatrix",
        "covMatrix3f": "covMatrix",
        "covMatrix4f": "covMatrix",
        "covMatrix6f": "covMatrix",
    }

    # EDM4HEP datatype mixins
    _datatype_mixins = {  # Example {'TrackCollection' : 'Track', 'MCParticleCollection':'MCParticleCollection', etc}
        name.split("::")[1] + "Collection": name.split("::")[1]
        for name in parsed_edm4hep["datatypes"].keys()
        if name.split("::")[1] != "EventHeader"
    }
    _datatype_mixins["EventHeader"] = "EventHeader"

    _momentum_fields_e = {
        "energy": "E",
        "momentum.x": "px",
        "momentum.y": "py",
        "momentum.z": "pz",
    }
    _two_vec_replacement = {"a": "x", "b": "y"}
    _replacement = {**_momentum_fields_e, **_two_vec_replacement}

    copy_links_to_target_datatype = False

    # Which collection to match if there are multiple matching collections for a given datatype
    _datatype_priority = {}

    def __init__(self, base_form, *args, **kwargs):
        super().__init__(base_form)
        self._form["fields"], self._form["contents"] = self._build_collections(
            self._form["fields"], self._form["contents"]
        )

    def _zip_components(self, collection_name, component_branches, branch_forms):
        """
        Zip the members of a component collection
        Eg. referencePoint (edm4hep::Vector3f) has the referencePoint.x, referencePoint.y and referencePoint.z branches
            They are zipped together to return the referencePoint collection
        """
        inverted_dict = {}
        for name in component_branches.keys():
            var = component_branches[name]["branch_var"]
            subvar = component_branches[name]["branch_subvar"]
            type = component_branches[name]["type"]
            doc = component_branches[name]["doc"]
            if var + "@" + type not in inverted_dict.keys():
                inverted_dict[var + "@" + type] = []
            inverted_dict[var + "@" + type].append(
                {"name": name, "branch_subvar": subvar, "doc": doc}
            )

        for var, branch_list in inverted_dict.items():
            assign_name = var.split("@")[0]
            type_name = var.split("@")[1].split("::")[1]
            mixin = self._components_mixins.get(type_name, None)
            if assign_name == "momentum":
                continue  # Used to create 4 vector for the whole collection, later.
            if var.split("@")[1] == "unknown":
                continue
            # component_name = var.split("@")[1].split("::")[1]

            to_zip_raw = {
                item["branch_subvar"]: branch_forms.pop(item["name"])
                for item in branch_list
            }
            # replace keys if needed
            to_zip = {
                self._replacement.get(name, name): form
                for name, form in to_zip_raw.items()
            }

            replaced_branch = (
                collection_name + "/" + collection_name + "." + assign_name
            )
            branch_forms[replaced_branch] = zip_forms(
                sort_dict(to_zip), str(assign_name), str(mixin)
            )

            branch_forms[replaced_branch]["content"]["parameters"].update(
                {"collection_name": assign_name, "__doc__": branch_list[0]["doc"]}
            )
        return branch_forms

    def _lookup_branch(self, collection_name, branch_name, key=None):
        """
        Returns 'type' or 'doc' of a branch component, given a collection_name, branch_name and key('type' or 'doc')
        """
        datatype = self._datatype_mixins.get(collection_name, None)
        if collection_name.startswith("_"):
            col_name = collection_name[1:].split("_")[0]
            subcol_name = collection_name[1:].split("_")[1]
            datatype = self._datatype_mixins.get(col_name, None)
        if datatype is None:
            raise FileNotFoundError(f"No datatype found for {collection_name}!")
        collection_edm4hep = parsed_edm4hep["datatypes"]["edm4hep::" + datatype]
        Members = collection_edm4hep.get("Members", {})
        VectorMembers = collection_edm4hep.get("VectorMembers", {})
        OneToOneRelations = collection_edm4hep.get("OneToOneRelations", {})
        OneToManyRelations = collection_edm4hep.get("OneToOneRelations", {})
        composite_dict = {
            **Members,
            **VectorMembers,
            **OneToOneRelations,
            **OneToManyRelations,
        }
        if collection_name.startswith("_"):
            matched_subcol = composite_dict.get(
                subcol_name, {"type": "unknown", "doc": "unknown"}
            )
            components_edm4hep = parsed_edm4hep["components"].get(
                matched_subcol["type"], {"Members": {}}
            )["Members"]
            composite_dict = {**composite_dict, **components_edm4hep}

        if key is not None:
            return composite_dict.get(
                branch_name, {"type": "unknown", "doc": "unknown"}
            )[key]
        return composite_dict.get(branch_name, {"type": "unknown", "doc": "unknown"})

    def _doc_strings(self, branch_forms, collections):
        """
        Assign docstrings for all branches
        Docstrings are taken from the comments in edm4hep.yaml
        """

        def assign_doc(branch, doc):
            branch["content"]["parameters"]["__doc__"] = doc
            return branch

        fieldnames = list(branch_forms.keys())
        for collection in collections:
            for name in fieldnames:
                slash_split = name.split("/")
                if slash_split[0] == collection:
                    if (
                        len(slash_split) > 1
                    ):  # Ensure that no placeholder branch is allowed
                        branch_name_split = slash_split[1].split(".")
                        var_name = branch_name_split[1]
                        if "[" in branch_name_split[1] and "]" in branch_name_split[1]:
                            var_name = branch_name_split[1].split("[")[0]
                        # Assign doc strings to all branches
                        doc = self._lookup_branch(collection, var_name, "doc")
                        branch_forms[name] = assign_doc(branch_forms[name], doc)
        return branch_forms

    def _process_components(self, branch_forms, all_collections):
        """
        Zip all the component types (except if the component is a VectorMember for a datatype)
        """

        def _process(branch_forms, collections):
            fieldnames = branch_forms.keys()
            for collection in collections:
                component_branches = {}
                for name in fieldnames:
                    slash_split = name.split("/")
                    if slash_split[0] == collection:
                        if (
                            len(slash_split) > 1
                        ):  # Ensure that no placeholder branch is allowed
                            branch_name_split = slash_split[1].split(".")
                            if len(branch_name_split) > 2:
                                branch_var = branch_name_split[-2]
                                branch_subvar = branch_name_split[-1]
                                # skip momentum because it will be used
                                # later to create 4 vector with E or mass
                                if branch_var == "momentum":
                                    continue
                                component = self._lookup_branch(collection, branch_var)
                                component_type = component["type"]
                                component_doc = component["doc"]

                                component_branches[name] = {
                                    "type": component_type,
                                    "branch_var": branch_var,
                                    "branch_subvar": branch_subvar,
                                    "doc": component_doc,
                                }
                branch_forms = self._zip_components(
                    collection, component_branches, branch_forms
                )
            return branch_forms

        branch_forms = _process(branch_forms, all_collections)
        branch_forms = _process(
            branch_forms, all_collections
        )  # Doing it twice to deal with nested components if at all present

        return branch_forms

    def _process_VectorMembers(self, branch_forms, all_collections):
        fieldnames = list(branch_forms.keys())

        for collection in all_collections:
            if collection.startswith("_"):
                continue
            branch_var = {
                name.split("/")[1].split(".")[1]: branch_forms[name]
                for name in fieldnames
                if (name.split("/")[0] == collection) and (len(name.split("/")) > 1)
            }
            datatype = self._datatype_mixins.get(collection, None)
            if datatype is None:
                continue
            vec_members = parsed_edm4hep["datatypes"]["edm4hep::" + datatype].get(
                "VectorMembers", None
            )
            if vec_members is None:
                continue
            for member in vec_members.keys():
                target_contents = {
                    name.split("/")[1][1:].split("_")[1]: branch_forms.pop(name)
                    for name in fieldnames
                    if name.startswith(f"_{collection}_{member}")
                    and (len(name.split("/")) > 1)
                }
                begin_form = branch_var[member + "_begin"]
                branch_forms.pop(f"{collection}/{collection}.{member}_begin")
                end_form = branch_var[member + "_end"]
                branch_forms.pop(f"{collection}/{collection}.{member}_end")

                vars = list(target_contents.keys())
                if len(vars) == 0:
                    if not vec_members[member]["type"].startswith("edm4hep::"):
                        # Example : _EventHeader_weights where 'weights'
                        # is the VectorMember of 'EventHeader' datatype
                        # ('weights' not to be confused with 'weight' )
                        associated_target_form = branch_forms.get(
                            f"_{collection}_{member}", None
                        )
                        if associated_target_form is None:
                            continue
                        branch_forms.pop(f"_{collection}_{member}")
                        target_form = transforms.begin_end_mapping_form(
                            begin_form, end_form, associated_target_form
                        )
                    else:
                        raise RuntimeError(f"_{collection}_{member} not found!")
                elif len(vars) == 1:
                    target_form = transforms.begin_end_mapping_form(
                        begin_form, end_form, target_contents[vars[0]]
                    )
                else:
                    # Example : _TrackCollection_trackStates.D0, _TrackCollection_trackStates.phi, etc.
                    #  where 'trackStates' is the VectorMember of 'TrackStates' component in 'Track' datatype
                    vec_contents = {
                        name.split(".")[1]: transforms.begin_end_mapping_form(
                            begin_form, end_form, targetform
                        )
                        for name, targetform in target_contents.items()
                    }
                    vec_contents = {}
                    for name, targetform in target_contents.items():
                        if name.endswith("covMatrix"):
                            vec_contents[name.split(".")[1]] = (
                                transforms.begin_end_mapping_nested_target_form(
                                    begin_form, end_form, targetform
                                )
                            )
                        elif name.endswith("referencePoint"):
                            vec_contents[name.split(".")[1]] = (
                                transforms.begin_end_mapping_with_xyzrecord_form(
                                    begin_form, end_form, targetform
                                )
                            )
                        else:
                            vec_contents[name.split(".")[1]] = (
                                transforms.begin_end_mapping_form(
                                    begin_form, end_form, targetform
                                )
                            )
                    target_form = zip_forms(vec_contents, member)

                branch_forms[f"{collection}/{collection}.{member}"] = target_form
                branch_forms[f"{collection}/{collection}.{member}"]["content"][
                    "parameters"
                ] = {"__doc__": vec_members[member]["doc"]}

        return branch_forms

    def _process_OneToOneRelations(self, branch_forms, all_collections):
        fieldnames = list(branch_forms.keys())

        for collection in all_collections:
            if collection.startswith("_"):
                continue
            # branch_var = {
            #     name.split("/")[1].split(".")[1]: branch_forms[name]
            #     for name in fieldnames
            #     if (name.split("/")[0] == collection) and (len(name.split("/")) > 1)
            # }
            datatype = self._datatype_mixins.get(collection, None)
            if datatype is None:
                continue
            OneToOneRelations = parsed_edm4hep["datatypes"]["edm4hep::" + datatype].get(
                "OneToOneRelations", None
            )
            if OneToOneRelations is None:
                continue
            for member in OneToOneRelations.keys():
                if member in ["from", "to"]:
                    continue  # Skip Link Collections
                target_contents = {
                    name.split("/")[1][1:].split("_")[-1]: branch_forms.pop(name)
                    for name in fieldnames
                    if name.startswith(f"_{collection}_{member}")
                    and (len(name.split("/")) > 1)
                }

                vars = list(target_contents.keys())
                if not OneToOneRelations[member]["type"].startswith("edm4hep::"):
                    raise RuntimeError(
                        f"{member} does not point to a valid datatype({OneToOneRelations[member]['type']})!"
                    )
                if len(vars) == 0:
                    raise RuntimeError(f"_{collection}_{member} not found!")
                else:
                    target_datatype = OneToOneRelations[member]["type"]
                    matched_collections = [
                        collection_name
                        for collection_name, datatype in self._datatype_mixins.items()
                        if "edm4hep::" + datatype == target_datatype
                    ]
                    # Potential Bug: What if there are more than one collections with the same datatype
                    # Since We can't the collection ID from the events branch, truly matching collections
                    # seems impossible here
                    # For now, lets add the relation to all the matched collections
                    if len(matched_collections) == 0:
                        warnings.warn(
                            f"No matched collection for {target_datatype} found!\n skipping ..."
                        )
                        continue
                    for matched_collection in matched_collections:

                        # grab the offset from one of the branches of the target datatype
                        target_vars = parsed_edm4hep["datatypes"][target_datatype][
                            "Members"
                        ]
                        first_var = list(target_vars.keys())[0]
                        offset_form = branch_forms[
                            f"{matched_collection}/{matched_collection}.{first_var}"
                        ]
                        target_datatype_offset_form = {
                            "class": "NumpyArray",
                            "itemsize": 8,
                            "format": "i",
                            "primitive": "int64",
                            "form_key": concat(
                                offset_form["form_key"],
                                "!offsets",
                            ),
                        }

                        OneToOneRelations_content = {
                            name.split(".")[1]: targetform
                            for name, targetform in target_contents.items()
                        }
                        OneToOneRelations_content.update(
                            {
                                "index_Global": transforms.local2global_form(
                                    index=OneToOneRelations_content["index"],
                                    target_offsets=target_datatype_offset_form,
                                )
                            }
                        )
                        # target_form = zip_forms(OneToOneRelations_content, member)

                        # branch_forms[
                        #     f"{collection}/{collection}.{member}_idx_{matched_collection}"
                        # ] = target_form
                        # branch_forms[
                        #     f"{collection}/{collection}.{member}_idx_{matched_collection}"
                        # ]["content"]["parameters"] = {"__doc__": OneToOneRelations[member]["doc"]}

                        for name, form in OneToOneRelations_content.items():
                            branch_forms[
                                f"{collection}/{collection}.{member}_idx_{matched_collection}_{name}"
                            ] = form
                            branch_forms[
                                f"{collection}/{collection}.{member}_idx_{matched_collection}_{name}"
                            ]["content"]["parameters"] = {
                                "__doc__": OneToOneRelations[member]["doc"]
                            }

        return branch_forms

    def _process_OneToManyRelations(self, branch_forms, all_collections):
        fieldnames = list(branch_forms.keys())

        for collection in all_collections:
            if collection.startswith("_"):
                continue
            # print("\ncollection : ", collection)
            branch_var = {
                name.split("/")[1].split(".")[1]: branch_forms[name]
                for name in fieldnames
                if (name.split("/")[0] == collection) and (len(name.split("/")) > 1)
            }
            datatype = self._datatype_mixins.get(collection, None)
            if datatype is None:
                continue
            OneToManyRelations = parsed_edm4hep["datatypes"][
                "edm4hep::" + datatype
            ].get("OneToManyRelations", None)
            if OneToManyRelations is None:
                continue
            for member in OneToManyRelations.keys():
                if member in ["from", "to"]:
                    continue  # Skip Link Collections
                target_contents = {
                    name.split("/")[1][1:].split("_")[-1]: branch_forms.pop(name)
                    for name in fieldnames
                    if name.startswith(f"_{collection}_{member}")
                    and (len(name.split("/")) > 1)
                }

                # print('\nmember : ', member)
                # print('\ntarget_contents.keys() : \n', target_contents.keys())
                begin_form = branch_var[member + "_begin"]
                end_form = branch_var[member + "_end"]
                branch_forms.pop(f"{collection}/{collection}.{member}_begin")
                branch_forms.pop(f"{collection}/{collection}.{member}_end")

                vars = list(target_contents.keys())
                if not OneToManyRelations[member]["type"].startswith("edm4hep::"):
                    raise RuntimeError(
                        f"{member} does not point to a valid datatype({OneToManyRelations[member]['type']})!"
                    )
                if len(vars) == 0:
                    raise RuntimeError(f"_{collection}_{member} not found!")
                else:
                    target_datatype = OneToManyRelations[member]["type"]
                    # print('\ntarget_datatype : ', target_datatype)
                    matched_collections = [
                        collection_name
                        for collection_name, datatype in self._datatype_mixins.items()
                        if "edm4hep::" + datatype == target_datatype
                    ]
                    # Potential problem: What if there are more than one collections with the same datatype
                    # Since We can't get the collection ID from the events branch, truly matching collections
                    # seems impossible here
                    # For now, lets add the relation to all the matched collections
                    if len(matched_collections) == 0:
                        # Might be the TrackerHit Interface
                        if target_datatype in list(parsed_edm4hep["interfaces"].keys()):
                            # What datatypes does it interface to?
                            interfaced_datatypes = parsed_edm4hep["interfaces"][
                                target_datatype
                            ]["Types"]
                            matched_collections = []
                            for i in interfaced_datatypes:
                                for (
                                    col_name,
                                    datatype_name,
                                ) in self._datatype_mixins.items():
                                    if "edm4hep::" + datatype_name == i:
                                        matched_collections.append(col_name)
                        # Or maybe not
                        else:
                            raise RuntimeError(
                                f"No matched collection for {target_datatype} found!"
                            )

                    for matched_collection in matched_collections:

                        # print("\nmatched_collection : ", matched_collection)
                        # grab the offset from one of the branches of the target datatype
                        target_datatype = self._datatype_mixins.get(
                            matched_collection, None
                        )
                        if target_datatype is None:
                            raise RuntimeError()
                        # print("\ntarget_datatype : ", target_datatype)
                        target_vars = parsed_edm4hep["datatypes"][
                            "edm4hep::" + target_datatype
                        ]["Members"]
                        first_var = list(target_vars.keys())[0]
                        # print("\nfirst_var from target_vars: ", first_var)
                        offset_form = branch_forms[
                            f"{matched_collection}/{matched_collection}.{first_var}"
                        ]
                        # print(collection)
                        # print(f'{matched_collection}/{matched_collection}.{first_var}')
                        target_datatype_offset_form = {
                            "class": "NumpyArray",
                            "itemsize": 8,
                            "format": "i",
                            "primitive": "int64",
                            "form_key": concat(
                                offset_form["form_key"],
                                "!offsets",
                            ),
                        }
                        first_var = list(branch_var.keys())[0]
                        # print("\nfirst_var from branch_var: ", first_var)
                        zip_offset_form = branch_var[first_var]
                        zip_datatype_offset_form = copy.deepcopy(
                            target_datatype_offset_form
                        )
                        zip_datatype_offset_form["form_key"] = concat(
                            zip_offset_form["form_key"], "!offsets"
                        )

                        OneToManyRelations_content = {
                            name.split(".")[1]: transforms.begin_end_mapping_form(
                                begin_form, end_form, targetform
                            )
                            for name, targetform in target_contents.items()
                        }
                        # print('\nOneToManyRelations_content :\n', OneToManyRelations_content)
                        # OneToManyRelations_content_global = {
                        #     name.split(".")[1]
                        #     + "_Global": transforms.global_begin_end_range_form(
                        #         copy.deepcopy(begin_form),
                        #         copy.deepcopy(end_form),
                        #         copy.deepcopy(targetform),
                        #         copy.deepcopy(target_datatype_offset_form),
                        #     )
                        #     for name, targetform in target_contents.items()
                        #     if name.split(".")[1] == "index"
                        # }
                        OneToManyRelations_content_global = {
                            name
                            + "_Global": transforms.nested_local2global_form(
                                form,
                                target_datatype_offset_form,
                            )
                            for name, form in OneToManyRelations_content.items()
                            if name == "index"
                        }
                        # print('\nOneToManyRelations_content_global :\n', OneToManyRelations_content_global)

                        to_zip = {
                            **OneToManyRelations_content,
                            **OneToManyRelations_content_global,
                        }
                        # target_form = zip_forms(to_zip, member, offsets=zip_datatype_offset_form)

                        # branch_forms[
                        #     f"{collection}/{collection}.{member}_idx_{matched_collection}"
                        # ] = target_form
                        # branch_forms[
                        #     f"{collection}/{collection}.{member}_idx_{matched_collection}"
                        # ]["content"]["parameters"] = {"__doc__": OneToManyRelations[member]["doc"]}

                        # branch_forms[
                        #     f"Special_Branch_{member}_idx_{matched_collection}/Special_Branch_{member}_idx_{matched_collection}.{member}_idx_{matched_collection}"
                        # ] = target_form

                        for key, form in to_zip.items():
                            branch_forms[
                                f"{collection}/{collection}.{member}_idx_{matched_collection}_{key}"
                            ] = form
                            branch_forms[
                                f"{collection}/{collection}.{member}_idx_{matched_collection}_{key}"
                            ]["content"]["parameters"] = {
                                "__doc__": OneToManyRelations[member]["doc"]
                            }

        return branch_forms

    def _process_Links(self, branch_forms, all_collections):
        fieldnames = list(branch_forms.keys())

        for collection in all_collections:
            if collection.startswith("_"):
                continue
            # branch_var = {
            #     name.split("/")[1].split(".")[1]: branch_forms[name]
            #     for name in fieldnames
            #     if (name.split("/")[0] == collection) and (len(name.split("/")) > 1)
            # }
            datatype = self._datatype_mixins.get(collection, None)
            if datatype is None:
                continue
            OneToOneRelations = parsed_edm4hep["datatypes"]["edm4hep::" + datatype].get(
                "OneToOneRelations", None
            )
            if OneToOneRelations is None:
                continue
            if not all(
                link_name in OneToOneRelations.keys() for link_name in ["from", "to"]
            ):
                continue
            set_matched_collections = set()
            dict_branches_to_copy = {}
            dict_docs_of_branches = {}
            for member in OneToOneRelations.keys():
                if member in ["from", "to"]:
                    target_contents = {
                        name.split("/")[1][1:].split("_")[1]: branch_forms.pop(name)
                        for name in fieldnames
                        if name.startswith(f"_{collection}_{member}")
                        and (len(name.split("/")) > 1)
                    }

                    vars = list(target_contents.keys())
                    if not OneToOneRelations[member]["type"].startswith("edm4hep::"):
                        raise RuntimeError(
                            f"{member} does not point to a valid datatype({OneToOneRelations[member]['type']})!"
                        )
                    if len(vars) == 0:
                        raise RuntimeError(f"_{collection}_{member} not found!")
                    else:
                        target_datatype = OneToOneRelations[member]["type"]
                        matched_collections = [
                            collection_name
                            for collection_name, datatype in self._datatype_mixins.items()
                            if "edm4hep::" + datatype == target_datatype
                        ]

                        if len(matched_collections) == 0:
                            # Might be the TrackerHit Interface
                            if target_datatype in list(
                                parsed_edm4hep["interfaces"].keys()
                            ):
                                # What datatypes does it interface to?
                                interfaced_datatypes = parsed_edm4hep["interfaces"][
                                    target_datatype
                                ]["Types"]
                                matched_collections = []
                                for i in interfaced_datatypes:
                                    for (
                                        col_name,
                                        datatype_name,
                                    ) in self._datatype_mixins.items():
                                        if "edm4hep::" + datatype_name == i:
                                            matched_collections.append(col_name)
                            # Or maybe not
                            else:
                                raise RuntimeError(
                                    f"No matched collection for {target_datatype} found!"
                                )

                        for matched_collection in matched_collections:

                            # grab the offset from one of the branches of the target datatype
                            target_datatype = self._datatype_mixins.get(
                                matched_collection, None
                            )
                            if target_datatype is None:
                                raise RuntimeError()
                            target_vars = parsed_edm4hep["datatypes"][
                                "edm4hep::" + target_datatype
                            ]["Members"]
                            first_var = list(target_vars.keys())[0]
                            offset_form = branch_forms[
                                f"{matched_collection}/{matched_collection}.{first_var}"
                            ]

                            target_datatype_offset_form = {
                                "class": "NumpyArray",
                                "itemsize": 8,
                                "format": "i",
                                "primitive": "int64",
                                "form_key": concat(
                                    offset_form["form_key"],
                                    "!offsets",
                                ),
                            }

                            OneToOneRelations_content = {
                                name.split(".")[1]: targetform
                                for name, targetform in target_contents.items()
                            }
                            OneToOneRelations_content.update(
                                {
                                    "index_Global": transforms.local2global_form(
                                        index=OneToOneRelations_content["index"],
                                        target_offsets=target_datatype_offset_form,
                                    )
                                }
                            )

                            target_form = zip_forms(OneToOneRelations_content, member)
                            branch_forms[
                                f"{collection}/{collection}.Link_{member}_{matched_collection}"
                            ] = target_form
                            branch_forms[
                                f"{collection}/{collection}.Link_{member}_{matched_collection}"
                            ]["parameters"] = {
                                "__doc__": OneToOneRelations[member]["doc"]
                            }
                            # Also copy this to the matched_collections
                            # First collect all the branches that need to be copied
                            do_copy = False
                            if self.copy_links_to_target_datatype:
                                if len(self._datatype_priority.keys()) == 0:
                                    raise RuntimeError(
                                        "Cannot copy links if no priority is given!"
                                    )
                                if len(matched_collections) > 1:
                                    # Choose which one to copy
                                    priority = self._datatype_priority[target_datatype]
                                    if matched_collection == priority:
                                        do_copy = True
                                else:
                                    do_copy = True
                            if do_copy:
                                if member == "from":
                                    set_matched_collections.update({matched_collection})
                                dict_branches_to_copy.update(
                                    {f"Link_{member}_{matched_collection}": target_form}
                                )
                                dict_docs_of_branches.update(
                                    {
                                        f"Link_{member}_{matched_collection}": OneToOneRelations[
                                            member
                                        ][
                                            "doc"
                                        ]
                                    }
                                )

            # Finally, copy the available branches to the set of matched_collections
            if self.copy_links_to_target_datatype:
                for matched_collection in set_matched_collections:
                    for name in dict_branches_to_copy.keys():
                        branch_forms[
                            f"{matched_collection}/{matched_collection}.{name}"
                        ] = dict_branches_to_copy[name]
                        branch_forms[
                            f"{matched_collection}/{matched_collection}.{name}"
                        ]["content"]["parameters"] = {
                            "__doc__": dict_docs_of_branches[name]
                        }

        return branch_forms

    def _make_collections(self, output, branch_forms):
        """
        Process branches to form a collection
        Example:
            "ReconstructedParticles/ReconstructedParticles.energy",
            "ReconstructedParticles/ReconstructedParticles.charge",
            "ReconstructedParticles/ReconstructedParticles.mass",
            "ReconstructedParticles/ReconstructedParticles.referencePoint"(subcollection containing x,y,z),
            ...
            etc
            are zipped together to form the "ReconstructedParticles" collection.
        The momentum.[x,y,z] branches along with the energy branch (if available) are used to
        provide the vector.LorentzVector behavior to the collection.
        """
        field_names = list(branch_forms.keys())

        # Extract the regular collection names
        # Example collections: {'Jet', 'ReconstructedParticles', 'MCRecoAssociations', ...}
        collections = {
            collection_name.split("/")[0]
            for collection_name in field_names
            if _all_collections.match(collection_name)
        }

        # Zip the collections
        # Example: 'ReconstructedParticles'
        for name in collections:
            # Get the mixin class for the collection, if available, otherwise "NanoCollection" by default
            mixin = self._datatype_mixins.get(name, "NanoCollection")

            # Content to be zipped together
            # Example collection_content: {'type':<type form>, 'energy':<energy form>, 'momentum.x':<momentum.x form> ...}
            collection_content = {
                k[(2 * len(name) + 2) :]: branch_forms.pop(k)
                for k in field_names
                if k.startswith(f"{name}/{name}.")
            }

            # Change the name of momentum fields, to facilitate the vector.LorentzVector behavior
            # 'energy' --> 'E'
            # 'momentum.x' --> 'px'
            # 'momentum.y' --> 'py'
            # 'momentum.z' --> 'pz'
            collection_content = {
                (k.replace(k, self._replacement[k]) if k in self._replacement else k): v
                for k, v in collection_content.items()
            }

            first_var_form = collection_content[list(collection_content.keys())[0]]
            # print(f"offset variable taken for {name} : ", list(collection_content.keys())[0])
            offset_form = {
                "class": "NumpyArray",
                "itemsize": 8,
                "format": "i",
                "primitive": "int64",
                "form_key": concat(
                    first_var_form["form_key"],
                    "!offsets",
                ),
            }

            output[name] = zip_forms(
                sort_dict(collection_content),
                name,
                record_name=mixin,
                offsets=offset_form,
            )
            # Update some metadata
            if mixin != "NanoCollection":
                output[name]["content"]["parameters"].update(
                    {
                        "collection_name": name,
                        "__doc__": parsed_edm4hep["datatypes"]["edm4hep::" + mixin].get(
                            "Description", mixin
                        ),
                    }
                )

            # Remove grouping branches which are generated from BaseSchema and contain no usable info
            # Example: Along with the "Jet/Jet.type","Jet/Jet.energy",etc., BaseSchema may produce "Jet" grouping branch.
            # It is an empty branch and needs to be removed
            if name in field_names:
                branch_forms.pop(name)

        return output, branch_forms

    def _unknown_collections(self, output, branch_forms, all_collections):
        """
        Process all the unknown, empty or faulty branches that remain
        after creating all the collections.
        Should be called only after creating all the other relevant collections.

        Note: It is not a neat implementation and needs more testing.
        """
        unlisted = copy.deepcopy(branch_forms)
        for name, content in unlisted.items():
            if content["class"] == "ListOffsetArray":
                if content["content"]["class"] == "RecordArray":
                    # Remove empty branches
                    if len(content["content"]["fields"]) == 0:
                        branch_forms.pop(name)
                        continue
                elif content["content"]["class"] == "RecordArray":
                    # Remove empty branches
                    if len(content["contents"]) == 0:
                        continue
                # If a branch is non-empty and is one of its kind (i.e. has no other associated branch)
                # call it a singleton and assign it directly to the output
                else:
                    # Singleton branch
                    output[name] = branch_forms.pop(name)
            elif content["class"] == "RecordArray":
                # Remove empty branches
                if len(content["contents"]) == 0:
                    continue
                else:
                    # If the branch is not empty, try to make a collection
                    # assuming good behavior of the branch
                    # Note: It's unlike that such a branch exists

                    # Extract the collection name from the branch
                    record_name = name.split("/")[0]

                    # Contents to be zipped
                    contents = {
                        k[2 * len(record_name) + 2 :]: branch_forms.pop(k)
                        for k in unlisted.keys()
                        if k.startswith(record_name + "/")
                    }
                    if len(list(contents.keys())) == 0:
                        continue
                    output[record_name] = zip_forms(
                        sort_dict(contents),
                        record_name,
                        self._datatype_mixins.get(record_name, "NanoCollection"),
                    )
            # If a branch is non-empty and is one of its kind (i.e. has no other associated branch)
            # call it a singleton and assign it directly to the output
            else:
                output[name] = content

        return output, branch_forms

    def _build_collections(self, field_names, input_contents):
        """
        Builds all the collections with the necessary behaviors defined in the mixins dictionary
        """
        branch_forms = {k: v for k, v in zip(field_names, input_contents)}

        # All collection names
        # Example: ReconstructedParticles or _ReconstructedParticle_clusters, etc
        all_collections = {
            collection_name.split("/")[0]
            for collection_name in field_names
            if _all_collections.match(collection_name)
        }

        output = {}
        branch_forms = self._doc_strings(branch_forms, all_collections)

        branch_forms = self._process_components(branch_forms, all_collections)
        branch_forms = self._process_VectorMembers(branch_forms, all_collections)
        branch_forms = self._process_OneToOneRelations(branch_forms, all_collections)
        branch_forms = self._process_OneToManyRelations(branch_forms, all_collections)
        branch_forms = self._process_Links(branch_forms, all_collections)

        output, branch_forms = self._make_collections(output, branch_forms)

        # Process all the other unknown/faulty/empty/singleton branches
        output, branch_forms = self._unknown_collections(
            output, branch_forms, all_collections
        )

        # sort the output by key
        # output = sort_dict(branch_forms)
        output = sort_dict(output)

        return output.keys(), output.values()
>>>>>>> 46794a71 (EDM4HEPSchema and Newstyle FCCSchema)

    @classmethod
    def behavior(cls):
        """Behaviors necessary to implement this schema"""
<<<<<<< HEAD
        from coffea.nanoevents.methods import base, edm4hep, vector
=======
        from coffea.nanoevents.methods import base, edm4hep
>>>>>>> 46794a71 (EDM4HEPSchema and Newstyle FCCSchema)

        behavior = {}
        behavior.update(base.behavior)
        behavior.update(vector.behavior)
        behavior.update(edm4hep.behavior)
        return behavior
