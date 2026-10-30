load boltz2-A.trunc.v2_model_0_plddt100.pdb, boltz

hide everything
show cartoon, boltz
bg_color white
set cartoon_transparency, 0

set_color af_very_high, [0.000, 0.325, 0.839]
set_color af_confident, [0.396, 0.796, 0.953]
set_color af_low,       [1.000, 0.859, 0.075]
set_color af_very_low,  [1.000, 0.490, 0.271]

color af_very_low,  boltz
color af_low,       boltz and not b < 50
color af_confident, boltz and not b < 70
color af_very_high, boltz and not b < 90

orient
