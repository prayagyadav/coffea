import awkward
import dask_awkward
from dask_awkward.lib.core import dask_property, dask_method
import numba
import numpy

from coffea.nanoevents.methods import base, vector

behavior = {}
behavior.update(base.behavior)

class _FCCEvents(behavior["NanoEvents"]):
    def __repr__(self):
        # return f"<event {getattr(self,'run','??')}:\
        #         {getattr(self,'luminosityBlock','??')}:\
        #         {getattr(self,'event','??')}>"
        return "FCC Events"


behavior["NanoEvents"] = _FCCEvents


def _set_repr_name(classname):
    def namefcn(self):
        return classname

    behavior[classname].__repr__ = namefcn


def map_index_to_array(array, index, axis=1):
    '''
    DESCRIPTION: Creates a slice of input array according to the input index.
    INPUTS: array (Singly nested)
            index (Singly or Doubly nested)
            axis (By default 1, use axis = 2 if index is doubly nested )
    EXAMPLE:
            a = awkward.Array([
                [44,33,23,22],
                [932,24,456,78],
                [22,345,78,90,98,24]
            ])

            a_index = awkward.Array([
                [0,1,2],
                [0,1],
                []
            ])

            a2_index = awkward.Array([
                [[0],[0,1],[2]],
                [[0,1]],
                []
            ])
            >> map_index_to_array(a, a_index)
                [[44, 33, 23],
                 [932, 24],
                 []]
                ---------------------
                type: 3 * var * int64
            >> map_index_to_array(a, a2_index, axis=2)
                [[[44], [44, 33], [23]],
                 [[932, 24]],
                 []]
                ---------------------------
                type: 3 * var * var * int64

    '''
    if axis==1:
        return array[index]
    elif axis==2:
        axis2_counts_array = awkward.num(index, axis=axis)
        flat_axis2_counts_array = awkward.flatten(axis2_counts_array, axis=1)
        flat_index = awkward.flatten(index, axis=axis)
        trimmed_flat_array = array[flat_index]
        trimmed_array = awkward.unflatten(trimmed_flat_array, flat_axis2_counts_array, axis=1)
        return trimmed_array
    else:
        raise AttributeError('Only axis = 1 or axis = 2 supported at the moment.')

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
        """Sum an array of vectors elementwise using `x`, `y`, `z`, `t`, and `charge` components"""
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


