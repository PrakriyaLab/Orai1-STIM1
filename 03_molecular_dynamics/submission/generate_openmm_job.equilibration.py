import argparse
import subprocess
import stat
from pathlib import Path
from datetime import datetime


def build_step_block(args, traj, base_dir, sim_rel_path, logfile):
    """Return the bash block for a single equilibration step."""
    traj_str  = f"minimization{traj:03d}"
    traj_prev = f"minimization{traj - 1:03d}"

    chk_rel_path  = sim_rel_path / traj_prev / "equilibration.chk"
    prev_pdb_path = base_dir / sim_rel_path / traj_prev / "equilibration.pdb"

    input_chk_cmd = f"-ichk {chk_rel_path}" if traj > 0 else ""

    out_pdb  = sim_rel_path / traj_str / "equilibration.pdb"
    out_chk  = sim_rel_path / traj_str / "equilibration.chk"
    out_dcd  = sim_rel_path / traj_str / "equilibration.dcd"
    timefile = sim_rel_path / traj_str / "timing.txt"

    inp_file = f"inputs/step6.{traj + 1}_equilibration.inp"

    py_cmd = (
        f"/usr/bin/time -v python scripts/openmm_run.py "
        f"--platform {args.platform} "
        f"-i {inp_file} "
        f"-p system/{args.system}/step5_input.psf "
        f"-c system/{args.system}/step5_input.crd "
        f"-t {args.toppar} "
        f"-b system/{args.system}/sysinfo.dat "
        f"{input_chk_cmd} "
        f"-opdb {out_pdb} -ochk {out_chk} -odcd {out_dcd} "
        f"-rewrap"
    )

    # Guard: previous step must have written its .pdb (written once, at completion)
    pdb_guard = ""
    if traj > 0:
        pdb_guard = f"""
# --- completion guard: previous step must have finished (equilibration.pdb must exist) ---
if [ ! -f "{prev_pdb_path}" ]; then
    echo "[ERROR] step6.{traj} did not complete — missing {prev_pdb_path}" | tee -a "$LOG"
    echo "[ERROR] Aborting before starting step6.{traj + 1}." | tee -a "$LOG"
    exit 1
fi"""

    block = f"""
# ============================================================
# Step step6.{traj + 1}  (traj index {traj})
# ============================================================
{pdb_guard}
echo "--- Starting step6.{traj + 1}: $(date) ---" | tee -a "$LOG"
mkdir -p "{base_dir / sim_rel_path / traj_str}"
taskset -c 0-15 {py_cmd} 2>&1 | tee -a "$LOG" | tee "{base_dir / timefile}"
STEP_RC=${{PIPESTATUS[0]}}
if [ $STEP_RC -ne 0 ]; then
    echo "[ERROR] step6.{traj + 1} failed (exit $STEP_RC) — aborting pipeline." | tee -a "$LOG"
    exit $STEP_RC
fi
# Verify this step also wrote its .pdb before moving on
if [ ! -f "{base_dir / out_pdb}" ]; then
    echo "[ERROR] step6.{traj + 1} exited 0 but no .pdb found — treating as failed." | tee -a "$LOG"
    exit 1
fi
echo "--- Finished step6.{traj + 1}: $(date) ---" | tee -a "$LOG"
"""
    return block


def generate_script():
    parser = argparse.ArgumentParser(
        description="Generate and execute a sequential OpenMM equilibration pipeline."
    )
    parser.add_argument('--system',     default='WT_restrained-boltz2', help='System name')
    parser.add_argument('--replica',    type=int, default=0,            help='Replica index')

    # Single-step or range
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--traj',       type=int,
                       help='Single trajectory index (e.g. 3 → step6.4)')
    group.add_argument('--traj_range', type=int, nargs=2, metavar=('START', 'END'),
                       help='Inclusive range of traj indices, e.g. --traj_range 0 5 '
                            'runs step6.1 through step6.6 sequentially')

    parser.add_argument('--platform',    default='CUDA',
                        choices=['CUDA', 'OpenCL', 'CPU'], help='Compute platform')
    parser.add_argument('--toppar',      default='toppar.str',
                        help='Path to toppar.str')
    parser.add_argument('--output_dir',  default='.',
                        help='Directory to write the generated script')
    parser.add_argument('--delay_hours', type=float, default=0.0,
                        help='Delay before first step starts (hours)')
    args = parser.parse_args()

    # Resolve traj list
    if args.traj is not None:
        traj_list = [args.traj]
    else:
        t_start, t_end = args.traj_range
        if t_start > t_end:
            parser.error("traj_range START must be <= END")
        traj_list = list(range(t_start, t_end + 1))

    # Path setup
    base_dir     = Path.cwd().parent.absolute()
    sim_rel_path = Path(f"minimization/{args.system}/Rep-{args.replica}")

    # Ensure base output dirs exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    (base_dir / "jobs").mkdir(parents=True, exist_ok=True)

    # Script metadata
    t_label   = (f"eq{traj_list[0]:03d}" if len(traj_list) == 1
                 else f"eq{traj_list[0]:03d}-eq{traj_list[-1]:03d}")
    session   = f"rep{args.replica}_{t_label}"
    logfile   = f"jobs/{args.system}_rep{args.replica}_{t_label}.log"
    delay_sec = int(args.delay_hours * 3600)

    # Build per-step bash blocks
    step_blocks = "\n".join(
        build_step_block(args, t, base_dir, sim_rel_path, logfile)
        for t in traj_list
    )

    bash_content = f"""#!/bin/bash
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# System : {args.system}  Replica: {args.replica}
# Steps  : step6.{traj_list[0]+1} → step6.{traj_list[-1]+1}  (traj {traj_list[0]}–{traj_list[-1]})

cd {base_dir}
source ~/miniconda3/etc/profile.d/conda.sh
conda activate openff

export OPENMM_CPU_THREADS=16
export OMP_NUM_THREADS=16

LOG="{logfile}"
SESSION="{session}"

echo "=== Pipeline started: $(date) ===" | tee -a "$LOG"
echo "    Steps: step6.{traj_list[0]+1} to step6.{traj_list[-1]+1}" | tee -a "$LOG"

# Optional startup delay
if [ {delay_sec} -gt 0 ]; then
    echo "[info] Sleeping {delay_sec}s before starting..." | tee -a "$LOG"
    sleep {delay_sec}
fi
{step_blocks}
echo "=== Pipeline complete: $(date) ===" | tee -a "$LOG"
"""

    script_name = f"{args.system}_rep{args.replica}_{t_label}.sh"
    script_path = Path(args.output_dir) / script_name

    script_path.write_text(bash_content)
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    print(f"Script generated: {script_path}")

    # Launch inside tmux (or fallback to nohup)
    try:
        result = subprocess.run(["tmux", "new-session", "-d", "-s", session,
                                 f"bash {script_path}"], check=False)
        if result.returncode == 0:
            print(f"[info] Launched in tmux session '{session}'")
            print(f"[info] Monitor with:  tmux attach -t {session}")
            print(f"[info] Log file:      {base_dir / logfile}")
        else:
            print("[warn] tmux launch failed, falling back to nohup")
            subprocess.Popen(["nohup", "bash", str(script_path)],
                             stdout=open(base_dir / logfile, "a"),
                             stderr=subprocess.STDOUT)
    except FileNotFoundError:
        print("[warn] tmux not found, falling back to nohup")
        subprocess.Popen(["nohup", "bash", str(script_path)],
                         stdout=open(base_dir / logfile, "a"),
                         stderr=subprocess.STDOUT)


if __name__ == "__main__":
    generate_script()
