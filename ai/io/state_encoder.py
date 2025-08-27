import torch, json
from ai.io.normalizer import normalizer

class state_encoder():
    def __init__(self):
        pass

    def data_to_tensor(self, data, dtype=torch.float32, device="cuda"):
        """
        Transform a list of numbers into a PyTorch tensor.
        """
        return torch.tensor(data, dtype=dtype, device=device)

    def json_to_list(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return self.dict_to_list(data)

    def dict_to_list(self, data_dict):
        """Convert a raw observation dict to a flat feature list (length=92)."""
        normalized_data = normalizer(data_dict)

        def extract_effect_values(effect):
            return [effect["code"], effect["multiplier"], effect["duration"]]

        def extract_action_values(action):
            values = [action["cost"]]
            for effect in action["effects"]:
                values.extend(extract_effect_values(effect))
            return values

        values_list = []

        for action in normalized_data["enemy_recent_actions"]:
            values_list.extend(extract_action_values(action))

        for actif in normalized_data["actifs"]["ai_actifs"]:
            values_list.extend(extract_effect_values(actif))

        for actif in normalized_data["actifs"]["enemy_actifs"]:
            values_list.extend(extract_effect_values(actif))

        ai_stats = normalized_data["combat_stats"]["ai_stats"]
        values_list.extend([
            ai_stats["level"], ai_stats["hpMax"], ai_stats["hp"],
            ai_stats["speed"], ai_stats["apMax"], ai_stats["ap"]
        ])

        ai_detailed_stats = ai_stats["stats"]
        values_list.extend([
            ai_detailed_stats["phy_atk"], ai_detailed_stats["phy_def"],
            ai_detailed_stats["spi_atk"], ai_detailed_stats["spi_def"],
            ai_detailed_stats["ele_atk"], ai_detailed_stats["ele_def"]
        ])

        enemy_stats = normalized_data["combat_stats"]["enemy_stats"]
        values_list.extend([enemy_stats["level"], enemy_stats["hpMax"], enemy_stats["hp"]])

        combat_states = normalized_data["combat_states"]
        values_list.extend([combat_states["round_count"], combat_states["action_left"]])

        for action in normalized_data["ai_available_actions"]:
            values_list.extend(extract_action_values(action))

        for action in normalized_data["ai_actions_history"]:
            values_list.extend(extract_action_values(action))

        assert len(values_list) == 92, f"Expected 92 features, got {len(values_list)}"
        return values_list

    # === NEW: build the [5]-action availability mask ==========================
    def build_availability_mask(self, normalized_data) -> torch.Tensor:
        """
        Returns a tensor of shape (5,) for [P1,P2,P3,P4,P5],
        where P1..P4 are 1 if (slot non-empty AND cost <= ap), else 0.
        P5 (Skip) can be 0 here; the decoder will force it to 1.
        """
        ap = normalized_data["combat_stats"]["ai_stats"]["ap"]  # already normalized [0,1]
        # cost is also normalized [0,1] with max=4 → compare in normalized space
        mask = [0, 0, 0, 0, 0]
        actions = normalized_data["ai_available_actions"]  # CHANGED (same rename)

        for i in range(4):
            slot = actions[i]
            # slot is "non-empty" if it has at least one non-zero field
            slot_non_empty = (slot["cost"] > 0.0) or any(
                e["code"] > 0.0 or e["multiplier"] > 0.0 or e["duration"] > 0.0
                for e in slot["effects"]
            )
            # available if non-empty AND cost <= ap
            available = slot_non_empty and (slot["cost"] <= ap)
            mask[i] = 1 if available else 0

        # P5 (Skip) left as 0/1 here; decoder will force it to 1 anyway
        mask[4] = 0
        return torch.tensor(mask, dtype=torch.int32)
