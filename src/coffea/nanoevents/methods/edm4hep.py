import awkward
<<<<<<< HEAD
import dask_awkward
import numpy

from coffea.nanoevents.methods import base, vector

PION_MASS = 0.13957018  # GeV

behavior = {}


@awkward.mixin_class(behavior)
class MCTruthParticle(vector.LorentzVectorM, base.NanoCollection):
    """Generated Monte Carlo particles."""

    @property
    def matched_pfos(self, _dask_array_=None):
        """Returns an array of matched reconstructed particle objects for each generator particle."""
        if _dask_array_ is not None:
            collection_name = self.layout.purelist_parameter("collection_name")
            original_from = self.behavior["__original_array__"]()[collection_name]
            original = self.behavior["__original_array__"]().PandoraPFOs
            return original._apply_global_mapping(
                _dask_array_,
                original_from,
                self.behavior["__original_array__"]().RecoMCTruthLink.Gmc_index,
                self.behavior["__original_array__"]().RecoMCTruthLink.Greco_index,
                _dask_array_=original,
            )
        raise RuntimeError("Not reachable in dask mode!")

    @property
    def matched_clusters(self, _dask_array_=None):
        """Returns an array of matched cluster particle objects for each generator particle."""
        if _dask_array_ is not None:
            collection_name = self.layout.purelist_parameter("collection_name")
            original_from = self.behavior["__original_array__"]()[collection_name]
            original = self.behavior["__original_array__"]().PandoraClusters
            return original._apply_global_mapping(
                _dask_array_,
                original_from,
                self.behavior["__original_array__"]().ClusterMCTruthLink.Gmc_index,
                self.behavior["__original_array__"]().ClusterMCTruthLink.Gcluster_index,
                _dask_array_=original,
            )
        raise RuntimeError("Not reachable in dask mode!")

    @property
    def matched_trks(self, _dask_array_=None):
        """Returns an array of matched cluster particle objects for each generator particle."""
        if _dask_array_ is not None:
            collection_name = self.layout.purelist_parameter("collection_name")
            original_from = self.behavior["__original_array__"]()[collection_name]
            original = self.behavior["__original_array__"]().MarlinTrkTracks
            return original._apply_global_mapping(
                _dask_array_,
                original_from,
                self.behavior[
                    "__original_array__"
                ]().MarlinTrkTracksMCTruthLink.Gmc_index,
                self.behavior[
                    "__original_array__"
                ]().MarlinTrkTracksMCTruthLink.Gtrk_index,
                _dask_array_=original,
            )
        raise RuntimeError("Not reachable in dask mode!")

    def _apply_nested_global_index(self, index, nested_counts, _dask_array_=None):
        """As _apply_global_index but expects one additional layer of nesting to get specified."""
        if isinstance(index, int):
            out = self._content()[index]
            return awkward.Record(out, behavior=self.behavior)

        def flat_take(layout):
            idx = awkward.Array(layout)
            return self._content()[idx.mask[idx >= 0]]

        def descend(layout, depth, **kwargs):
            if layout.purelist_depth == 1:
                return flat_take(layout)

        (index_out,) = awkward.broadcast_arrays(
            index._meta if isinstance(index, dask_awkward.Array) else index
        )
        nested_counts_out = (
            nested_counts._meta
            if isinstance(nested_counts, dask_awkward.Array)
            else nested_counts
        )
        index_out = awkward.unflatten(
            index_out, awkward.flatten(nested_counts_out), axis=-1
        )
        layout_out = awkward.transform(descend, index_out.layout, highlevel=False)
        out = awkward.Array(layout_out, behavior=self.behavior)

        if isinstance(index, dask_awkward.Array):
            return _dask_array_.map_partitions(
                base._ClassMethodFn("_apply_nested_global_index"),
                index,
                nested_counts,
                label="_apply_nested_global_index",
                meta=out,
            )
        return out

    @property
    def parents(self, _dask_array_=None):
        if _dask_array_ is not None:
            collection_name = self.layout.purelist_parameter("collection_name")
            original = self.behavior["__original_array__"]()[collection_name]
            return original._apply_nested_global_index(
                self.behavior["__original_array__"]().GMCParticlesSkimmedParentsIndex,
                original.parents_counts,
                _dask_array_=original,
            )
        raise RuntimeError("Not reachable in dask mode!")

    @property
    def children(self, _dask_array_=None):
        if _dask_array_ is not None:
            collection_name = self.layout.purelist_parameter("collection_name")
            original = self.behavior["__original_array__"]()[collection_name]
            return original._apply_nested_global_index(
                self.behavior["__original_array__"]().GMCParticlesSkimmedParentsIndex,
                original.children_counts,
                _dask_array_=original,
            )
        raise RuntimeError("Not reachable in dask mode!")


