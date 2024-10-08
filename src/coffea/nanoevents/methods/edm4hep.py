import awkward
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
