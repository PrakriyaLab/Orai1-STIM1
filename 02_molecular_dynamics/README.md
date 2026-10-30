# 02 — Molecular dynamics: system building, simulation, analysis

The minimized complex from 01 is embedded in a POPC bilayer with 
[CHARMM-GUI](https://charmm-gui.org) (CHARMM36 force field, CaCl₂-containing solvent), 
equilibrated and run in production with OpenMM, and analyzed for structural stability, 
binding interface distances, and mutation ΔΔG.

## Contents

```
system/            One folder per CHARMM-GUI-built system including the full CHARMM-GUI
                    structure/topology files (step5_input.psf/.pdb/.crd, ~200 MB each).
restraints/        Per-condition restraint definitions (dihe.txt, lipid_pos.txt,
                    prot_pos.txt) for 5 simulation conditions.
inputs/            CHARMM-GUI OpenMM input decks: step6.1-6.6 (equilibration), step7 (production).
scripts/           postprocessing_MD.py, _RMSD.py, _RMSF.py, _Distance.py/distance.py,
                    featurization.py (project analysis code).
submission/        Job wrappers: submit_1 (postprocessing) .. submit_5 (featurization),
                    submit_6/7 (FoldX repair + mutation scan, for DDG estimation).
analysis_notebooks/   DDG_analysis.ipynb, Structural_analysis.RMSF-RMSD.refined.ipynb,
                    Snapshots_selections.ipynb, Y258-F394-H398.ipynb.
```
