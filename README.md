# Cold Spray Additive Manufacturing (CSAM) Deployment Optimization using Bender's Decomposition

Mobile Cold-Spray Additive Manufacturing facility deployment model.

## Setup

```bash
git clone <your-repo>
cd csam-benders-core
'''

# Create virtual environment (recommended)
'''bash 
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
'''

Running Experiments
'''bash
Single Run
python -m experiment_scripts.run_single --max_csam 3 --u_l1 80 --c_dummy 5000 --seed 456
'''

Sweep Experiments
'''bash
python -m experiment_scripts.run_sweep
python -m experiment_scripts.analyze_sweep
'''

Results are organized under experiments/sweeps/.

Project Structure

model/ — Core network & optimization logic
experiment_scripts/ — Running experiments
visualization_scripts/ — Plotting tools
experiments/sweeps/ — Organized results

See experiments/sweeps/ for latest results.