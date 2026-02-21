from src.services.activity_service import POINTS, calculate_score
from src.models.schemas import ActivityType


def test_message_points_value():
    assert POINTS[ActivityType.MESSAGE_SENT] == 2


def test_reaction_points_value():
    assert POINTS[ActivityType.REACTION_ADD] == 1


def test_score_single_message():
    # 1 message → stored as 2 → score = 2 / 2.0 = 1.0
    assert calculate_score([2]) == 1.0


def test_score_single_reaction():
    # 1 reaction → stored as 1 → score = 1 / 2.0 = 0.5
    assert calculate_score([1]) == 0.5


def test_score_combined():
    # 3 messages (3×2=6) + 2 reactions (2×1=2) → 8 / 2.0 = 4.0
    assert calculate_score([2, 2, 2, 1, 1]) == 4.0


def test_score_empty():
    assert calculate_score([]) == 0.0