@awkward.mixin_class(behavior)
class MCTruthParticle(MomentumCandidate, base.NanoCollection):
    """Generated Monte Carlo particles."""


    @numba.njit
    def index_range_numba_wrap(self, begin_end, builder):
        for ev in begin_end:
            builder.begin_list()
            for j in ev:
                builder.begin_list()
                for k in range(j[0],j[1]):
                    builder.integer(k)
                builder.end_list()
            builder.end_list()
        return builder

    def index_range(self, begin, end):
        begin_end = awkward.concatenate((begin[:,:,numpy.newaxis],end[:,:,numpy.newaxis]),axis=2)
        if awkward.backend(begin) == "typetracer" or awkward.backend(end) == "typetracer":
            # here we fake the output of numba wrapper function since
            # operating on length-zero data returns the wrong layout!
            awkward.typetracer.length_zero_if_typetracer(begin_end) # force touching of the necessary data
            return awkward.Array(awkward.Array([]).layout.to_typetracer(forget_length=True))
        return self.index_range_numba_wrap(begin_end, awkward.ArrayBuilder()).snapshot()

    #Daughters
    @dask_property
    def get_daughters_index(self):
        ranges = self.index_range(self.daughters.begin, self.daughters.end)
        return awkward.values_astype(map_index_to_array(self._events().Particleidx1.index, ranges, axis=2), "int64")

    @get_daughters_index.dask
    def get_daughters_index(self, dask_array):
        ranges = dask_awkward.map_partitions(self.index_range, dask_array.daughters.begin, dask_array.daughters.end)
        return awkward.values_astype(map_index_to_array(dask_array._events().Particleidx1.index, ranges, axis=2), "int64")

    @dask_property
    def get_daughters(self):
        return map_index_to_array(self, self.get_daughters_index, axis=2)

    @get_daughters.dask
    def get_daughters(self, dask_array):
        return map_index_to_array(dask_array, dask_array.get_daughters_index, axis=2)

    #Parents
    @dask_property
    def get_parents_index(self):
        ranges = self.index_range(self.parents.begin, self.parents.end)
        return awkward.values_astype(map_index_to_array(self._events().Particleidx0.index, ranges, axis=2), "int64")

    @get_parents_index.dask
    def get_parents_index(self, dask_array):
        ranges = dask_awkward.map_partitions(self.index_range, dask_array.parents.begin, dask_array.parents.end)
        return awkward.values_astype(map_index_to_array(dask_array._events().Particleidx0.index, ranges, axis=2), "int64")

    @dask_property
    def get_parents(self):
        return map_index_to_array(self, self.get_parents_index, axis=2)

    @get_parents.dask
    def get_parents(self, dask_array):
        return map_index_to_array(dask_array, dask_array.get_parents_index, axis=2)

    # @property
    # def matched_pfos(self, _dask_array_=None):
    #     """Returns an array of matched reconstructed particle objects for each generator particle."""
    #     if _dask_array_ is not None:
    #         collection_name = self.layout.purelist_parameter("collection_name")
    #         original_from = self.behavior["__original_array__"]()[collection_name]
    #         original = self.behavior["__original_array__"]().PandoraPFOs
    #         return original._apply_global_mapping(
    #             _dask_array_,
    #             original_from,
    #             self.behavior["__original_array__"]().RecoMCTruthLink.Gmc_index,
    #             self.behavior["__original_array__"]().RecoMCTruthLink.Greco_index,
    #             _dask_array_=original,
    #         )
    #     raise RuntimeError("Not reachable in dask mode!")

    # @property
    # def matched_clusters(self, _dask_array_=None):
    #     """Returns an array of matched cluster particle objects for each generator particle."""
    #     if _dask_array_ is not None:
    #         collection_name = self.layout.purelist_parameter("collection_name")
    #         original_from = self.behavior["__original_array__"]()[collection_name]
    #         original = self.behavior["__original_array__"]().PandoraClusters
    #         return original._apply_global_mapping(
    #             _dask_array_,
    #             original_from,
    #             self.behavior["__original_array__"]().ClusterMCTruthLink.Gmc_index,
    #             self.behavior["__original_array__"]().ClusterMCTruthLink.Gcluster_index,
    #             _dask_array_=original,
    #         )
    #     raise RuntimeError("Not reachable in dask mode!")

    # @property
    # def matched_trks(self, _dask_array_=None):
    #     """Returns an array of matched cluster particle objects for each generator particle."""
    #     if _dask_array_ is not None:
    #         collection_name = self.layout.purelist_parameter("collection_name")
    #         original_from = self.behavior["__original_array__"]()[collection_name]
    #         original = self.behavior["__original_array__"]().MarlinTrkTracks
    #         return original._apply_global_mapping(
    #             _dask_array_,
    #             original_from,
    #             self.behavior[
    #                 "__original_array__"
    #             ]().MarlinTrkTracksMCTruthLink.Gmc_index,
    #             self.behavior[
    #                 "__original_array__"
    #             ]().MarlinTrkTracksMCTruthLink.Gtrk_index,
    #             _dask_array_=original,
    #         )
    #     raise RuntimeError("Not reachable in dask mode!")

    # def _apply_nested_global_index(self, index, nested_counts, _dask_array_=None):
    #     """As _apply_global_index but expects one additional layer of nesting to get specified."""
    #     if isinstance(index, int):
    #         out = self._content()[index]
    #         return awkward.Record(out, behavior=self.behavior)

    #     def flat_take(layout):
    #         idx = awkward.Array(layout)
    #         return self._content()[idx.mask[idx >= 0]]

    #     def descend(layout, depth, **kwargs):
    #         if layout.purelist_depth == 1:
    #             return flat_take(layout)

    #     (index_out,) = awkward.broadcast_arrays(
    #         index._meta if isinstance(index, dask_awkward.Array) else index
    #     )
    #     nested_counts_out = (
    #         nested_counts._meta
    #         if isinstance(nested_counts, dask_awkward.Array)
    #         else nested_counts
    #     )
    #     index_out = awkward.unflatten(
    #         index_out, awkward.flatten(nested_counts_out), axis=-1
    #     )
    #     layout_out = awkward.transform(descend, index_out.layout, highlevel=False)
    #     out = awkward.Array(layout_out, behavior=self.behavior)

    #     if isinstance(index, dask_awkward.Array):
    #         return _dask_array_.map_partitions(
    #             base._ClassMethodFn("_apply_nested_global_index"),
    #             index,
    #             nested_counts,
    #             label="_apply_nested_global_index",
    #             meta=out,
    #         )
    #     return out

    # @property
    # def parents(self, _dask_array_=None):
    #     if _dask_array_ is not None:
    #         collection_name = self.layout.purelist_parameter("collection_name")
    #         original = self.behavior["__original_array__"]()[collection_name]
    #         return original._apply_nested_global_index(
    #             self.behavior["__original_array__"]().GMCParticlesSkimmedParentsIndex,
    #             original.parents_counts,
    #             _dask_array_=original,
    #         )
    #     raise RuntimeError("Not reachable in dask mode!")

    # @property
    # def children(self, _dask_array_=None):
    #     if _dask_array_ is not None:
    #         collection_name = self.layout.purelist_parameter("collection_name")
    #         original = self.behavior["__original_array__"]()[collection_name]
    #         return original._apply_nested_global_index(
    #             self.behavior["__original_array__"]().GMCParticlesSkimmedParentsIndex,
    #             original.children_counts,
    #             _dask_array_=original,
    #         )
    #     raise RuntimeError("Not reachable in dask mode!")


