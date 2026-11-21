# How to run (one job list per laptop)

Setup once, on every laptop:
```bash
cd challenge-1-ml-decoder-kit
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt scikit-learn matplotlib     # relay-bp needs Rust: https://rustup.rs
```
On a Mac, put `caffeinate -i` in front of each command so the laptop doesn't sleep. Results go in `results/`.

## Laptop 1: p = 0.003 (longest)
```bash
python run_job.py --basis X --p 0.003 --shots 5000 --seed 2 --decoders bp relay --out results/test_X_p0.003.npz
python run_job.py --basis Z --p 0.003 --shots 5000 --seed 2 --decoders bp relay --out results/test_Z_p0.003.npz
python run_job.py --basis X --p 0.003 --shots 5000 --seed 1 --decoders bp --out results/train_X_p0.003.npz
python run_job.py --basis Z --p 0.003 --shots 5000 --seed 1 --decoders bp --out results/train_Z_p0.003.npz
```

## Laptop 2: p = 0.005
Same four commands with `--p 0.005` and `p0.005` in the file names, and `--shots 2000` on the test jobs.

## Laptop 3: p = 0.004 (+ BP-OSD sanity check)
Same four commands with `--p 0.004`, `--shots 2000` on the test jobs, and `--decoders bp relay bposd` on the test jobs.

## Laptop 4: erasure experiment (p = 0.004)
```bash
for f in 0.25 0.5 0.75; do for b in X Z; do
  python run_job.py --basis $b --p 0.004 --f $f --shots 1000 --seed 2 --decoders bposd bposd_flags --out results/erase_${b}_p0.004_f${f}.npz
done; done
```

## Laptop 5: analysis (anyone, any time; takes seconds)
Collect every `results/*.npz` file into one `results/` folder, then:
```bash
python analyze.py --dir results
```
This prints the table and writes `results/results.csv` and `results/results.png`.

Run a 50-shot version of any command first to check it works before starting the long one.