@awkward.mixin_class(behavior)
class RecoParticle(vector.LorentzVector, base.NanoCollection):
    """Reconstructed particles."""

    @property
    def matched_gen(self, _dask_array_=None):
        """Returns an array of matched generator particle objects for each reconstructed particle."""
        if _dask_array_ is not None:
            collection_name = self.layout.purelist_parameter("collection_name")
            original_from = self.behavior["__original_array__"]()[collection_name]
            original = self.behavior["__original_array__"]().MCParticlesSkimmed
            return original._apply_global_mapping(
                _dask_array_,
                original_from,
                self.behavior["__original_array__"]().RecoMCTruthLink.Greco_index,
                self.behavior["__original_array__"]().RecoMCTruthLink.Gmc_index,
                _dask_array_=original,
            )
        raise RuntimeError("Not reachable in dask mode!")


@awkward.mixin_class(behavior)
class Cluster(vector.PtThetaPhiELorentzVector, base.NanoCollection):
    """Clusters."""

    @property
    def matched_gen(self, _dask_array_=None):
        """Returns an array of matched generator particle objects for each cluster."""
        if _dask_array_ is not None:
            collection_name = self.layout.purelist_parameter("collection_name")
            original_from = self.behavior["__original_array__"]()[collection_name]
            original = self.behavior["__original_array__"]().MCParticlesSkimmed
            return original._apply_global_mapping(
                _dask_array_,
                original_from,
                self.behavior["__original_array__"]().ClusterMCTruthLink.Gcluster_index,
                self.behavior["__original_array__"]().ClusterMCTruthLink.Gmc_index,
                _dask_array_=original,
            )
        raise RuntimeError("Not reachable in dask mode!")


@awkward.mixin_class(behavior)
class Track(vector.LorentzVectorM, base.NanoEvents, base.NanoCollection):
    """Tracks."""

    @property
    def matched_gen(self, _dask_array_=None):
        """Returns an array of matched generator particle objects for each track."""
        if _dask_array_ is not None:
            collection_name = self.layout.purelist_parameter("collection_name")
            original_from = self.behavior["__original_array__"]()[collection_name]
            original = self.behavior["__original_array__"]().MCParticlesSkimmed
            return original._apply_global_mapping(
                _dask_array_,
                original_from,
                self.behavior[
                    "__original_array__"
                ]().MarlinTrkTracksMCTruthLink.Gtrk_index,
                self.behavior[
                    "__original_array__"
                ]().MarlinTrkTracksMCTruthLink.Gmc_index,
                _dask_array_=original,
            )
        raise RuntimeError("Not reachable in dask mode!")

    @property
    def pt(self):
        r"""transverse momentum
        mag :: magnetic field strength in T

        source: https://github.com/PandoraPFA/MarlinPandora/blob/master/src/TrackCreator.cc#LL521
        """
        metadata = self.behavior["__original_array__"]().get_metadata()

        if metadata is None or "b_field" not in metadata.keys():
            print(
                "Track momentum requires value of magnetic field. \n"
                "Please have 'metadata' argument in from_root function have"
                "key 'b_field' with the value of magnetic field."
            )
            raise ValueError(
                "Track momentum requires value of magnetic field. \n"
                "Please have 'metadata' argument in from_root function have"
                "key 'b_field' with the value of magnetic field."
            )
        else:
            b_field = metadata["b_field"]
            return b_field * 2.99792e-4 / numpy.abs(self["omega"])

    @property
    def phi(self):
        r"""x momentum"""
        return self["phi"]

    @property
    def x(self):
        r"""x momentum"""
        return numpy.cos(self["phi"]) * self.pt

    @property
    def y(self):
        r"""y momentum"""
        return numpy.sin(self["phi"]) * self.pt

    @property
    def z(self):
        r"""z momentum"""
        return self["tanLambda"] * self.pt

    @property
    def mass(self):
        r"""mass of the track - assumed to be the mass of a pion
        source: https://github.com/iLCSoft/MarlinTrk/blob/c53d868979ef6db26077746ce264633819ffcf4f/src/MarlinAidaTTTrack.cc#LL54C3-L58C3
        """
        return PION_MASS * awkward.ones_like(self["omega"])