_set_repr_name("MCTruthParticle")
behavior.update(
    awkward._util.copy_behaviors(MomentumCandidate, MCTruthParticle, behavior)
)

MCTruthParticleArray.ProjectionClass2D = vector.TwoVectorArray  # noqa: F821
MCTruthParticleArray.ProjectionClass3D = vector.ThreeVectorArray  # noqa: F821
MCTruthParticleArray.ProjectionClass4D = MCTruthParticleArray  # noqa: F821
MCTruthParticleArray.MomentumClass = vector.LorentzVectorArray  # noqa: F821


@awkward.mixin_class(behavior)
class RecoParticle(MomentumCandidate, base.NanoCollection):
    """Reconstructed particles"""

    def match_collection(self, idx):
        """Returns matched particles"""
        return self[idx.index]

    @dask_property
    def matched_gen(self):
        sel = awkward.broadcast_arrays(True, self)[0]
        index = self._events().MCRecoAssociations.reco_mc_index[:,:,1]
        return self._events().Particle[index[sel]]


    @matched_gen.dask
    def matched_gen(self, dask_array):
        sel = awkward.broadcast_arrays(True, dask_array)[0]
        index = dask_array._events().MCRecoAssociations.reco_mc_index[:,:,1]
        return dask_array._events().Particle[index[sel]]

_set_repr_name("RecoParticle")
behavior.update(awkward._util.copy_behaviors(MomentumCandidate, RecoParticle, behavior))

RecoParticleArray.ProjectionClass2D = vector.TwoVectorArray  # noqa: F821
RecoParticleArray.ProjectionClass3D = vector.ThreeVectorArray  # noqa: F821
RecoParticleArray.ProjectionClass4D = RecoParticleArray  # noqa: F821
RecoParticleArray.MomentumClass = vector.LorentzVectorArray  # noqa: F821


# @awkward.mixin_class(behavior)
# class Cluster(vector.PtThetaPhiELorentzVector, base.NanoCollection):
#     """Clusters."""

#     @property
#     def matched_gen(self, _dask_array_=None):
#         """Returns an array of matched generator particle objects for each cluster."""
#         if _dask_array_ is not None:
#             collection_name = self.layout.purelist_parameter("collection_name")
#             original_from = self.behavior["__original_array__"]()[collection_name]
#             original = self.behavior["__original_array__"]().MCParticlesSkimmed
#             return original._apply_global_mapping(
#                 _dask_array_,
#                 original_from,
#                 self.behavior["__original_array__"]().ClusterMCTruthLink.Gcluster_index,
#                 self.behavior["__original_array__"]().ClusterMCTruthLink.Gmc_index,
#                 _dask_array_=original,
#             )
#         raise RuntimeError("Not reachable in dask mode!")


