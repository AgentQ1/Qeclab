# Copy-paste prompts, one per computer

Each person pastes their block into Claude (Claude Code on their laptop, or any Claude that can run commands), or runs the commands themselves.

## Computer 1
```text
You are running job "computer 1" for our hackathon decoder benchmark.
Clone https://github.com/MGCquantum/MGCcorrection and cd into challenge-1-ml-decoder-kit. Read ../SPEC.md for context only.
Setup: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt scikit-learn matplotlib (relay-bp needs Rust; install it from rustup.rs if the build fails). mkdir -p results.
Quick check: python run_job.py --basis X --p 0.004 --shots 50 --seed 2 --decoders bp relay --out results/check.npz ; it must print one summary line. Then delete results/check.npz and tell me it worked.
Rules: do NOT edit any code, seeds, shot counts or file names. On a Mac, prefix every long command with caffeinate -i. Run the two commands blocks below in two separate terminals at the same time where there are two. When each command finishes, show me its one summary line. If anything errors, show me the last 10 lines and stop; don't change code to fix it.
When everything has finished: git pull && git add -f results/*.npz && git commit -m "results: computer 1" && git push.
Commands (one terminal):
python run_job.py --basis X --p 0.003 --shots 5000 --seed 2 --decoders bp relay --out results/test_X_p0.003.npz
python run_job.py --basis X --p 0.003 --shots 5000 --seed 1 --decoders bp --out results/train_X_p0.003.npz
```

## Computer 2
```text
You are running job "computer 2" for our hackathon decoder benchmark.
Clone https://github.com/MGCquantum/MGCcorrection and cd into challenge-1-ml-decoder-kit. Read ../SPEC.md for context only.
Setup: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt scikit-learn matplotlib (relay-bp needs Rust; install it from rustup.rs if the build fails). mkdir -p results.
Quick check: python run_job.py --basis X --p 0.004 --shots 50 --seed 2 --decoders bp relay --out results/check.npz ; it must print one summary line. Then delete results/check.npz and tell me it worked.
Rules: do NOT edit any code, seeds, shot counts or file names. On a Mac, prefix every long command with caffeinate -i. Run the two commands blocks below in two separate terminals at the same time where there are two. When each command finishes, show me its one summary line. If anything errors, show me the last 10 lines and stop; don't change code to fix it.
When everything has finished: git pull && git add -f results/*.npz && git commit -m "results: computer 2" && git push.
Commands (one terminal):
python run_job.py --basis Z --p 0.003 --shots 5000 --seed 2 --decoders bp relay --out results/test_Z_p0.003.npz
python run_job.py --basis Z --p 0.003 --shots 5000 --seed 1 --decoders bp --out results/train_Z_p0.003.npz
```

## Computer 3
```text
You are running job "computer 3" for our hackathon decoder benchmark.
Clone https://github.com/MGCquantum/MGCcorrection and cd into challenge-1-ml-decoder-kit. Read ../SPEC.md for context only.
Setup: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt scikit-learn matplotlib (relay-bp needs Rust; install it from rustup.rs if the build fails). mkdir -p results.
Quick check: python run_job.py --basis X --p 0.004 --shots 50 --seed 2 --decoders bp relay --out results/check.npz ; it must print one summary line. Then delete results/check.npz and tell me it worked.
Rules: do NOT edit any code, seeds, shot counts or file names. On a Mac, prefix every long command with caffeinate -i. Run the two commands blocks below in two separate terminals at the same time where there are two. When each command finishes, show me its one summary line. If anything errors, show me the last 10 lines and stop; don't change code to fix it.
When everything has finished: git pull && git add -f results/*.npz && git commit -m "results: computer 3" && git push.
First, the setup check: python baseline.py --p 0.004 --shots 1000 . Expect relay-bp around 10 failures and bposd around 50 (per basis, roughly). Show me the output; if it is far off, stop.
Terminal 1:
python run_job.py --basis X --p 0.004 --shots 2000 --seed 2 --decoders bp relay bposd --out results/test_X_p0.004.npz
python run_job.py --basis X --p 0.004 --shots 5000 --seed 1 --decoders bp --out results/train_X_p0.004.npz
Terminal 2:
python run_job.py --basis Z --p 0.004 --shots 2000 --seed 2 --decoders bp relay bposd --out results/test_Z_p0.004.npz
python run_job.py --basis Z --p 0.004 --shots 5000 --seed 1 --decoders bp --out results/train_Z_p0.004.npz
```

