# Genetic/Neuroevolution Hyperparameters — Quick Guide

Below is a succinct explainer of each field you posted, what it does, how changing it affects training, and rough sane ranges. The context assumed is a **GA/ES-style population training** of a policy/network where offspring are created by crossover + Gaussian mutation and evaluated over K episodes.

---

## Core GA population

* **`pop_size: 128`**
  Number of individuals (policies) per generation.
  **↑ larger** → better exploration & stability, **but** more compute per generation.
  *Typical:* 32–512 depending on budget.

* **`elites: 10`**
  Top-N individuals copied unchanged to the next generation (elitism).
  **↑ higher** → preserves strong solutions, avoids regression; **too high** reduces diversity.
  *Rule of thumb:* 2–10% of `pop_size`.

* **`tournament_k: 3`**
  Tournament selection size (pick the best of k random candidates).
  **↑ higher** → stronger selection pressure (faster convergence), **but** higher risk of premature convergence.
  *Typical:* 2–5.

## Reproduction (crossover + mutation)

* **`crossover_rate: 0.7`**
  Probability that a pair uses **crossover** to produce offspring (else pure cloning+mutation).
  **↑ higher** → more mixing of good traits; **too high** can break well‑adapted structures.
  *Typical:* 0.5–0.9.

* **`mut_prob: 0.08`**
  Per-parameter probability of applying a perturbation.
  Effective expected mutated fraction ≈ *8%* of weights per child.
  **↑ higher** → more exploration; **too high** ≈ random search.
  *Typical:* 0.01–0.2 depending on network size.

* **`mut_sigma_scale: 0.05`**, **`mut_sigma_floor: 0.02`**
  Gaussian noise scale per tensor:
  $**sigma** = max(`mut_sigma_scale` · *tensor.std()*, `mut_sigma_floor`)$
  Ensures nonzero noise even when a layer’s weights have tiny variance.
  **↑ sigma** → bigger steps/exploration; **too large** destroys structure.

## Evaluation budget

* **`eval_K: 32`**
  Episodes used to score **each** individual (averaged).
  **↑ higher** → lower reward variance & safer selection, **but** cost scales with `pop_size·K`.
  *Typical:* 5–64 (depends on environment stochasticity).

* **`batch_eval: True`, `batch_size: 8`**
  Evaluate up to `batch_size` episodes/environments concurrently to speed up the `K` rollouts.
  Increase until you saturate CPU/GPU; watch for memory/OS handle limits.

## Runtime & reproducibility

* **`device: "cuda"`**
  Device for model forward passes. Env stepping may still be CPU-bound unless vectorized on GPU.
  If CUDA is unavailable, fall back to CPU.

* **`seed: 1234`**
  RNG seed for reproducibility (selection, mutation, environment RNG if plumbed through).
  Change to run multiple independent trials.

* **`save_dir: "checkpoints"`**
  Folder for best (or per-generation) snapshots.

## Reward shaping / penalties (passed to Evaluator)

Weights applied to auxiliary terms in the fitness/reward:

* **`w_hp_margin: 0.25`**
  Scales the **HP margin** term (e.g., normalized *AI\_HP − Opp\_HP* at end or per step).
  **↑ higher** → favors winning by larger HP difference.

* **`w_brevity: 0.10`**
  Rewards **shorter fights** (fewer steps/rounds).
  **↑ higher** → encourages aggressive finishes; too high may cause reckless play.

* **`w_skip_pen: 0.01`**
  **Penalty per voluntary `Skip`** chosen by the AI.
  **↑ higher** → discourages wasting turns; too high may prevent strategic skipping.

* **`w_stun_pen: 0.02`**
  **Penalty per AI turn lost to stun** (outcome sensitivity).
  Encourages building/choosing actions that avoid being stunned or break stun chains.

* **`w_no_damage_pen: 0.10`**
  **Penalty if the AI deals zero total damage** during an episode.
  Prevents degenerate defensive/idle policies.

---

## Quick tuning tips

1. **Compute budget first.** The dominant cost is roughly `pop_size × eval_K` (modulo batching). Scale those with your hardware.
2. **Balance exploration/exploitation.** Start with `mut_prob ≈ 0.05–0.1`, `sigma_scale ≈ 0.05`, `sigma_floor ≈ 0.01–0.02`; adjust based on stagnation vs. instability.
3. **Watch selection pressure.** If diversity collapses early, lower `tournament_k` or `elites`, or raise mutation slightly.
4. **Stochastic envs need higher K.** If returns vary wildly, increase `eval_K` (and batch size to compensate).
5. **Shaping weights**: increase only to guide behavior; if the agent optimizes the shaped terms but plays poorly, reduce them and lean more on true win/lose reward.

---

## What happens if…

* **Training stalls** → mildly increase `mut_prob` or `mut_sigma_scale`; lower `tournament_k`; add a **diversity injection** every N gens.
* **Chaotic fitness** → raise `eval_K`; reduce mutation magnitudes; reduce `crossover_rate`.
* **Overly passive agent** → bump `w_brevity`, `w_no_damage_pen`, and/or reduce `w_skip_pen` if skipping is needed tactically.