@awkward.mixin_class(behavior)
class ParticleLink(base.NanoCollection):
    """MCRecoParticleAssociation objects."""

    @property
    def reco_mc_index(self):
        """
        returns an array of indices mapping to generator particles for each reconstructed particle
        """
        arr_reco = self.reco_index
        arr_mc = self.mc_index

        # this is just to shape the index array properly
        sorted_reco = arr_reco[awkward.argsort(arr_reco)]
        sorted_mc = arr_mc[awkward.argsort(arr_reco)]
        proper_indices = awkward.unflatten(
            sorted_mc, awkward.flatten(awkward.run_lengths(sorted_reco), axis=1), axis=1
        )

        return proper_indices

    @property
    def debug_index_shaping(self):
        """
        function acting as a canned reproducer of the source of the problem in the above function
        **just for debugging purposes**
        """
        arr_reco = self.reco_index
        arr_mc = self.mc_index

        sorted_reco = arr_reco[awkward.argsort(arr_reco)]
        sorted_mc = arr_mc[awkward.argsort(arr_reco)]

        print(sorted_reco, sorted_mc)

        return sorted_reco  # only return one due to type constraints
=======
import numpy
from dask_awkward.lib.core import dask_method, dask_property

from coffea.nanoevents.methods import base, vector
from coffea.nanoevents.methods.base import _ClassMethodFn

behavior = {}
behavior.update(base.behavior)


class _EDM4HEPEvents(behavior["NanoEvents"]):
    def __repr__(self):
        return "EDM4HEP-Event"


behavior["NanoEvents"] = _EDM4HEPEvents


def _set_repr_name(classname):
    def namefcn(self):
        return classname

    behavior[classname].__repr__ = namefcn


