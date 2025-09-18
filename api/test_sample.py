# test_votes_logic.py
import json
from datetime import datetime
import pytest

# Fonction simplifiée pour compter les votes (isolée, sans Azure)
def count_votes(votes):
    results = {"Oui": 0, "Non": 0}
    for vote in votes:
        choice = vote.get("choice")
        if choice in results:
            results[choice] += 1
    return results

def test_count_votes_simple():
    # votes simulés
    votes = [
        {"email": "a@example.com", "choice": "Oui"},
        {"email": "b@example.com", "choice": "Non"},
        {"email": "c@example.com", "choice": "Oui"}
    ]

    results = count_votes(votes)
    assert results["Oui"] == 2
    assert results["Non"] == 1

def test_count_votes_empty():
    votes = []
    results = count_votes(votes)
    assert results["Oui"] == 0
    assert results["Non"] == 0

def test_count_votes_invalid_choice():
    votes = [
        {"email": "a@example.com", "choice": "Peut-être"},
        {"email": "b@example.com", "choice": "Oui"}
    ]
    results = count_votes(votes)
    assert results["Oui"] == 1
    assert results["Non"] == 0
