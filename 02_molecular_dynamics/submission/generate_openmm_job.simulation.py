#!/usr/bin/env python3
import os
import argparse

parser = argparse.ArgumentParser(description="Generate OpenMM run bash script with tmux or nohup support.")

parser.add_argument('--system', default='popc_0.1mCaCl2_seqfixed_180Apadding', help='System name (e.g. popc_0.1mCaCl2_seqfixed_180Apadding)')
parser.add_argument('--replica', type=int, default=0, help='Replica index (e.g. 0)')
parser.add_argument('--traj', type=int, required=True, help='Trajectory index (e.g. 3 for TRAJ003)')
parser.add_argument('--platform', default='CUDA', choices=['CUDA', 'OpenCL', 'CPU'], help='OpenMM compute platform')
parser.add_argument('--input', default='inputs/step7_production.inp', help='Path to input .inp file')
parser.add_argument('--toppar', default='toppar.str', help='Path to toppar.str')
parser.add_argument('--output_dir', default='.', help='Directory to write the bash script')
parser.add_argument('--delay_hours', type=float, default=0.0, help='Delay time before starting job (in hours)')

args = parser.parse_args()
cwd = os.getcwd()
base_dir = os.path.abspath(os.path.join(cwd, '..'))

# Derived variables
traj_str = f"TRAJ{args.traj:03d}"
base_sim_path = f"simulations/{args.system}/Rep-{args.replica}"

if args.traj > 0:
    traj_prev = f"TRAJ{args.traj - 1:03d}"
    chkfile = f"{base_sim_path}/{traj_prev}/sim.chk"
    dcdfile_prev = f"{base_sim_path}/{traj_prev}/sim.dcd"
else:
    chkfile = f"minimization/{args.system}/Rep-{args.replica}/minimization005/equilibration.chk"
    dcdfile_prev = f"minimization/{args.system}/Rep-{args.replica}/minimization005/equilibration.dcd"

if not os.path.isfile(os.path.join(base_dir, chkfile)) and not os.path.isfile(os.path.join(base_dir, dcdfile_prev)):
    raise ValueError('Checkpoint file is not found or previous TRAJ not being written!')

os.makedirs(os.path.join(base_dir, base_sim_path, traj_str), exist_ok=True)


outpdb = f"{base_sim_path}/{traj_str}/sim.pdb"
outchk = f"{base_sim_path}/{traj_str}/sim.chk"
outdcd = f"{base_sim_path}/{traj_str}/sim.dcd"

top = f"system/{args.system}/step5_input.psf"

chk_full = os.path.join(base_dir, chkfile)

if os.path.isfile(chk_full):
    CHKFILE = f"CHKFILE={chkfile}"
else:
    CHKFILE = ""
    
crd = f"system/{args.system}/step5_input.crd"
sysinfo = f"system/{args.system}/sysinfo.dat"

logfile = f"jobs/{args.system}_rep{args.replica}_traj{args.traj:03d}.log"
timefile = f"{base_sim_path}/{traj_str}/timing.txt"
session_name = f"rep{args.replica}_sim{args.traj:03d}"

script_name = f"{args.system}_rep{args.replica}_traj{args.traj:03d}.sh"
script_path = os.path.join(args.output_dir, script_name)

# Compute delay in seconds
delay_seconds = int(args.delay_hours * 3600)

with open(script_path, 'w') as f1:
    bash = f"""#!/bin/bash

cd {base_dir}
# === Conda and environment setup ===
source ~/miniconda3/etc/profile.d/conda.sh
conda activate openff

# === Configuration ===
INPUT="{args.input}"
TOP="{top}"
CRD="{crd}"
TOPPAR="{args.toppar}"
SYSINFO="{sysinfo}"
PLATFORM="{args.platform}"
"""
    if CHKFILE != '':
        bash += f"""
{CHKFILE}
"""
    bash += f"""
OUTPDB="{outpdb}"
OUTCHK="{outchk}"
OUTDCD="{outdcd}"

LOGFILE="{logfile}"
TIMEFILE="{timefile}"
SESSION_NAME="{session_name}"

echo "=== Job Script Started at $(date) ===" | tee -a "${{LOGFILE}}"

# === Check for tmux ===
if command -v tmux >/dev/null 2>&1; then
    echo "[info] tmux found, running job in session '${{SESSION_NAME}}'"
    tmux new-session -d -s "${{SESSION_NAME}}" \\
    "echo '[info] Job scheduled with delay of {delay_seconds} seconds'; \\
    echo 'Sleep start: $(date)'; \\
    sleep {delay_seconds}; \\
    echo 'Sleep end: $(date)'; \\
    echo 'Running OpenMM in tmux session ${{SESSION_NAME}}...'; \\
    /usr/bin/time -v python scripts/openmm_run.py \\
        --platform ${{PLATFORM}} \\
        -i ${{INPUT}} \\
        -p ${{TOP}} \\
        -c ${{CRD}} \\
        -t ${{TOPPAR}} \\
        -b ${{SYSINFO}} \\
"""
    if CHKFILE != '':
        bash += f"""        -ichk ${{CHKFILE}} \\
"""
    bash += f"""        -opdb ${{OUTPDB}} \\
        -ochk ${{OUTCHK}} \\
        -odcd ${{OUTDCD}} \\
        -rewrap \\
        2>&1 | tee -a ${{LOGFILE}} | tee ${{TIMEFILE}}; \\
    if [ \\$? -eq 0 ]; then \\
        echo 'OpenMM run completed successfully at $(date)' | tee -a ${{LOGFILE}}; \\
    else \\
        echo 'OpenMM run FAILED at $(date)' | tee -a ${{LOGFILE}}; \\
    fi"
    echo "[info] Attach to session with: tmux attach -t ${{SESSION_NAME}}"
else
    echo "[warn] tmux not found, using nohup..."
    echo "[info] Job scheduled with delay of {delay_seconds} seconds"
    echo "Sleep start: $(date)"
    sleep {delay_seconds}
    echo "Sleep end: $(date)"
    echo "Running OpenMM with nohup..."
    nohup /usr/bin/time -v python scripts/openmm_run.py \\
        --platform ${{PLATFORM}} \\
        -i ${{INPUT}} \\
        -p ${{TOP}} \\
        -c ${{CRD}} \\
        -t ${{TOPPAR}} \\
        -b ${{SYSINFO}} \\
"""
    if CHKFILE != '':
        bash += f"""        -ichk ${{CHKFILE}} \\
"""
    bash += f"""        -opdb ${{OUTPDB}} \\
        -ochk ${{OUTCHK}} \\
        -odcd ${{OUTDCD}} \\
        -rewrap \\
        > "${{LOGFILE}}" 2>&1 &
    
    NOHUP_PID=$!
    echo "[info] Job launched with PID ${{NOHUP_PID}}"
    echo "[info] Monitor progress with: tail -f ${{LOGFILE}}"
    
    # Wait for the background job and check exit status
    wait ${{NOHUP_PID}}
    if [ $? -eq 0 ]; then
        echo "OpenMM run completed successfully at $(date)" | tee -a "${{LOGFILE}}"
    else
        echo "OpenMM run FAILED at $(date)" | tee -a "${{LOGFILE}}"
    fi
fi

echo "=== Job Script Finished at $(date) ===" | tee -a "${{LOGFILE}}"
"""
    f1.write(bash)

os.chmod(script_path, 0o755)
print(f"Wrote job script to: {script_path}")

# Execute the script after writing
print(f"Launching job script: {script_path}")
import subprocess
try:
    subprocess.run(["bash", script_path], check=True)
    print("Job script launched successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error occurred while launching the job script: {e}")