@awkward.mixin_class(behavior)
class edm4hep_nanocollection(base.NanoCollection):
    """Modified NanoCollection for EDM4HEP"""

    @dask_method
    def _apply_nested_global_index(self, index):
        # extract the shape of the index
        counts1 = awkward.num(index, axis=1)
        counts2 = awkward.flatten(awkward.num(index, axis=2), axis=1)
        if index.ndim == 4:
            counts3 = awkward.ravel(awkward.num(index, axis=3))

        # Apply the flat index
        out = self._apply_global_index(awkward.ravel(index))

        # Rebuild the shape of the index
        if index.ndim == 4:
            out = awkward.unflatten(out, counts3, axis=0)
        out = awkward.unflatten(out, counts2, axis=0)
        out = awkward.unflatten(out, counts1, axis=0)

        return out

    @_apply_nested_global_index.dask
    def _apply_nested_global_index(self, dask_array, index):
        return dask_array.map_partitions(
            _ClassMethodFn("_apply_nested_global_index"),
            index,
            label="apply_nested_global_index",
        )

    @dask_property
    def List_Relations(self):
        """List all the branches that are for OneToOneRelations or OneToManyRelations"""
        idxs = {name for name in self.fields if "_idx_" in name}
        return idxs

    @List_Relations.dask
    def List_Relations(self, dask_array):
        """List all the branches that are for OneToOneRelations or OneToManyRelations"""
        idxs = {name for name in dask_array.fields if "_idx_" in name}
        return idxs

    @dask_method
    def Map_Relation(self, generic_name, target_name):
        name_struct = generic_name + "_idx_" + target_name + "_index_Global"
        idx_field_names = [name for name in self.fields if name_struct in name]
        if len(idx_field_names) == 0:
            raise FileNotFoundError(
                f"*{name_struct} not found in the current collection"
            )
        elif len(idx_field_names) > 1:
            raise RuntimeError(f"More than one field available for *{name_struct}!")

        index = self[idx_field_names[0]]
        if index.ndim == 2:
            return self._events()[target_name]._apply_global_index(index)
        elif index.ndim == 3 or index.ndim == 4:
            return self._events()[target_name]._apply_nested_global_index(index)
        else:
            raise RuntimeError(f"Index is highly nested!\n{index}")

    @Map_Relation.dask
    def Map_Relation(self, dask_array, generic_name, target_name):
        name_struct = generic_name + "_idx_" + target_name + "_index_Global"
        idx_field_names = [name for name in dask_array.fields if name_struct in name]
        if len(idx_field_names) == 0:
            raise FileNotFoundError(
                f"*{name_struct} not found in the current collection"
            )
        elif len(idx_field_names) > 1:
            raise RuntimeError(f"More than one field available for *{name_struct}!")

        index = dask_array[idx_field_names[0]]
        if index.ndim == 2:
            return dask_array._events()[target_name]._apply_global_index(index)
        elif index.ndim == 3 or index.ndim == 4:
            return dask_array._events()[target_name]._apply_nested_global_index(index)
        else:
            raise RuntimeError(f"Index is highly nested!\n{index}")

    @dask_property
    def List_Links(self):
        """List all the branches that are Links"""
        idxs = {
            name
            for name in self.fields
            if (("Link_from" in name) or ("Link_to" in name))
        }
        return idxs

    @List_Links.dask
    def List_Links(self, dask_array):
        """List all the branches that are Links"""
        idxs = {
            name
            for name in dask_array.fields
            if (("Link_from" in name) or ("Link_to" in name))
        }
        return idxs

    @dask_method
    def Map_Link(self, generic_name, target_name):
        idx_field_name = "Link_" + generic_name + "_" + target_name
        if idx_field_name not in self.fields:
            raise FileNotFoundError(
                f"{idx_field_name} not found in the current collection"
            )
        return self._events()[target_name]._apply_global_index(
            self[idx_field_name]["index_Global"]
        )

    @Map_Link.dask
    def Map_Link(self, dask_array, generic_name, target_name):
        idx_field_name = "Link_" + generic_name + "_" + target_name
        if idx_field_name not in dask_array.fields:
            raise FileNotFoundError(
                f"{idx_field_name} not found in the current collection"
            )
        return dask_array._events()[target_name]._apply_global_index(
            dask_array[idx_field_name]["index_Global"]
        )


behavior.update(
    awkward._util.copy_behaviors(base.NanoCollection, edm4hep_nanocollection, behavior)
)


