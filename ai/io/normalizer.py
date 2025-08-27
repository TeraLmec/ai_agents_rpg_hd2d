def normalizer(data: dict) -> dict:

    min_max_dict = {
        # Fighter level and basic stats
        "level": {"min": 0, "max": 5},
        "hpMax": {"min": 0, "max": 480},
        "hp": {"min": 0, "max": 480},
        "speed": {"min": 0, "max": 10},
        "apMax": {"min": 0, "max": 5},
        "ap": {"min": 0, "max": 5},
        "stat": {"min": 0, "max": 187},

        # Action costs
        "cost": {"min": 0, "max": 4},

        # Effect codes
        "code": {"min": 0, "max": 10},
        "multiplier": {"min": 0, "max": 75},
        "duration": {"min": 0, "max": 4},

        # Combat states
        "round_count": {"min": 0, "max": 100},
        "action_left": {"min": 0, "max": 3}
    }

    def normalize_value(value, field_name):
        """Normalize a single value based on its field name"""
        if field_name in min_max_dict:
            min_val = min_max_dict[field_name]["min"]
            max_val = min_max_dict[field_name]["max"]
            # === CHANGED: clamp to [0,1] for safety ==================
            if max_val != min_val:
                norm = (value - min_val) / (max_val - min_val)
                return max(0.0, min(1.0, norm))  # CHANGED
            return 0.0
        return value

    def normalize_effect(effect):
        """Normalize an effect object"""
        return {
            "code": normalize_value(effect["code"], "code"),
            "multiplier": normalize_value(effect["multiplier"], "multiplier"),
            "duration": normalize_value(effect["duration"], "duration")
        }

    def normalize_action(action):
        """Normalize an action object"""
        return {
            "cost": normalize_value(action["cost"], "cost"),
            "effects": [normalize_effect(effect) for effect in action["effects"]]
        }

    # Create normalized data structure
    normalized_data = {}

    # Normalize enemy recent actions
    normalized_data["enemy_recent_actions"] = [
        normalize_action(action) for action in data["enemy_recent_actions"]
    ]

    # Normalize actifs
    normalized_data["actifs"] = {
        "ai_actifs": [normalize_effect(actif) for actif in data["actifs"]["ai_actifs"]],
        "enemy_actifs": [normalize_effect(actif) for actif in data["actifs"]["enemy_actifs"]]
    }

    # Normalize combat stats
    ai_stats = data["combat_stats"]["ai_stats"]
    enemy_stats = data["combat_stats"]["enemy_stats"]

    normalized_data["combat_stats"] = {
        "ai_stats": {
            "level": normalize_value(ai_stats["level"], "level"),
            "hpMax": normalize_value(ai_stats["hpMax"], "hpMax"),
            "hp": normalize_value(ai_stats["hp"], "hp"),
            "speed": normalize_value(ai_stats["speed"], "speed"),
            "apMax": normalize_value(ai_stats["apMax"], "apMax"),
            "ap": normalize_value(ai_stats["ap"], "ap"),
            "stats": {
                "phy_atk": normalize_value(ai_stats["stats"]["phy_atk"], "stat"),
                "phy_def": normalize_value(ai_stats["stats"]["phy_def"], "stat"),
                "spi_atk": normalize_value(ai_stats["stats"]["spi_atk"], "stat"),
                "spi_def": normalize_value(ai_stats["stats"]["spi_def"], "stat"),
                "ele_atk": normalize_value(ai_stats["stats"]["ele_atk"], "stat"),
                "ele_def": normalize_value(ai_stats["stats"]["ele_def"], "stat")
            }
        },
        "enemy_stats": {
            "level": normalize_value(enemy_stats["level"], "level"),
            "hpMax": normalize_value(enemy_stats["hpMax"], "hpMax"),
            "hp": normalize_value(enemy_stats["hp"], "hp")
        }
    }

    # Normalize combat states
    normalized_data["combat_states"] = {
        "round_count": normalize_value(data["combat_states"]["round_count"], "round_count"),
        "action_left": normalize_value(data["combat_states"]["action_left"], "action_left")
    }

    # === CHANGED: fix key name 'ai_available_actions' = consistent ===
    normalized_data["ai_available_actions"] = [      # CHANGED
        normalize_action(action) for action in data["ai_available_actions"]  # CHANGED
    ]

    # Normalize actions history
    normalized_data["ai_actions_history"] = [
        normalize_action(action) for action in data["ai_actions_history"]
    ]

    return normalized_data
