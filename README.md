# csam-benders-core structure
csam-benders-core/
├── model/
│   ├── __init__.py
│   ├── network.py          # nodes, arcs, data structures
│   ├── parameters.py       # defaults + loading
│   └── core.py             # pure Benders solver
├── scripts/
│   ├── run_single.py
│   └── run_sweep.py
├── data/                   # (copy your existing CSVs/JSON here later)
├── experiments/            # auto-generated
├── output/                 # temporary CSVs
├── visualizations/
├── config/
│   └── sweeps.json         # optional
├── requirements.txt
└── README.md