@awkward.mixin_class(behavior)
class MomentumCandidate(vector.LorentzVector):
    """A Lorentz vector with charge

    This mixin class requires the parent class to provide items `px`, `py`, `pz`, `E`, and `charge`.
    """

    @awkward.mixin_class_method(numpy.add, {"MomentumCandidate"})
    def add(self, other):
        """Add two candidates together elementwise using `px`, `py`, `pz`, `E`, and `charge` components"""
        return awkward.zip(
            {
                "px": self.px + other.px,
                "py": self.py + other.py,
                "pz": self.pz + other.pz,
                "E": self.E + other.E,
                "charge": self.charge + other.charge,
            },
            with_name="MomentumCandidate",
            behavior=self.behavior,
        )

    def sum(self, axis=-1):
        """Sum an array of vectors elementwise using `px`, `py`, `pz`, `E`, and `charge` components"""
        return awkward.zip(
            {
                "px": awkward.sum(self.px, axis=axis),
                "py": awkward.sum(self.py, axis=axis),
                "pz": awkward.sum(self.pz, axis=axis),
                "E": awkward.sum(self.E, axis=axis),
                "charge": awkward.sum(self.charge, axis=axis),
            },
            with_name="MomentumCandidate",
            behavior=self.behavior,
        )

    @property
    def absolute_mass(self):
        return numpy.sqrt(numpy.abs(self.mass2))


behavior.update(
    awkward._util.copy_behaviors(vector.LorentzVector, MomentumCandidate, behavior)
)
MomentumCandidateArray.ProjectionClass2D = vector.TwoVectorArray  # noqa: F821
MomentumCandidateArray.ProjectionClass3D = vector.ThreeVectorArray  # noqa: F821
MomentumCandidateArray.ProjectionClass4D = vector.LorentzVectorArray  # noqa: F821
MomentumCandidateArray.MomentumClass = MomentumCandidateArray  # noqa: F821


#########################################################################################
# Selected Components #
#########################################################################################
@awkward.mixin_class(behavior)
class TrackState(base.NanoCollection):
    """EDM4HEP Component: TrackState"""


_set_repr_name("TrackState")
TrackState.ProjectionClass2D = vector.TwoVectorArray  # noqa: F821
TrackState.ProjectionClass3D = vector.ThreeVectorArray  # noqa: F821
TrackState.ProjectionClass4D = TrackState  # noqa: F821
TrackState.MomentumClass = vector.LorentzVectorArray  # noqa: F821


@awkward.mixin_class(behavior)
class Quantity(base.NanoCollection):
    """EDM4HEP Component: Quantity"""


_set_repr_name("Quantity")


@awkward.mixin_class(behavior)
class covMatrix(base.NanoCollection):
    """EDM4HEP Component: covMatrix"""


_set_repr_name("covMatrix")


#########################################################################################
# Datatypes #
#########################################################################################
@awkward.mixin_class(behavior)
class EventHeader(edm4hep_nanocollection):
    """EDM4HEP Datatype: EventHeader"""


_set_repr_name("EventHeader")


@awkward.mixin_class(behavior)
class MCParticle(MomentumCandidate, edm4hep_nanocollection):
    """EDM4HEP Datatype: MCParticle"""


_set_repr_name("MCParticle")
behavior.update(awkward._util.copy_behaviors(MomentumCandidate, MCParticle, behavior))
MCParticleArray.ProjectionClass2D = vector.TwoVectorArray  # noqa: F821
MCParticleArray.ProjectionClass3D = vector.ThreeVectorArray  # noqa: F821
MCParticleArray.ProjectionClass4D = MCParticleArray  # noqa: F821
MCParticleArray.MomentumClass = vector.LorentzVectorArray  # noqa: F821


@awkward.mixin_class(behavior)
class SimTrackerHit(edm4hep_nanocollection):
    """EDM4HEP Datatype: SimTrackerHit"""


_set_repr_name("SimTrackerHit")


@awkward.mixin_class(behavior)
class CaloHitContribution(edm4hep_nanocollection):
    """EDM4HEP Datatype: CaloHitContribution"""


_set_repr_name("CaloHitContribution")


@awkward.mixin_class(behavior)
class SimCalorimeterHit(edm4hep_nanocollection):
    """EDM4HEP Datatype: SimCalorimeterHit"""


_set_repr_name("SimCalorimeterHit")


@awkward.mixin_class(behavior)
class RawCalorimeterHit(edm4hep_nanocollection):
    """EDM4HEP Datatype: RawCalorimeterHit"""


