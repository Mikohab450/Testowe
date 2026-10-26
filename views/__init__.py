"""Pakiet widoków aplikacji QuizMaker."""

from .hasher_view import HasherView
from .quiz_list_view import QuizListView
from .quiz_play_view import QuizPlayView
from .solve_quiz_view import SolveQuizView

__all__ = ["QuizListView", "QuizPlayView", "SolveQuizView", "HasherView"]
