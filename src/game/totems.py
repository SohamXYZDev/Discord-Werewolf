"""
Canonical totem definitions and helpers for the Werewolf bot.
This centralizes totem metadata so commands and game logic use the same source of truth.
"""
from typing import Dict, List

TOTEMS: Dict[str, Dict] = {
    "death": {
        "name": "Death Totem",
        "description": "The recipient dies at the end of the night.",
        "type": "Harmful",
        "giver": "Shaman / Wolf Shaman"
    },
    "protection": {
        "name": "Protection Totem",
        "description": "Protects the holder from being killed for one night.",
        "type": "Beneficial",
        "giver": "Shaman / Wolf Shaman"
    },
    "revealing": {
        "name": "Revealing Totem",
        "description": "If the recipient is lynched the following day, their role is revealed but they do not die.",
        "type": "Mixed",
        "giver": "Shaman"
    },
    "influence": {
        "name": "Influence Totem",
        "description": "The holder's lynch vote counts twice during the next day.",
        "type": "Beneficial",
        "giver": "Shaman"
    },
    "impatience": {
        "name": "Impatience Totem",
        "description": "If the holder votes, the day may end immediately.",
        "type": "Beneficial",
        "giver": "Shaman"
    },
    "pacifism": {
        "name": "Pacifism Totem",
        "description": "The holder's vote is automatically counted as an abstain.",
        "type": "Harmful",
        "giver": "Wolf Shaman / Crazed Shaman"
    },
    "cursed": {
        "name": "Cursed Totem",
        "description": "Gives the 'cursed' template: you appear as a wolf to investigative roles.",
        "type": "Harmful",
        "giver": "Wolf Shaman"
    },
    "lycanthropy": {
        "name": "Lycanthropy Totem",
        "description": "If targeted by wolves, the holder is converted into a wolf instead of dying.",
        "type": "Harmful",
        "giver": "Wolf Shaman"
    },
    "retribution": {
        "name": "Retribution Totem",
        "description": "If the recipient is killed by wolves, one of the wolves that targeted them also dies.",
        "type": "Harmful",
        "giver": "Wolf Shaman"
    },
    "blinding": {
        "name": "Blinding Totem",
        "description": "The recipient becomes injured for the following day and cannot vote.",
        "type": "Harmful",
        "giver": "Wolf Shaman"
    },
    "deceit": {
        "name": "Deceit Totem",
        "description": "Investigations on the recipient will return misleading information.",
        "type": "Harmful",
        "giver": "Wolf Shaman"
    },
    "misdirection": {
        "name": "Misdirection Totem",
        "description": "Night abilities targeting the recipient may be redirected to someone else.",
        "type": "Mixed",
        "giver": "Wolf Shaman"
    },
    "luck": {
        "name": "Luck Totem",
        "description": "Abilities targeting the recipient have a chance to be redirected to an adjacent player.",
        "type": "Mixed",
        "giver": "Wolf Shaman"
    },
    "silence": {
        "name": "Silence Totem",
        "description": "The recipient cannot use special abilities for the next day and night.",
        "type": "Harmful",
        "giver": "Shaman / Wolf Shaman"
    },
    "pestilence": {
        "name": "Pestilence Totem",
        "description": "If the recipient is killed by wolves, the wolves become sick and cannot kill the following night.",
        "type": "Harmful",
        "giver": "Wolf Shaman"
    },
    "desperation": {
        "name": "Desperation Totem",
        "description": "If the recipient fails to vote during the day they may die.",
        "type": "Harmful",
        "giver": "Shaman / Crazed Shaman"
    }
}

SHAMAN_TOTEMS: List[str] = [
    'death', 'protection', 'revealing', 'influence', 'impatience', 'pacifism', 'silence', 'desperation'
]

WOLF_SHAMAN_TOTEMS: List[str] = [
    'protection', 'cursed', 'lycanthropy', 'retribution', 'blinding', 'deceit', 'misdirection', 'luck'
]

def normalize_totem_name(name: str) -> str:
    """Normalize incoming totem names to canonical keys."""
    if not name:
        return ""
    n = name.lower().strip()
    n = n.replace('_totem', '').replace('totem', '')
    n = n.replace(' ', '_')
    return n