_set_repr_name("RawCalorimeterHit")


@awkward.mixin_class(behavior)
class CalorimeterHit(edm4hep_nanocollection):
    """EDM4HEP Datatype: CalorimeterHit"""


_set_repr_name("CalorimeterHit")


@awkward.mixin_class(behavior)
class ParticleID(edm4hep_nanocollection):
    """EDM4HEP Datatype: ParticleID"""


_set_repr_name("ParticleID")


@awkward.mixin_class(behavior)
class Cluster(edm4hep_nanocollection):
    """EDM4HEP Datatype: Cluster"""


_set_repr_name("Cluster")


@awkward.mixin_class(behavior)
class TrackerHit3D(edm4hep_nanocollection):
    """EDM4HEP Datatype: TrackerHit3D"""


_set_repr_name("TrackerHit3D")


@awkward.mixin_class(behavior)
class TrackerHitPlane(edm4hep_nanocollection):
    """EDM4HEP Datatype: TrackerHitPlane"""


_set_repr_name("TrackerHitPlane")


@awkward.mixin_class(behavior)
class RawTimeSeries(edm4hep_nanocollection):
    """EDM4HEP Datatype: RawTimeSeries"""


_set_repr_name("RawTimeSeries")


@awkward.mixin_class(behavior)
class Track(edm4hep_nanocollection):
    """EDM4HEP Datatype: Track"""


_set_repr_name("Track")


@awkward.mixin_class(behavior)
class Vertex(edm4hep_nanocollection):
    """EDM4HEP Datatype: Vertex"""


_set_repr_name("Vertex")


@awkward.mixin_class(behavior)
class ReconstructedParticle(MomentumCandidate, edm4hep_nanocollection):
    """EDM4HEP Datatype: Reconstructed particle"""


_set_repr_name("ReconstructedParticle")
behavior.update(
    awkward._util.copy_behaviors(MomentumCandidate, ReconstructedParticle, behavior)
)
ReconstructedParticleArray.ProjectionClass2D = vector.TwoVectorArray  # noqa: F821
ReconstructedParticleArray.ProjectionClass3D = vector.ThreeVectorArray  # noqa: F821
ReconstructedParticleArray.ProjectionClass4D = ReconstructedParticleArray  # noqa: F821
ReconstructedParticleArray.MomentumClass = vector.LorentzVectorArray  # noqa: F821


@awkward.mixin_class(behavior)
class TimeSeries(edm4hep_nanocollection):
    """EDM4HEP Datatype: TimeSeries"""


_set_repr_name("TimeSeries")


@awkward.mixin_class(behavior)
class RecDqdx(edm4hep_nanocollection):
    """EDM4HEP Datatype: RecDqdx"""


_set_repr_name("RecDqdx")


#########################################################################################
# Selected Links #
#########################################################################################
@awkward.mixin_class(behavior)
class RecoMCParticleLink(edm4hep_nanocollection):
    """EDM4HEP Link: MCRecoParticleLink"""


_set_repr_name("RecoMCParticleLink")
RecoMCParticleLinkArray.ProjectionClass2D = vector.TwoVectorArray  # noqa: F821
RecoMCParticleLinkArray.ProjectionClass3D = vector.ThreeVectorArray  # noqa: F821
RecoMCParticleLinkArray.ProjectionClass4D = RecoMCParticleLinkArray  # noqa: F821
RecoMCParticleLinkArray.MomentumClass = vector.LorentzVectorArray  # noqa: F821


#########################################################################################
# Extras #
#########################################################################################
@awkward.mixin_class(behavior)
class ObjectID(base.NanoCollection):
    """
    Generic Object ID storage, pointing to another collection.
    Usually have the <podio::ObjectID> type
    """


_set_repr_name("ObjectID")
>>>>>>> 46794a71 (EDM4HEPSchema and Newstyle FCCSchema)
