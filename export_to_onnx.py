import torch, os, json, argparse

# --- Définition exacte du modèle (train.py) ---
class PolicyMLP(torch.nn.Module):
    def __init__(self, in_dim=92, h1=128, h2=64, out_dim=5):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(in_dim, h1), torch.nn.ReLU(),
            torch.nn.Linear(h1, h2),     torch.nn.ReLU(),
            torch.nn.Linear(h2, out_dim),
        )
    def forward(self, x): return self.net(x)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", default="checkpoints/best_final.pt", help="chemin vers le checkpoint")
    parser.add_argument("--out", default="model.onnx", help="fichier onnx de sortie")
    parser.add_argument("--manifest", default="model_manifest.json", help="fichier json de sortie")
    args = parser.parse_args()

    device = torch.device("cpu")

    # 1) Reconstruit le modèle
    model = PolicyMLP().to(device).eval()

    # 2) Charge le checkpoint
    state = torch.load(args.ckpt, map_location=device)
    # selon l’entraînement, ça peut être un state_dict direct ou sous clé
    if "state_dict" in state: 
        state = state["state_dict"]
    elif "best_state_dict" in state: 
        state = state["best_state_dict"]
    model.load_state_dict(state, strict=True)

    # 3) Dummy input
    ex = torch.randn(1, 92, dtype=torch.float32, device=device)

    # 4) Export ONNX
    torch.onnx.export(
        model, ex, args.out,
        input_names=["features"],
        output_names=["logits"],
        dynamic_axes={"features": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17
    )

    # 5) Manifest (contrat UE)
    manifest = {
        "version": 1,
        "inputs": {
            "features": {
                "dtype": "float32",
                "shape": ["batch", 92],
                "feature_order": [  # à remplir si tu veux documenter chaque feature
                    # ex: "ply_recent_actions[0].cost", ..., "ai_actions_history[1].effects[1].duration"
                ],
                "normalization": "none"
            }
        },
        "outputs": {
            "logits": {
                "shape": ["batch", 5],
                "semantics": [
                    "prob_action1",
                    "prob_action2",
                    "prob_action3",
                    "prob_action4",
                    "prob_skip"
                ]
            }
        },
        "postproc": {
            "selection": {
                "type": "argmax_or_topk",
                "k": 1   # côté UE tu choisis 3 fois par tour
            },
            "masking": "engine_side"
        }
    }
    with open(args.manifest, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Export terminé : {args.out}, manifest : {args.manifest}")


if __name__ == "__main__":
    main()