from __future__ import annotations
from numpy.random import choice as np_choice

def choice(choices, weights=None):
    """
    Selects a random choice from a list of choices based on given weights.
    
    :param choices: List of choices to select from.
    :param weights: List of weights corresponding to each choice. If None, all choices are equally likely.
    :return: A randomly selected choice from the list, based on weighting if provided.
    """
    if weights is None:
        weights = [1/len(choices)] * len(choices)

    # Add a None choice with weight 0 to force np_choice to retain original types
    # and not convert to numpy types
    if None not in choices:
        choices.append(None)
        weights.append(0)

    return np_choice(choices, p=weights)