# Genetic/Neuroevolution Hyperparameters — Quick Guide (EN)

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
  Tournament selection size.
  **↑ higher** → stronger selection pressure (faster convergence), **but** higher risk of premature convergence.
  *Typical:* 2–5.

## Reproduction

* **`crossover_rate: 0.7`**
  Probability of crossover when producing offspring.
  **↑ higher** → more mixing of traits; **too high** can disrupt good structures.
  *Typical:* 0.5–0.9.

* **`mut_prob: 0.08`**
  Per-parameter mutation probability (\~8% of weights).
  **↑ higher** → more exploration; **too high** ≈ random search.
  *Typical:* 0.01–0.2.

* **`mut_sigma_scale: 0.05`, `mut_sigma_floor: 0.02`**
  Gaussian noise scale:
  σ = max(`scale`·std, `floor`).
  Ensures nonzero noise even if variance is small.
  **↑ sigma** → bigger steps; too high destroys structure.

## Evaluation budget

* **`eval_K: 32`**
  Episodes per individual (averaged).
  **↑ higher** → less variance, but cost ∝ `pop_size·K`.
  *Typical:* 5–64.

* **`batch_eval: True`, `batch_size: 8`**
  Parallel evaluation to speed up rollouts.
  Increase until CPU/GPU saturated.

## Runtime & reproducibility

* **`device: "cuda"`**
  Device for model forward passes.
  If no CUDA → CPU.

* **`seed: 1234`**
  RNG seed for reproducibility.

* **`save_dir: "checkpoints"`**
  Folder for snapshots.

## Reward shaping / penalties

* **`w_hp_margin: 0.25`** — favors winning with larger HP difference.
* **`w_brevity: 0.10`** — rewards shorter fights.
* **`w_skip_pen: 0.01`** — penalty for voluntary skips.
* **`w_stun_pen: 0.02`** — penalty per turn lost to stun.
* **`w_no_damage_pen: 0.10`** — penalty if AI deals zero damage.

---

# Hyperparamètres Génétiques / Neuroévolution — Guide Rapide (FR)

Résumé de chaque champ, son rôle, impact, et plages de valeurs conseillées. Contexte : entraînement **GA/ES** d’une politique où les descendants sont créés par croisement + mutation gaussienne et évalués sur K épisodes.

---

## Population de base

* **`pop_size: 128`**
  Nombre d’individus par génération.
  **↑ plus grand** → meilleure exploration, **mais** plus de calcul.
  *Typique :* 32–512.

* **`elites: 10`**
  Meilleurs individus copiés tels quels.
  **↑ plus grand** → conserve la qualité, **mais** réduit diversité.
  *Règle :* 2–10%.

* **`tournament_k: 3`**
  Taille du tournoi de sélection.
  **↑ plus grand** → convergence rapide, risque de prématurité.
  *Typique :* 2–5.

## Reproduction

* **`crossover_rate: 0.7`**
  Probabilité de croisement.
  **↑ plus grand** → mélange de traits ; trop haut casse des structures.
  *Typique :* 0.5–0.9.

* **`mut_prob: 0.08`**
  Proba par paramètre de mutation (\~8%).
  **↑ plus grand** → exploration ; trop grand ≈ recherche aléatoire.
  *Typique :* 0.01–0.2.

* **`mut_sigma_scale: 0.05`, `mut_sigma_floor: 0.02`**
  Échelle du bruit gaussien :
  σ = max(`scale`·std, `floor`).
  Assure un bruit non nul.
  **↑ sigma** → grands sauts ; trop grand détruit la structure.

## Budget d’évaluation

* **`eval_K: 32`**
  Épisodes par individu.
  **↑ plus grand** → variance réduite, coût ∝ `pop_size·K`.
  *Typique :* 5–64.

* **`batch_eval: True`, `batch_size: 8`**
  Évalue en parallèle.
  Augmente jusqu’à saturation CPU/GPU.

## Exécution & reproductibilité

* **`device: "cuda"`** — périphérique.
* **`seed: 1234`** — graine RNG.
* **`save_dir: "checkpoints"`** — dossier de sauvegarde.

## Pondérations de récompense / pénalités

* **`w_hp_margin: 0.25`** — favorise une grande marge de PV.
* **`w_brevity: 0.10`** — récompense les combats courts.
* **`w_skip_pen: 0.01`** — pénalité par skip volontaire.
* **`w_stun_pen: 0.02`** — pénalité par tour perdu au stun.
* **`w_no_damage_pen: 0.10`** — pénalité si aucun dégât infligé.

---

## Conseils rapides

1. **Budget.** Coût ≈ `pop_size × eval_K`.
2. **Équilibre.** `mut_prob` \~0.05–0.1, `sigma_scale` \~0.05, `sigma_floor` \~0.01–0.02.
3. **Pression.** Si diversité chute vite → baisser `tournament_k`/`elites`, ou monter un peu la mutation.
4. **Stochastique.** Si résultats volatils → monter `eval_K`.
5. **Shaping.** Utiliser pondérations comme guidage, pas comme objectif principal.

---

## Et si…

* **Entraînement stagne** → augmenter `mut_prob`/`sigma`, baisser `tournament_k`, injection de diversité.
* **Fitness chaotique** → augmenter `eval_K`, réduire mutation ou `crossover_rate`.
* **Agent passif** → augmenter `w_brevity`, `w_no_damage_pen`, réduire `w_skip_pen` si nécessaire.
