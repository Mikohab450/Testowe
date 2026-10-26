"""Główny punkt wejściowy aplikacji QuizMaker.

Zarządza oknem głównym oraz nawigacją wysokopoziomową między widokami.
"""

from __future__ import annotations

import json
from pathlib import Path
import customtkinter as ctk

from views import HasherView, QuizListView, QuizPlayView


class QuizMakerApp(ctk.CTk):
    """Główna klasa aplikacji QuizMaker oparta na CustomTkinter."""

    TAB_SOLVE = "Rozwiąż quiz"
    TAB_HASHER = "Hasher quizów"

    def __init__(self):
        super().__init__()

        # Konfiguracja okna głównego
        self.title("QuizMaker")
        self.geometry("780x620")
        self.minsize(640, 480)

        # Słownik do przechowywania instancji widoków
        self.views: dict[str, ctk.CTkFrame] = {}

        # Inicjalizacja komponentów i nawigacji
        self._init_ui()

    def _init_ui(self) -> None:
        """Inicjalizuje główny interfejs aplikacji oraz zakładki."""
        # Główny kontener zakładek (Tabview)
        self.tabview = ctk.CTkTabview(
            master=self,
            command=self._on_tab_changed,
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Dodanie zakładek
        tab_solve = self.tabview.add(self.TAB_SOLVE)
        tab_hasher = self.tabview.add(self.TAB_HASHER)

        # Inicjalizacja widoków w zakładce rozwiązywania quizów
        self.quiz_list_view = QuizListView(master=tab_solve, controller=self)
        self.quiz_play_view = QuizPlayView(master=tab_solve, controller=self)

        # Inicjalizacja widoku w zakładce hashowania
        self.hasher_view = HasherView(master=tab_hasher, controller=self)

        # Rejestracja widoków w słowniku
        self.views = {
            "quiz_list": self.quiz_list_view,
            "quiz_play": self.quiz_play_view,
            self.TAB_SOLVE: self.quiz_list_view,
            "Roziwąż quiz": self.quiz_list_view,
            self.TAB_HASHER: self.hasher_view,
        }

        # Domyślnie w zakładce "Rozwiąż quiz" uruchamia się jako pierwszy widok listy quizów
        self.quiz_list_view.pack(fill="both", expand=True)

        # Widok hasher w swojej zakładce
        self.hasher_view.pack(fill="both", expand=True)

        # Upewniamy się, że po włączeniu aplikacji aktywna jest zakładka z listą quizów
        self.tabview.set(self.TAB_SOLVE)

    def _on_tab_changed(self) -> None:
        """Obsługuje zdarzenie przełączenia zakładki."""
        current_tab = self.tabview.get()
        if current_tab in (self.TAB_SOLVE, "Roziwąż quiz"):
            # Jeśli wracamy do zakładki quizów, upewnijmy się, że widok ma aktualne dane
            if self.quiz_list_view.winfo_ismapped():
                self.quiz_list_view.on_show()
        elif current_tab == self.TAB_HASHER:
            if hasattr(self.hasher_view, "on_show"):
                self.hasher_view.on_show()

    def start_quiz(self, quiz_source: str | Path | dict) -> None:
        """Przenosi użytkownika z listy quizów do widoku rozgrywki.

        Args:
            quiz_source: Ścieżka do pliku JSON lub słownik z danymi quizu.
        """
        if isinstance(quiz_source, dict):
            self.quiz_play_view.start_quiz(quiz_data=quiz_source)
        else:
            path = Path(quiz_source)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    quiz_data = json.load(f)
                self.quiz_play_view.start_quiz(quiz_data=quiz_data, quiz_path=path)
            except Exception as e:
                print(f"Błąd podczas wczytywania quizu: {e}")
                self.quiz_play_view.set_quiz(path)

        self.quiz_list_view.pack_forget()
        self.quiz_play_view.pack(fill="both", expand=True)

    def show_quiz_list(self) -> None:
        """Powraca z widoku rozgrywki do widoku listy quizów."""
        self.quiz_play_view.pack_forget()
        self.quiz_list_view.pack(fill="both", expand=True)
        self.quiz_list_view.load_quizes()

    def show_view(self, view_name: str) -> None:
        """Wysokopoziomowa metoda do zmiany aktywnego widoku/zakładki."""
        normalized_name = self.TAB_SOLVE if view_name in (self.TAB_SOLVE, "Roziwąż quiz", "quiz_list") else view_name

        if normalized_name == self.TAB_SOLVE:
            self.tabview.set(self.TAB_SOLVE)
            self.show_quiz_list()
        elif normalized_name == "quiz_play":
            self.tabview.set(self.TAB_SOLVE)
            self.quiz_list_view.pack_forget()
            self.quiz_play_view.pack(fill="both", expand=True)
        elif normalized_name == self.TAB_HASHER:
            self.tabview.set(self.TAB_HASHER)
            self._on_tab_changed()
        else:
            raise ValueError(f"Nieznany widok: {view_name}")

    def get_view(self, view_name: str) -> ctk.CTkFrame | None:
        """Zwraca instancję wskazanego widoku."""
        return self.views.get(view_name)


def main():
    # Ustawienie domyślnego motywu CustomTkinter
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = QuizMakerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