## Computer 4
```text
You are running job "computer 4" for our hackathon decoder benchmark.
Clone https://github.com/MGCquantum/MGCcorrection and cd into challenge-1-ml-decoder-kit. Read ../SPEC.md for context only.
Setup: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt scikit-learn matplotlib (relay-bp needs Rust; install it from rustup.rs if the build fails). mkdir -p results.
Quick check: python run_job.py --basis X --p 0.004 --shots 50 --seed 2 --decoders bp relay --out results/check.npz ; it must print one summary line. Then delete results/check.npz and tell me it worked.
Rules: do NOT edit any code, seeds, shot counts or file names. On a Mac, prefix every long command with caffeinate -i. Run the two commands blocks below in two separate terminals at the same time where there are two. When each command finishes, show me its one summary line. If anything errors, show me the last 10 lines and stop; don't change code to fix it.
When everything has finished: git pull && git add -f results/*.npz && git commit -m "results: computer 4" && git push.
Terminal 1:
python run_job.py --basis X --p 0.005 --shots 2000 --seed 2 --decoders bp relay --out results/test_X_p0.005.npz
python run_job.py --basis X --p 0.005 --shots 5000 --seed 1 --decoders bp --out results/train_X_p0.005.npz
Terminal 2:
python run_job.py --basis Z --p 0.005 --shots 2000 --seed 2 --decoders bp relay --out results/test_Z_p0.005.npz
python run_job.py --basis Z --p 0.005 --shots 5000 --seed 1 --decoders bp --out results/train_Z_p0.005.npz
```

## Computer 5
```text
You are running job "computer 5" for our hackathon decoder benchmark.
Clone https://github.com/MGCquantum/MGCcorrection and cd into challenge-1-ml-decoder-kit. Read ../SPEC.md for context only.
Setup: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt scikit-learn matplotlib (relay-bp needs Rust; install it from rustup.rs if the build fails). mkdir -p results.
Quick check: python run_job.py --basis X --p 0.004 --shots 50 --seed 2 --decoders bp relay --out results/check.npz ; it must print one summary line. Then delete results/check.npz and tell me it worked.
Rules: do NOT edit any code, seeds, shot counts or file names. On a Mac, prefix every long command with caffeinate -i. Run the two commands blocks below in two separate terminals at the same time where there are two. When each command finishes, show me its one summary line. If anything errors, show me the last 10 lines and stop; don't change code to fix it.
When everything has finished: git pull && git add -f results/*.npz && git commit -m "results: computer 5" && git push.
Terminal 1:
for f in 0.25 0.5 0.75; do python run_job.py --basis X --p 0.004 --f $f --shots 1000 --seed 2 --decoders bposd bposd_flags --out results/erase_X_p0.004_f$f.npz; done
Terminal 2:
for f in 0.25 0.5 0.75; do python run_job.py --basis Z --p 0.004 --f $f --shots 1000 --seed 2 --decoders bposd bposd_flags --out results/erase_Z_p0.004_f$f.npz; done
```

## Agastya (analysis, any computer, any time)
```text
Clone https://github.com/MGCquantum/MGCcorrection, cd challenge-1-ml-decoder-kit, set up the venv as in TEAM_PLAN.md step 2.
Then: git pull && python analyze.py --dir results
Show me the printed table and open results/results.png. Do not edit code. Compare the numbers against the targets in ../SPEC.md ("What working means") and tell me which targets pass and which fail.
```
