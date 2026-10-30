# Orai1–STIM1 CRAC Channel: Structural Modeling & Molecular Dynamics

Structural modeling and molecular dynamics (MD) simulation pipeline for the
**Orai1 hexameric channel bound to the STIM1 CRAC-activation domain (CAD)**,
the calcium-release-activated calcium (CRAC) channel complex. The pipeline
goes from sequence to a simulation-ready membrane system in three stages:
AI-based structure prediction (Boltz-2), and CHARMM-GUI/OpenMM molecular 
dynamics with downstream trajectory analysis.

![Boltz-2 model of the Orai1 hexamer bound to twelve STIM1 CAD chains, colored by per-residue pLDDT confidence; top view (left) and side view (right)](docs/figures/orai1_stim1_hexamer_cad_pLDDT.png)

*Boltz-2 prediction of the Orai1 hexamer (chains A–F) bound to twelve copies
of the STIM1 CRAC-activation domain (CAD, chains G–R), colored by
per-residue pLDDT confidence (orange = low, blue = high). Top view (left)
and side view (right). A vector version is available at
[`docs/figures/orai1_stim1_hexamer_cad_pLDDT.pdf`](docs/figures/orai1_stim1_hexamer_cad_pLDDT.pdf).*

## Repository layout

```
.
├── 01_boltz2_structure_prediction/   Stage 1 — Boltz-2 structure prediction
├── 02_molecular_dynamics/            Stage 2 — CHARMM-GUI system build, OpenMM MD, analysis
└── docs/figures/                     Figures for this README
```

## Pipeline overview

### Stage 1 — Boltz-2 structure prediction (`01_boltz2_structure_prediction/`)

1. **Single-chain model.** A single Orai1 subunit is predicted from sequence
   alone with [Boltz-2](https://github.com/jwohlwend/boltz)
   (`configs/orai1_singlechain.yaml` → `structures/orai1_singlechain_model.cif`).
2. **Truncated template.** The single-chain model is truncated (TM4
   extension removed, TM1 cytosolic segment removed, TM3–TM4 loop removed)
   to give a minimal, well-supported template
   (`structures/orai1_singlechain_template_truncated.cif`).
3. **Restrained hexamer + CAD complex.** The truncated template is used to
   guide a Boltz-2 prediction of the full complex: six copies of Orai1
   (chains A–F) and twelve copies of the STIM1 CRAC-activation domain (CAD,
   chains G–R, two CAD per Orai1 subunit), with pocket and pairwise-contact
   restraints encoding known Orai1–STIM1 interface residues (e.g. Orai1
   Tyr258–STIM1 His398)
   (`configs/boltz2.yaml` →
   `structures/boltz2_model_*.cif`).

### Stage 2 — Molecular dynamics (`03_molecular_dynamics/`)

The refined complex (and related structures — see below) is built into a
membrane system with [CHARMM-GUI](https://charmm-gui.org) (POPC bilayer,
CaCl₂-containing solvent, CHARMM36 force field) and simulated with OpenMM.

- `system/` — one subfolder per CHARMM-GUI-built system (`WT_boltz2`,
  `WT_refined_loop`, `boltz2.pentameric`), including the full CHARMM-GUI
  structure/topology files (`step5_input.psf/.pdb/.crd`).
- `restraints/` — per-condition restraint definitions (protein position,
  lipid position, dihedral) for different systems.
- `inputs/` — CHARMM-GUI OpenMM input decks for six equilibration stages
  (`step6.1`–`step6.6`) and production (`step7`).
- `scripts/` — the CHARMM-GUI-generated OpenMM driver (`openmm_run.py` and
  `omm_*.py` helper modules) plus post-processing and analysis code
  (trajectory alignment, RMSD, RMSF, inter-residue distances, PyEMMA
  featurization).
- `submission/` — job wrappers around the analysis scripts
  (`submit_1`…`submit_5`) and FoldX repair/mutation scans
  (`submit_6`, `submit_7`) for ΔΔG estimation.
- `analysis_notebooks/` — Jupyter notebooks for RMSD/RMSF structural
  analysis, ΔΔG analysis, representative-snapshot selection, and
  gate-residue distance tracking (e.g. Orai1 Y258 / STIM1 F394–H398).

## Software

- [Boltz-2](https://github.com/jwohlwend/boltz) — structure prediction
- [Biopython](https://biopython.org/), [PDBFixer](https://github.com/openmm/pdbfixer), [OpenMM](https://openmm.org/) — structure preparation, minimization, and MD
- [CHARMM-GUI](https://charmm-gui.org) — membrane system building (CHARMM36 force field)
- [MDAnalysis](https://www.mdanalysis.org/) — trajectory analysis (RMSD, RMSF, distances)
- [PyEMMA](http://emma-project.org/) — featurization
- [FoldX](https://foldxsuite.crg.eu/) — ΔΔG mutation scanning
- Python 3.10

## License

Code in this repository is released under the [MIT License](LICENSE). The
force field files, and MD production under `03_molecular_dynamics/scripts` are third-party
distributed by CHARMM-GUI/the MacKerell lab under their own academic-use terms and are not 
covered by this repository's license.

## Contact

Ella — honghanguyen1711@gmail.com