# @awkward.mixin_class(behavior)
# class Track(vector.LorentzVector, base.NanoEvents, base.NanoCollection):
#     """Tracks."""

#     @property
#     def matched_gen(self, _dask_array_=None):
#         """Returns an array of matched generator particle objects for each track."""
#         if _dask_array_ is not None:
#             collection_name = self.layout.purelist_parameter("collection_name")
#             original_from = self.behavior["__original_array__"]()[collection_name]
#             original = self.behavior["__original_array__"]().MCParticlesSkimmed
#             return original._apply_global_mapping(
#                 _dask_array_,
#                 original_from,
#                 self.behavior[
#                     "__original_array__"
#                 ]().MarlinTrkTracksMCTruthLink.Gtrk_index,
#                 self.behavior[
#                     "__original_array__"
#                 ]().MarlinTrkTracksMCTruthLink.Gmc_index,
#                 _dask_array_=original,
#             )
#         raise RuntimeError("Not reachable in dask mode!")

#     @property
#     def pt(self):
#         r"""transverse momentum
#         mag :: magnetic field strength in T

#         source: https://github.com/PandoraPFA/MarlinPandora/blob/master/src/TrackCreator.cc#LL521
#         """
#         metadata = self.behavior["__original_array__"]().get_metadata()

#         if metadata is None or "b_field" not in metadata.keys():
#             print(
#                 "Track momentum requires value of magnetic field. \n"
#                 "Please have 'metadata' argument in from_root function have"
#                 "key 'b_field' with the value of magnetic field."
#             )
#             raise ValueError(
#                 "Track momentum requires value of magnetic field. \n"
#                 "Please have 'metadata' argument in from_root function have"
#                 "key 'b_field' with the value of magnetic field."
#             )
#         else:
#             b_field = metadata["b_field"]
#             return b_field * 2.99792e-4 / numpy.abs(self["omega"])

#     @property
#     def phi(self):
#         r"""phi of momentum"""
#         return self["phi"]

#     @property
#     def x(self):
#         r"""x momentum"""
#         return numpy.cos(self["phi"]) * self.pt

#     @property
#     def y(self):
#         r"""y momentum"""
#         return numpy.sin(self["phi"]) * self.pt

#     @property
#     def z(self):
#         r"""z momentum"""
#         return self["tanLambda"] * self.pt

#     @property
#     def mass(self):
#         r"""mass of the track - assumed to be the mass of a pion
#         source: https://github.com/iLCSoft/MarlinTrk/blob/c53d868979ef6db26077746ce264633819ffcf4f/src/MarlinAidaTTTrack.cc#LL54C3-L58C3
#         """
#         return PION_MASS * awkward.ones_like(self["omega"])


@awkward.mixin_class(behavior)
class ParticleLink(base.NanoCollection):
    """MCRecoParticleAssociation objects."""

    @property
    def reco_mc_index(self):
        """
        Returns an array of indices mapping to generator particles for each reconstructed particle
        """
        arr_reco = self.reco.index[:,:,numpy.newaxis]
        arr_mc = self.mc.index[:,:,numpy.newaxis]

        joined_indices = awkward.concatenate((arr_reco,arr_mc), axis=2)

        return joined_indices

    @dask_property
    def reco_mc(self):
        """
        Returns an array of Records mapping to generator particle record for each reconstructed particle record
        """
        reco_index = self.reco.index
        mc_index = self.mc.index
        r = self._events().ReconstructedParticles[reco_index][:,:,numpy.newaxis]
        m = self._events().Particle[mc_index][:,:,numpy.newaxis]

        return awkward.concatenate((r,m), axis=2)

    @reco_mc.dask
    def reco_mc(self, dask_array):
        """
        Returns an array of Records mapping to generator particle record for each reconstructed particle record
        """
        reco_index = dask_array.reco.index
        mc_index = dask_array.mc.index
        r = dask_array._events().ReconstructedParticles[reco_index][:,:,numpy.newaxis]
        m = dask_array._events().Particle[mc_index][:,:,numpy.newaxis]

        return awkward.concatenate((r,m), axis=2)
