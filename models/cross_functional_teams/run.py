"""Small runner for the cross-functional teams model."""

from __future__ import annotations

from pprint import pprint

from model import CrossFunctionalTeamsModel, model_summary


if __name__ == "__main__":
    model = CrossFunctionalTeamsModel(rng=42)
    for _ in range(5):
        model.step()
    pprint(model_summary(model))
