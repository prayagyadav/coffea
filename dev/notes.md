# FCC Schema


## What does the FCC Events Spring 2021 have?
### Top Level
- "events" tree
- "metadata" tree
- "evt_metadata" tree
- "col_metadata" tree

### events tree
There are 3 types of branch names :
A] Generic names: Names with no symbols. Have 2 subgroups:
  a) Empty branches
    - Electron
    - AllMuon
    - Muon
    - Photon
  b) Non-Empty branches
    - EFlowNeutralHadron
    - Particle
    - ReconstructedParticles
    - EFlowPhoton
    - MCRecoAssociations
    - MissingET
    - ParticleIDs
    - Jet
    - EFlowTrack
    - EFlowTrack_1
B] Hash-Tagged: Contains two leaves- Index and Collection ID
  - Electron#0
  - AllMuon#0
  - EFlowNeutralHadron#0
  - EFlowNeutralHadron#1
  - EFlowNeutralHadron#2
  - Particle#0
  - Particle#1
  - Photon#0
  - ReconstructedParticles#0
  - ReconstructedParticles#1
  - ReconstructedParticles#2
  - ReconstructedParticles#3
  - ReconstructedParticles#4
  - ReconstructedParticles#5
  - EFlowPhoton#0
  - EFlowPhoton#1
  - EFlowPhoton#2
  - MCRecoAssociations#0
  - MCRecoAssociations#1
  - MissingET#0
  - MissingET#1
  - MissingET#2
  - MissingET#3
  - MissingET#4
  - MissingET#5
  - Jet#0
  - Jet#1
  - Jet#2
  - Jet#3
  - Jet#4
  - Jet#5
  - EFlowTrack#0
  - EFlowTrack#1
C] Trailing Underscore: Donno the purpose
 - EFlowNeutralHadron_0 (Empty)
 - EFlowNeutralHadron_1 (Empty)
 - EFlowNeutralHadron_2 (Empty)
 - EFlowPhoton_0 (Empty)
 - EFlowPhoton_1 (Empty)
 - EFlowPhoton_2 (Empty)
 - ParticleIDs_0 (Non-Empty)
 - EFlowTrack_0 (Empty)
 - EFlowTrack_1 (Has Non-Empty sub-branches)

There are three types of fields in branches:
A] Generic fields (Nesting level 0)
B] 3-vector fields
  a) position
    - position.x
    - position.y
    - position.z
  b) directionError
    - directionError.x
    - directionError.y
    - directionError.z
  c) vertex
    - vertex.x
    - vertex.y
    - vertex.z
  d) endpoint
    - endpoint.x
    - endpoint.y
    - endpoint.z
  e) referencePoint
    - referencePoint.x
    - referencePoint.y
    - referencePoint.z
C] 4-vector fields
  a) momentum
    - momentum.x
    - momentum.y
    - momentum.z
    - mass or energy
  b) momentumAtEndpoint
    - momentumAtEndpoint.x
    - momentumAtEndpoint.y
    - momentumAtEndpoint.z
    - mass or energy
D] Special Collections
4 different classes defined in methods define these Special Collections.



### Some Ideas

- zip all Hashed-Tagged(#[0-n]) into one objname.idx variable with components Index and CollectionIds and their subcomponents named [0-n]
