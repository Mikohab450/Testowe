"""Widok rozgrywki quizu z obsługą pytań jednokrotnego wyboru i hashowania."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import customtkinter as ctk


class QuizPlayView(ctk.CTkFrame):
    """Widok rozgrywki - odpowiada za prezentację pytań, weryfikację odpowiedzi i wynik."""

    def __init__(self, master, controller=None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller

        # Dane bieżącego quizu
        self.quiz_data: dict | None = None
        self.quiz_path: Path | None = None
        self.questions: list[dict] = []
        self.total_questions: int = 0

        # Stan rozgrywki
        self.current_question_index: int = 0
        self.score: int = 0
        self.has_checked_current: bool = False

        # Zmienna przechowująca wybraną literę (A, B, C, D...)
        self.selected_option_var = ctk.StringVar(value="")

        self._build_ui()

    def _build_ui(self) -> None:
        """Buduje szkielet interfejsu widoku rozgrywki."""
        # Górny pasek z nawigacją i informacjami
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=(15, 10))

        self.back_button = ctk.CTkButton(
            self.top_bar,
            text="← Lista quizów",
            command=self._on_back_clicked,
            width=130,
            height=32,
        )
        self.back_button.pack(side="left")

        self.quiz_title_label = ctk.CTkLabel(
            self.top_bar,
            text="Quiz",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.quiz_title_label.pack(side="left", padx=20)

        self.score_header_label = ctk.CTkLabel(
            self.top_bar,
            text="Punkty: 0",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3498db",
        )
        self.score_header_label.pack(side="right")

        # Pasek postępu
        self.progress_bar = ctk.CTkProgressBar(self, height=10)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.progress_bar.set(0)

        # Kontener główny na pytanie i opcje
        self.card_frame = ctk.CTkFrame(self, corner_radius=12)
        self.card_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Kontener na podsumowanie końcowe (początkowo ukryty)
        self.summary_frame = ctk.CTkFrame(self, corner_radius=12)

        # --- Elementy wewnątrz card_frame ---
        # Numer pytania
        self.q_number_label = ctk.CTkLabel(
            self.card_frame,
            text="Pytanie 1 / 1",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="gray",
        )
        self.q_number_label.pack(anchor="w", padx=25, pady=(20, 5))

        # Treść pytania
        self.question_text_label = ctk.CTkLabel(
            self.card_frame,
            text="Treść pytania...",
            font=ctk.CTkFont(size=18, weight="bold"),
            wraplength=680,
            justify="left",
            anchor="w",
        )
        self.question_text_label.pack(fill="x", padx=25, pady=(5, 15))

        # Kontener na radiobuttony z opcjami odpowiedzi
        self.options_container = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.options_container.pack(fill="both", expand=True, padx=25, pady=5)
        self.radio_buttons: list[ctk.CTkRadioButton] = []

        # Obszar feedbacku (zielony/czerwony napis z informacją o poprawności)
        self.feedback_label = ctk.CTkLabel(
            self.card_frame,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=30,
        )
        self.feedback_label.pack(fill="x", padx=25, pady=(10, 5))

        # Dolny pasek z przyciskiem akcji ("Sprawdź odpowiedź" / "Następne pytanie")
        self.action_button = ctk.CTkButton(
            self.card_frame,
            text="Sprawdź odpowiedź",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            command=self._on_action_button_clicked,
        )
        self.action_button.pack(padx=25, pady=(5, 20), fill="x")

        # --- Elementy wewnątrz summary_frame ---
        self._build_summary_ui()

    def _build_summary_ui(self) -> None:
        """Tworzy elementy ekranu podsumowania końcowego."""
        self.summary_title = ctk.CTkLabel(
            self.summary_frame,
            text="Koniec Quizu! 🎉",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.summary_title.pack(pady=(40, 15))

        self.summary_quiz_name = ctk.CTkLabel(
            self.summary_frame,
            text="Quiz",
            font=ctk.CTkFont(size=18),
            text_color="gray",
        )
        self.summary_quiz_name.pack(pady=5)

        # Wielki napis z wynikiem: X/Y (Z%)
        self.summary_score_label = ctk.CTkLabel(
            self.summary_frame,
            text="Twój wynik: 0/0 (0%)",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#2ecc71",
        )
        self.summary_score_label.pack(pady=25)

        self.summary_feedback_label = ctk.CTkLabel(
            self.summary_frame,
            text="Gratulacje!",
            font=ctk.CTkFont(size=16),
        )
        self.summary_feedback_label.pack(pady=10)

        buttons_box = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        buttons_box.pack(pady=(30, 40))

        self.restart_btn = ctk.CTkButton(
            buttons_box,
            text="↻ Zagraj ponownie",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=42,
            width=180,
            command=self._restart_quiz,
        )
        self.restart_btn.pack(side="left", padx=10)

        self.summary_back_btn = ctk.CTkButton(
            buttons_box,
            text="← Lista quizów",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=42,
            width=180,
            fg_color="gray",
            hover_color="#555555",
            command=self._on_back_clicked,
        )
        self.summary_back_btn.pack(side="left", padx=10)

    def start_quiz(self, quiz_data: dict, quiz_path: str | Path | None = None) -> None:
        """Inicjalizuje rozgrywkę na podstawie przekazanego słownika z danymi quizu."""
        self.quiz_data = quiz_data
        self.quiz_path = Path(quiz_path) if quiz_path else None
        self.questions = quiz_data.get("questions", [])
        self.total_questions = len(self.questions)

        title = quiz_data.get("title", self.quiz_path.stem if self.quiz_path else "Quiz")
        self.quiz_title_label.configure(text=title)
        self.summary_quiz_name.configure(text=title)

        # Reset stanu gry
        self.current_question_index = 0
        self.score = 0
        self.score_header_label.configure(text="Punkty: 0")

        # Pokaż kartę pytania, ukryj podsumowanie
        self.summary_frame.pack_forget()
        self.card_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        if not self.questions:
            self.question_text_label.configure(text="Brak pytań w tym quizie.")
            self.action_button.configure(state="disabled")
            return

        self.action_button.configure(state="normal")
        # Załaduj pierwsze pytanie
        self._load_question(0)

    def load_quiz_data(self, quiz_data: dict, quiz_path: str | Path | None = None) -> None:
        """Alias dla metody start_quiz."""
        self.start_quiz(quiz_data, quiz_path)

    def set_quiz(self, quiz_path: str | Path) -> None:
        """Wczytuje quiz ze ścieżki i uruchamia rozgrywkę."""
        path = Path(quiz_path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.start_quiz(quiz_data=data, quiz_path=path)
        except Exception as e:
            print(f"Błąd podczas wczytywania quizu z pliku {quiz_path}: {e}")

    def _load_question(self, index: int) -> None:
        """Wyświetla pytanie o wskazanym indeksie."""
        self.current_question_index = index
        self.has_checked_current = False
        q = self.questions[index]

        # Aktualizacja nagłówków i paska postępu
        q_num_1_based = index + 1
        self.q_number_label.configure(text=f"Pytanie {q_num_1_based} z {self.total_questions}")
        self.question_text_label.configure(text=q.get("question", ""))
        self.progress_bar.set(index / self.total_questions)

        # Reset feedbacku i wyboru
        self.feedback_label.configure(text="")
        self.selected_option_var.set("")

        # Czyszczenie dotychczasowych radiobuttonów
        for widget in self.options_container.winfo_children():
            widget.destroy()
        self.radio_buttons.clear()

        # Budowa nowych radiobuttonów z opcjami
        options = q.get("options", [])
        for opt_text in options:
            # Odzyskujemy literę opcji (np. 'A' z 'A. Tworzy okno gry' lub litera z indeksu)
            opt_stripped = opt_text.strip()
            letter = opt_stripped[0].upper() if opt_stripped and opt_stripped[0].isalpha() else ""

            rb = ctk.CTkRadioButton(
                self.options_container,
                text=opt_text,
                variable=self.selected_option_var,
                value=letter,
                font=ctk.CTkFont(size=15),
            )
            rb.pack(anchor="w", padx=10, pady=8, fill="x")
            self.radio_buttons.append(rb)

        # Ustawienie przycisku akcji na "Sprawdź odpowiedź"
        self.action_button.configure(
            text="Sprawdź odpowiedź",
            fg_color=("#3B8ED0", "#1F6AA5"),
        )

    def _on_action_button_clicked(self) -> None:
        """Obsługuje kliknięcie przycisku akcji (sprawdzenie lub przejście dalej)."""
        if not self.has_checked_current:
            self._check_answer()
        else:
            self._go_to_next()

    def _check_answer(self) -> None:
        """Weryfikuje wybraną odpowiedź zgodnie z regułami hashowania (z solą = numer pytania)."""
        selected_letter = self.selected_option_var.get().strip().upper()

        if not selected_letter:
            self.feedback_label.configure(
                text="⚠ Proszę zaznaczyć jedną z odpowiedzi!",
                text_color="#f39c12",
            )
            return

        self.has_checked_current = True

        # Zablokowanie zmiany wyboru po sprawdzeniu
        for rb in self.radio_buttons:
            rb.configure(state="disabled")

        # Numer pytania jako sól (1-based, czyli 1, 2, 3...)
        q_num = self.current_question_index + 1
        q = self.questions[self.current_question_index]
        q_answer = q.get("answer", "")
        options = q.get("options", [])

        # Weryfikacja hasha z solą (i ewentualne odzyskanie poprawnej litery A-D)
        is_correct, correct_letter = self._verify_answer(selected_letter, q_answer, q_num, options)

        if is_correct:
            self.score += 1
            self.score_header_label.configure(text=f"Punkty: {self.score}")
            self.feedback_label.configure(
                text="✓ Poprawna odpowiedź! (+1 pkt)",
                text_color="#2ecc71",  # Zielony
            )
        else:
            self.feedback_label.configure(
                text=f"✗ Niepoprawna odpowiedź! Poprawna to: {correct_letter}",
                text_color="#e74c3c",  # Czerwony
            )

        # Zmiana przycisku akcji na przejście do następnego pytania lub wyniku
        if self.current_question_index + 1 < self.total_questions:
            self.action_button.configure(
                text="Następne pytanie ▶",
                fg_color="#2ecc71",
            )
        else:
            self.action_button.configure(
                text="Zobacz wynik końcowy 🏆",
                fg_color="#9b59b6",
            )

    def _verify_answer(
        self, user_letter: str, q_answer: str, question_num: int, options: list[str]
    ) -> tuple[bool, str]:
        """Sprawdza odpowiedź użytkownika i znajduje poprawną literę (A-D).

        Zgodnie z quiz_player.py oraz quiz_hasher.py:
        Sól to numer pytania (str(question_num)).
        """
        user_letter = user_letter.strip().upper()
        target_hash = str(q_answer).strip()
        salt = str(question_num)

        # Pobieramy dostępne litery z opcji (lub domyślnie A-D)
        letters = []
        for opt in options:
            opt_s = opt.strip()
            if opt_s and opt_s[0].isalpha():
                letters.append(opt_s[0].upper())
        if not letters:
            letters = ["A", "B", "C", "D"]

        correct_letter = "?"

        # 1. Główny mechanizm: Hash SHA-256 z solą (numer pytania)
        for letter in letters:
            candidate_hash = hashlib.sha256((letter + salt).encode("utf-8")).hexdigest()
            if candidate_hash == target_hash:
                correct_letter = letter
                break

        # 2. Rezerwa: Hash SHA-256 bez soli
        if correct_letter == "?":
            for letter in letters:
                candidate_hash = hashlib.sha256(letter.encode("utf-8")).hexdigest()
                if candidate_hash == target_hash:
                    correct_letter = letter
                    break

        # 3. Rezerwa: Zwykły tekst (np. plik bez hashowania 'answer': 'B')
        if correct_letter == "?":
            for letter in letters:
                if letter == target_hash.upper():
                    correct_letter = letter
                    break

        if correct_letter == "?":
            correct_letter = target_hash

        is_correct = (user_letter == correct_letter)
        return is_correct, correct_letter

    def _go_to_next(self) -> None:
        """Przechodzi do kolejnego pytania lub kończy quiz."""
        next_index = self.current_question_index + 1
        if next_index < self.total_questions:
            self._load_question(next_index)
        else:
            self._show_summary()

    def _show_summary(self) -> None:
        """Wyświetla ekran końcowy z wynikiem X/Y (Z%)."""
        self.progress_bar.set(1.0)
        self.card_frame.pack_forget()
        self.summary_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        total = self.total_questions
        score = self.score
        percentage = (score / total) * 100 if total > 0 else 0.0

        # Wymagany format: X/Y (Z%)
        score_text = f"Twój wynik: {score}/{total} ({percentage:.1f}%)"
        self.summary_score_label.configure(text=score_text)

        # Kolor i komentarz motywacyjny
        if percentage == 100:
            self.summary_score_label.configure(text_color="#2ecc71")
            self.summary_feedback_label.configure(
                text="Gratulacje! Odpowiedziałeś bezbłędnie! 🏆"
            )
        elif percentage >= 50:
            self.summary_score_label.configure(text_color="#3498db")
            self.summary_feedback_label.configure(
                text="Dobry wynik, ale zawsze może być lepiej! 👍"
            )
        else:
            self.summary_score_label.configure(text_color="#e74c3c")
            self.summary_feedback_label.configure(
                text="Może następnym razem pójdzie lepiej. Warto poćwiczyć! 📚"
            )

    def _restart_quiz(self) -> None:
        """Restartuje bieżący quiz od pierwszego pytania."""
        if self.quiz_data:
            self.start_quiz(self.quiz_data, self.quiz_path)

    def _on_back_clicked(self) -> None:
        """Powraca do widoku listy quizów za pośrednictwem kontrolera."""
        if self.controller and hasattr(self.controller, "show_quiz_list"):
            self.controller.show_quiz_list()
