import torch

def decode_action(nn_output, mask):
    """
    nn_output: tensor of shape (5,) from the model
    mask:   tensor of shape (5,), 1 = available, 0 = unavailable
            (Skip can be 0 here, we will force it to 1)

    Returns:
      probs: tensor of shape (5,), normalized probabilities
      choice: int index 0..4 of the chosen action
      output_json: dict with P1..P5 probabilities
    """
    # === NEW: ensure stable dtype ===============================
    nn_output = nn_output.to(torch.float32)
    mask = mask.to(torch.int)
    # ============================================================

    # 1. Force Skip (last index) to always be available
    mask = mask.clone()
    mask[-1] = 1

    # 2. Zero out nn_output for unavailable actions
    masked_nn_output = nn_output.clone()
    masked_nn_output[mask == 0] = -1e9  # very negative = prob ~ 0

    # 3. Softmax to turn nn_output into probabilities
    probs = torch.softmax(masked_nn_output, dim=0)

    # 4. Pick the action with the highest probability
    choice = int(torch.argmax(probs).item())

    # 5. Build JSON-style output
    output_json = {
        "P1": float(probs[0]),
        "P2": float(probs[1]),
        "P3": float(probs[2]),
        "P4": float(probs[3]),
        "P5": float(probs[4]),
        "chosen_index": choice
    }

    return probs, choice, output_json
