"""Widok listy quizów dostępnych w folderze 'quizes'."""

from __future__ import annotations

import json
from pathlib import Path
import customtkinter as ctk


class QuizListView(ctk.CTkFrame):
    """Widok listy quizów - wczytuje pliki JSON i pozwala wybrać quiz do gry."""

    def __init__(self, master, controller=None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller

        # Ścieżka do katalogu z quizami
        self.quizes_dir = Path(__file__).resolve().parent.parent / "quizes"

        self._build_ui()
        self.load_quizes()

    def _build_ui(self) -> None:
        # Nagłówek widoku
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Wybierz Quiz",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="↻ Odśwież listę",
            width=130,
            command=self.load_quizes,
        )
        refresh_btn.pack(side="right")

        subtitle_label = ctk.CTkLabel(
            self,
            text="Kliknij w wybrany quiz poniżej, aby przejść do rozgrywki:",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        subtitle_label.pack(anchor="w", padx=20, pady=(0, 10))

        # Przewijana lista quizów
        self.scrollable_list = ctk.CTkScrollableFrame(
            self,
            label_text="Dostępne quizy",
            label_font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.scrollable_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def load_quizes(self) -> None:
        """Wczytuje wszystkie pliki .json z folderu 'quizes' i wyświetla je na liście."""
        # Czyszczenie dotychczasowych elementów listy
        for widget in self.scrollable_list.winfo_children():
            widget.destroy()

        if not self.quizes_dir.exists():
            self.quizes_dir.mkdir(parents=True, exist_ok=True)

        quiz_files = sorted(
            self.quizes_dir.glob("*.json"),
            key=lambda p: p.name.lower()
        )

        if not quiz_files:
            empty_label = ctk.CTkLabel(
                self.scrollable_list,
                text="Brak plików quizów w folderze 'quizes'.\nDodaj pliki .json, aby móc je rozwiązać.",
                font=ctk.CTkFont(size=15),
                text_color="gray",
            )
            empty_label.pack(pady=40)
            return

        for quiz_path in quiz_files:
            self._create_quiz_item(quiz_path)

    def _create_quiz_item(self, quiz_path: Path) -> None:
        """Tworzy pojedynczy element (kartę) quizu na liście."""
        # Wczytanie metadanych z pliku JSON
        quiz_title = quiz_path.stem
        questions_count = None

        try:
            with open(quiz_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                quiz_title = data.get("title", quiz_title)
                if "questions" in data and isinstance(data["questions"], list):
                    questions_count = len(data["questions"])
        except Exception:
            pass

        # Ramka (karta) dla danego quizu
        card = ctk.CTkFrame(self.scrollable_list, corner_radius=10)
        card.pack(fill="x", padx=10, pady=6)

        # Informacje po lewej stronie
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)

        title_label = ctk.CTkLabel(
            info_frame,
            text=quiz_title,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        title_label.pack(fill="x")

        details_text = f"Plik: {quiz_path.name}"
        if questions_count is not None:
            details_text += f"   •   Liczba pytań: {questions_count}"

        details_label = ctk.CTkLabel(
            info_frame,
            text=details_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        details_label.pack(fill="x", pady=(2, 0))

        # Przycisk wyboru po prawej stronie
        select_btn = ctk.CTkButton(
            card,
            text="Wybierz ▶",
            width=100,
            command=lambda p=quiz_path: self._on_quiz_selected(p),
        )
        select_btn.pack(side="right", padx=15, pady=10)

        # Kliknięcie w etykiety również wybiera quiz
        title_label.bind("<Button-1>", lambda event, p=quiz_path: self._on_quiz_selected(p))
        details_label.bind("<Button-1>", lambda event, p=quiz_path: self._on_quiz_selected(p))

    def _on_quiz_selected(self, quiz_path: Path) -> None:
        """Obsługuje kliknięcie w dany quiz i przenosi do widoku rozgrywki."""
        if self.controller and hasattr(self.controller, "start_quiz"):
            self.controller.start_quiz(quiz_path)

    def on_show(self) -> None:
        """Metoda wywoływana przy przełączeniu na ten widok - odświeża listę."""
        self.load_quizes()
