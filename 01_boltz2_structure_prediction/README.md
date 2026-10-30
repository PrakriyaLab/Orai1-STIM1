# 01 — Boltz-2 structure prediction

Predicts the Orai1 hexamer bound to the STIM1 CRAC-activation domain (CAD)
in two passes with [LMI4Boltz](https://github.com/tlitfin/lmi4boltz).

## Contents

```
configs/
  orai1_singlechain.yaml                         Boltz-2 input: single Orai1 chain, sequence only
  boltz2.yaml      Boltz-2 input: 6x Orai1 + 12x CAD, template + pocket restraints
structures/
  orai1_singlechain_model.cif                    Output of the single-chain run
  orai1_singlechain_confidence.json
  orai1_singlechain_template_truncated.cif       Single-chain model, truncated (TM4 extension /
                                                 TM1 cytosolic segment / TM3-TM4 loop removed),
                                                 used as the structural template for the complex run
  boltz2_model_0.cif            Output of the restrained complex run
  boltz2_model_1.cif
  boltz2_model_2.cif
  confidence_boltz2_model_0.json
  confidence_boltz2_model_1.json
  confidence_boltz2_model_2.json
raw_boltz2_run_output/    (present locally, not tracked in git — see repo-root README)
  orai1.singlechain/
  boltz2/
```

## Method

Exact CLI flags depend on the installed [LMI4Boltz](https://github.com/tlitfin/lmi4boltz) — see its own documentation.
