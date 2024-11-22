import awkward
import numpy
from dask_awkward.lib.core import dask_method, dask_property

from coffea.nanoevents.methods import base, vector

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
        idx_field_name = generic_name + "_idx_" + target_name
        if idx_field_name not in self.fields:
            raise FileNotFoundError(
                f"{idx_field_name} not found in the current collection"
            )
        return self._events()[target_name]._apply_global_index(
            self[idx_field_name]["index_Global"]
        )

    @Map_Relation.dask
    def Map_Relation(self, dask_array, generic_name, target_name):
        idx_field_name = generic_name + "_idx_" + target_name
        if idx_field_name not in dask_array.fields:
            raise FileNotFoundError(
                f"{idx_field_name} not found in the current collection"
            )
        return dask_array._events()[target_name]._apply_global_index(
            dask_array[idx_field_name]["index_Global"]
        )

    @dask_property
    def List_Links(self):
        """List all the branches that are Links"""
        idxs = {name for name in self.fields if (("Link_from" in name) or ("Link_to" in name))}
        return idxs

    @List_Links.dask
    def List_Links(self, dask_array):
        """List all the branches that are Links"""
        idxs = {name for name in dask_array.fields if (("Link_from" in name) or ("Link_to" in name))}
        return idxs

    @dask_method
    def Map_Link(self, generic_name, target_name):
        # idx_field_name = generic_name + "_idx_" + target_name
        idx_field_name = 'Link_'+generic_name+'_'+target_name
        if idx_field_name not in self.fields:
            raise FileNotFoundError(
                f"{idx_field_name} not found in the current collection"
            )
        return self._events()[target_name]._apply_global_index(
            self[idx_field_name]["index_Global"]
        )

    @Map_Link.dask
    def Map_Link(self, dask_array, generic_name, target_name):
        # idx_field_name = generic_name + "_idx_" + target_name
        idx_field_name = 'Link_'+generic_name+'_'+target_name
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

    # Daughters
    @dask_property
    def get_daughters_index(self):
        """
        Obtain the global indices of the daughters of each and every MCParticle
        - The output is a doubly nested awkward array
        - Needs the presence of Particleidx1 collection
        - The Particleidx1.index contains info about the daughters
        """
        return self.daughters.Particleidx1_rangesG

    @get_daughters_index.dask
    def get_daughters_index(self, dask_array):
        """
        Obtain the global indices of the daughters of each and every MCParticle
        - The output is a doubly nested awkward array
        - Needs the presence of Particleidx1 collection
        - The Particleidx1.index contains info about the daughters
        """
        return dask_array.daughters.Particleidx1_rangesG

    @dask_property
    def get_daughters(self):
        """
        Obtain the actual MCParticle daughters to each and every MCParticle
        - The output is a doubly nested awkward array
        - Needs the presence of Particleidx1 collection
        - The Particleidx1.index contains info about the daughters
        """
        return self._events().Particle._apply_global_index(self.get_daughters_index)

    @get_daughters.dask
    def get_daughters(self, dask_array):
        """
        Obtain the actual MCParticle daughters to each and every MCParticle
        - The output is a doubly nested awkward array
        - Needs the presence of Particleidx1 collection
        - The Particleidx1.index contains info about the daughters
        """
        return dask_array._events().Particle._apply_global_index(
            dask_array.get_daughters_index
        )

    # Parents
    @dask_property
    def get_parents_index(self):
        """
        Obtain the global indices of the parents of each and every MCParticle
        - The output is a doubly nested awkward array
        - Needs the presence of Particleidx0 collection
        - The Particleidx0.index contains info about the parents
        """
        return self.parents.Particleidx0_rangesG

    @get_parents_index.dask
    def get_parents_index(self, dask_array):
        """
        Obtain the indices of the parents of each and every MCParticle
        - The output is a doubly nested awkward array
        - Needs the presence of Particleidx0 collection
        - The Particleidx0.index contains info about the parents
        """
        return dask_array.parents.Particleidx0_rangesG

    @dask_property
    def get_parents(self):
        """
        Obtain the actual MCParticle parents to each and every MCParticle
        - The output is a doubly nested awkward array
        - Needs the presence of Particleidx0 collection
        - The Particleidx0.index contains info about the parents
        """
        return self._events().Particle._apply_global_index(self.get_parents_index)

    @get_parents.dask
    def get_parents(self, dask_array):
        """
        Obtain the actual MCParticle parents to each and every MCParticle
        - The output is a doubly nested awkward array
        - Needs the presence of Particleidx0 collection
        - The Particleidx0.index contains info about the parents
        """
        return dask_array._events().Particle._apply_global_index(
            dask_array.get_parents_index
        )


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
    """EDM4HEP Datatype: ParticleID"""


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

    def match_collection(self, idx):
        """Returns matched particles; pass on an ObjectID array."""
        return self[idx.index]

    @dask_property
    def match_muons(self):
        """Returns matched muons; drops none values"""
        m = self._events().ReconstructedParticles._apply_global_index(
            self.Muonidx0_indexGlobal
        )
        return awkward.drop_none(m, behavior=self.behavior)

    @match_muons.dask
    def match_muons(self, dask_array):
        """Returns matched muons; drops none values"""
        m = dask_array._events().ReconstructedParticles._apply_global_index(
            dask_array.Muonidx0_indexGlobal
        )
        return awkward.drop_none(m, behavior=self.behavior)

    @dask_property
    def match_electrons(self):
        """Returns matched electrons; drops none values"""
        e = self._events().ReconstructedParticles._apply_global_index(
            self.Electronidx0_indexGlobal
        )
        return awkward.drop_none(e, behavior=self.behavior)

    @match_electrons.dask
    def match_electrons(self, dask_array):
        """Returns matched electrons; drops none values"""
        e = dask_array._events().ReconstructedParticles._apply_global_index(
            dask_array.Electronidx0_indexGlobal
        )
        return awkward.drop_none(e, behavior=self.behavior)

    @dask_property
    def match_gen(self):
        """Returns the Gen level (MC) particle corresponding to the ReconstructedParticle"""
        prepared = self._events().Particle[self._events().MCRecoAssociations.mc.index]
        return prepared._apply_global_index(self.MCRecoAssociationsidx0_indexGlobal)

    @match_gen.dask
    def match_gen(self, dask_array):
        """Returns the Gen level (MC) particle corresponding to the ReconstructedParticle"""
        prepared = dask_array._events().Particle[
            dask_array._events().MCRecoAssociations.mc.index
        ]
        return prepared._apply_global_index(
            dask_array.MCRecoAssociationsidx0_indexGlobal
        )


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

    @property
    def reco_mc_index(self):
        """
        Returns an array of indices mapping to generator particles for each reconstructed particle
        """
        arr_reco = self.reco.index[:, :, numpy.newaxis]
        arr_mc = self.mc.index[:, :, numpy.newaxis]

        joined_indices = awkward.concatenate((arr_reco, arr_mc), axis=2)

        return joined_indices

    @dask_property
    def reco_mc(self):
        """
        Returns an array of records mapping to generator particle record for each reconstructed particle record
        - Needs 'ReconstructedParticles' and 'Particle' collections
        """
        reco_index = self.reco.index
        mc_index = self.mc.index
        r = self._events().ReconstructedParticles[reco_index][:, :, numpy.newaxis]
        m = self._events().Particle[mc_index][:, :, numpy.newaxis]

        return awkward.concatenate((r, m), axis=2)

    @reco_mc.dask
    def reco_mc(self, dask_array):
        """
        Returns an array of records mapping to generator particle record for each reconstructed particle record
        - Needs 'ReconstructedParticles' and 'Particle' collections
        """
        reco_index = dask_array.reco.index
        mc_index = dask_array.mc.index
        r = dask_array._events().ReconstructedParticles[reco_index][:, :, numpy.newaxis]
        m = dask_array._events().Particle[mc_index][:, :, numpy.newaxis]

        return awkward.concatenate((r, m), axis=2)


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
