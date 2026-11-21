# Team plan: who does what, step by step

Five people. Four of you lend a laptop, and one runs the analysis and the pitch. You don't need to understand the code to run it.

| Person | Laptop job | Also owns |
|---|---|---|
| **A** (fastest laptop) | p = 0.004 sweep + BP-OSD sanity check | Checking the setup is correct (step 4) |
| **B** | p = 0.003 sweep | README for the repo |
| **C** | p = 0.005 sweep | Plots in the slides |
| **D** | Erasure experiment | Explaining erasure on the slide |
| **Agastya** | Analysis (`analyze.py`), any laptop | Mentors, the go/no-go calls, slides, the pitch |

If someone's laptop can't install relay-BP (step 2 fails), they hand their job to Agastya's laptop and take over slides.

---

## Step 1. Get the code (everyone, 5 min)
```bash
git clone https://github.com/MGCquantum/MGCcorrection
cd MGCcorrection
```
If `lossy.py`, `run_job.py`, `analyze.py` and `RUN.md` aren't in `challenge-1-ml-decoder-kit/` yet, unzip `mgccorrection-code.zip` into this folder.

## Step 2. Install (everyone, 5–15 min)
```bash
cd challenge-1-ml-decoder-kit
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt scikit-learn matplotlib
```
- relay-BP needs Rust. If install fails on `relay-bp`, install Rust from https://rustup.rs, open a new terminal and repeat.
- Every new terminal needs `source .venv/bin/activate` first.

## Step 3. Quick check (everyone, 2 min)
```bash
mkdir -p results
python run_job.py --basis X --p 0.004 --shots 50 --seed 2 --decoders bp relay --out results/check.npz
```
It should print one line like `results/check.npz [20 s] bp: fails .. relay: fails ..`. Then delete `results/check.npz`. **Post "ready" in the group chat.**

## Step 4. Person A confirms the setup is correct (15 min)
```bash
python baseline.py --p 0.004 --shots 1000
```
- relay-BP should fail about 1 in 100 pairs, which is roughly 10 failures.
- BP-OSD should fail about 5 in 100, which is roughly 50 failures.
- If these are far off, stop and tell Agastya.

## Step 5. Start your long job (A–D)
Open **two terminals** and run the X commands in one and the Z commands in the other, so both run at once.
- **Mac:** put `caffeinate -i` before each command so the laptop doesn't sleep.
- Keep the laptop plugged in and the lid open.

**A (p = 0.004):**
```bash
# terminal 1
python run_job.py --basis X --p 0.004 --shots 2000 --seed 2 --decoders bp relay bposd --out results/test_X_p0.004.npz
python run_job.py --basis X --p 0.004 --shots 5000 --seed 1 --decoders bp --out results/train_X_p0.004.npz
# terminal 2: the same two commands with --basis Z and _Z_ in the file names
```
**B (p = 0.003):** same as A but with `--p 0.003`, `p0.003` in the file names, `--shots 5000` on the test job, and `--decoders bp relay` (no `bposd`).
**C (p = 0.005):** same as A but with `--p 0.005`, `p0.005` in the file names, and `--decoders bp relay` (no `bposd`).
**D (erasure):**
```bash
# terminal 1
for f in 0.25 0.5 0.75; do python run_job.py --basis X --p 0.004 --f $f --shots 1000 --seed 2 --decoders bposd bposd_flags --out results/erase_X_p0.004_f$f.npz; done
# terminal 2: the same with --basis Z and erase_Z_ in the file name
```

**Rules:**
- **Never change `--seed`:** 2 for test, 1 for train.
- **Copy file names exactly,** because `analyze.py` finds files by name.
- When a command finishes, **paste its one summary line** in the group chat.

## Step 6. Hand over results (A–D)
Upload your `results/*.npz` files to the shared Drive folder, or push them:
```bash
git add -f results/*.npz && git commit -m "results: <your job>" && git push
```

## Step 7. Analysis (Agastya, any time, seconds)
Put every `.npz` file in one `results/` folder, then:
```bash
python analyze.py --dir results
```
You get a printed table, `results/results.csv` and `results/results.png`. Run it as soon as the first files arrive, so you can find problems early.

---

## Checkpoints (Agastya calls these)
| Time | Check | If it fails |
|---|---|---|
| 5:30 pm | Everyone posted "ready" (step 3) | Move that person's job to another laptop |
| 6:00 pm | Person A's setup check matches (step 4) | Stop everyone and fix it first |
| 8:00 pm | First erasure files are in, and `bposd_flags` fails less than `bposd` | Drop the erasure story and pitch the hybrid only |
| 11:00 pm | All jobs finished or running | Rerun anything missing overnight |
| 10:00 am Sun | Final `analyze.py` run; numbers locked | Use whatever is complete |
| 1:45 pm Sun | Code, results, plot and README pushed | — |

## If more time or laptops free up
- Rerun the test jobs with more shots (5,000 at p = 0.004 and 0.005) for tighter error bars. Use a new file name, keep the same seed, and replace the old file.
- Add more erasure points (`--f 0.1`, `0.9`).
