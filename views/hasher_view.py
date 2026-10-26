"""Widok hashowania quizów (HasherView).

Umożliwia wybór quizu z pliku JSON i zahashowanie poprawnych odpowiedzi
z solą (numerem pytania) do nowego pliku z dopiskiem '_hashed'.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import customtkinter as ctk


class HasherView(ctk.CTkFrame):
    """Widok hashowania odpowiedzi w quizach."""

    def __init__(self, master, controller=None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller

        # Ścieżka do katalogu z quizami
        self.quizes_dir = Path(__file__).resolve().parent.parent / "quizes"

        # Stan wybranego quizu
        self.selected_quiz_path: Path | None = None
        self.selected_path_var = ctk.StringVar(value="")
        self.last_hashed_path: Path | None = None

        self._build_ui()
        self.load_quizes()

    def _build_ui(self) -> None:
        """Tworzy interfejs użytkownika dla widoku Hashera."""
        # --- Nagłówek ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Hasher Quizów 🔒",
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

        desc_label = ctk.CTkLabel(
            self,
            text=(
                "Wybierz quiz z listy, aby zahashować poprawne odpowiedzi algorytmem SHA-256 z solą (numer pytania).\n"
                "Wynik zostanie wyeksportowany do nowego pliku z dopiskiem '_hashed.json'."
            ),
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="left",
        )
        desc_label.pack(anchor="w", padx=20, pady=(0, 10))

        # --- Główny kontener z listą quizów do wyboru ---
        self.scrollable_list = ctk.CTkScrollableFrame(
            self,
            label_text="Wybierz quiz do zahashowania",
            label_font=ctk.CTkFont(size=14, weight="bold"),
            height=260,
        )
        self.scrollable_list.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # --- Panel podglądu wybranego pliku i akcji hashowania ---
        self.action_card = ctk.CTkFrame(self, corner_radius=12)
        self.action_card.pack(fill="x", padx=20, pady=(0, 15))

        self.selected_info_label = ctk.CTkLabel(
            self.action_card,
            text="Wybierz quiz z powyższej listy...",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.selected_info_label.pack(fill="x", padx=20, pady=(15, 5))

        self.target_file_label = ctk.CTkLabel(
            self.action_card,
            text="Plik docelowy: nie wybrano",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self.target_file_label.pack(fill="x", padx=20, pady=(0, 10))

        # Komunikat o statusie/wyniku hashowania
        self.status_label = ctk.CTkLabel(
            self.action_card,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 10))

        # Przyciski akcji
        btn_box = ctk.CTkFrame(self.action_card, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 15))

        self.hash_btn = ctk.CTkButton(
            btn_box,
            text="🔒 Zahashuj odpowiedzi i eksportuj",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            command=self._on_hash_clicked,
            state="disabled",
        )
        self.hash_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.play_hashed_btn = ctk.CTkButton(
            btn_box,
            text="▶ Rozwiąż ten quiz",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=170,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self._on_play_hashed_clicked,
        )
        # Początkowo ukryty, pojawia się po udanym hashowaniu
        self.play_hashed_btn.pack_forget()

    def load_quizes(self) -> None:
        """Wczytuje listę plików quizów z folderu 'quizes' i wyświetla je w liście wyboru."""
        for widget in self.scrollable_list.winfo_children():
            widget.destroy()

        if not self.quizes_dir.exists():
            self.quizes_dir.mkdir(parents=True, exist_ok=True)

        quiz_files = sorted(
            self.quizes_dir.glob("*.json"),
            key=lambda p: p.name.lower()
        )

        if not quiz_files:
            empty_lbl = ctk.CTkLabel(
                self.scrollable_list,
                text="Brak plików quizów w folderze 'quizes'.",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            )
            empty_lbl.pack(pady=30)
            return

        for q_path in quiz_files:
            self._create_quiz_option_item(q_path)

        # Jeśli poprzednio wybrany plik wciąż istnieje, zachowaj wybór, inaczej zresetuj
        if self.selected_quiz_path and self.selected_quiz_path.exists():
            self._select_quiz(self.selected_quiz_path)
        else:
            # Automatycznie zaznacz pierwszy niehashowany quiz (lub pierwszy na liście)
            unhashed = self._find_first_unhashed(quiz_files)
            target = unhashed if unhashed else quiz_files[0]
            self._select_quiz(target)

    def _find_first_unhashed(self, quiz_files: list[Path]) -> Path | None:
        """Znajduje pierwszy plik z odpowiedziami jawnymi (niezahashowanymi)."""
        for p in quiz_files:
            if not self._is_quiz_hashed(p):
                return p
        return None

    def _is_quiz_hashed(self, path: Path) -> bool:
        """Sprawdza, czy odpowiedzi w quizie są już zahashowane SHA-256."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            questions = data.get("questions", [])
            if questions:
                ans = str(questions[0].get("answer", "")).strip()
                # SHA-256 ma dokładnie 64 znaki hex
                return len(ans) == 64 and all(c in "0123456789abcdefABCDEF" for c in ans)
        except Exception:
            pass
        return False

    def _create_quiz_option_item(self, quiz_path: Path) -> None:
        """Tworzy wiersz wyboru dla pojedynczego quizu."""
        is_hashed = self._is_quiz_hashed(quiz_path)

        # Odczytanie tytułu
        title = quiz_path.stem
        q_count = 0
        try:
            with open(quiz_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title", title)
                q_count = len(data.get("questions", []))
        except Exception:
            pass

        card = ctk.CTkFrame(self.scrollable_list, corner_radius=8)
        card.pack(fill="x", padx=10, pady=4)

        # Radiobutton do wyboru
        rb = ctk.CTkRadioButton(
            card,
            text="",
            variable=self.selected_path_var,
            value=str(quiz_path),
            command=lambda p=quiz_path: self._select_quiz(p),
            width=24,
        )
        rb.pack(side="left", padx=(15, 5), pady=10)

        # Informacje o quizie
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=8)

        title_lbl = ctk.CTkLabel(
            info_frame,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        title_lbl.pack(fill="x")

        details_lbl = ctk.CTkLabel(
            info_frame,
            text=f"Plik: {quiz_path.name}  •  Pytań: {q_count}",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        details_lbl.pack(fill="x")

        # Etykieta statusu
        badge_text = "🔒 Już zahashowany" if is_hashed else "🟢 Niezahashowany (zalecany)"
        badge_color = "gray" if is_hashed else "#2ecc71"

        badge_lbl = ctk.CTkLabel(
            card,
            text=badge_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=badge_color,
        )
        badge_lbl.pack(side="right", padx=15, pady=10)

        # Umożliwienie kliknięcia w cały wiersz
        for widget in (card, info_frame, title_lbl, details_lbl, badge_lbl):
            widget.bind("<Button-1>", lambda event, p=quiz_path: self._select_quiz(p))

    def _select_quiz(self, quiz_path: Path) -> None:
        """Ustawia wskazany quiz jako wybrany i aktualizuje panel akcji."""
        self.selected_quiz_path = quiz_path
        self.selected_path_var.set(str(quiz_path))

        is_hashed = self._is_quiz_hashed(quiz_path)
        dest_filename = f"{quiz_path.stem}_hashed.json"

        title = quiz_path.stem
        q_count = 0
        try:
            with open(quiz_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title", title)
                q_count = len(data.get("questions", []))
        except Exception:
            pass

        status_text = " (uwaga: ten quiz zawiera już zahashowane odpowiedzi)" if is_hashed else " (gotowy do hashowania)"

        self.selected_info_label.configure(
            text=f"Wybrany quiz: {title} ({q_count} pytań){status_text}"
        )
        self.target_file_label.configure(
            text=f"Plik źródłowy: {quiz_path.name}   ➔   Plik docelowy: {dest_filename}"
        )

        self.hash_btn.configure(
            state="normal",
            text=f"🔒 Zahashuj odpowiedzi i zapisz jako {dest_filename}",
        )
        self.status_label.configure(text="")
        self.play_hashed_btn.pack_forget()

    def _on_hash_clicked(self) -> None:
        """Przeprowadza hashowanie odpowiedzi z solą i zapisuje plik z dopiskiem '_hashed'."""
        if not self.selected_quiz_path or not self.selected_quiz_path.exists():
            self.status_label.configure(
                text="⚠ Proszę wybrać plik quizu z listy!",
                text_color="#e74c3c",
            )
            return

        try:
            with open(self.selected_quiz_path, "r", encoding="utf-8") as f:
                quiz_data = json.load(f)

            questions = quiz_data.get("questions", [])
            if not questions:
                self.status_label.configure(
                    text="⚠ Plik nie zawiera żadnych pytań do zahashowania.",
                    text_color="#e74c3c",
                )
                return

            # Kopia słownika do modyfikacji
            new_quiz_data = copy.deepcopy(quiz_data)

            # Schemat hashowania na wzór quiz_hasher.py:
            # sha256((litera + numer pytania))
            for i, q in enumerate(new_quiz_data.get("questions", []), 1):
                raw_ans = str(q.get("answer", "")).strip().upper()
                salt = str(i)
                hashed_ans = hashlib.sha256((raw_ans + salt).encode("utf-8")).hexdigest()
                q["answer"] = hashed_ans

            # Zapis do pliku o tej samej nazwie z dopiskiem '_hashed'
            new_filename = f"{self.selected_quiz_path.stem}_hashed.json"
            target_path = self.selected_quiz_path.parent / new_filename

            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(new_quiz_data, f, indent=4, ensure_ascii=False)

            self.last_hashed_path = target_path

            # Informacja o sukcesie
            self.status_label.configure(
                text=f"✓ Sukces! Zahashowano {len(questions)} pytań i zapisano do:\n{new_filename}",
                text_color="#2ecc71",
            )

            # Pokazanie przycisku szybkiego przejścia do gry
            self.play_hashed_btn.pack(side="right")

            # Odświeżenie listy w hasherze i w quiz_list_view
            self.load_quizes()
            self._notify_quiz_list_updated()

        except Exception as e:
            self.status_label.configure(
                text=f"✗ Wystąpił błąd podczas hashowania: {e}",
                text_color="#e74c3c",
            )

    def _on_play_hashed_clicked(self) -> None:
        """Przenosi użytkownika bezpośrednio do rozgrywki nowo zahashowanego quizu."""
        if self.last_hashed_path and self.controller:
            if hasattr(self.controller, "show_view"):
                self.controller.show_view("Rozwiąż quiz")
            if hasattr(self.controller, "start_quiz"):
                self.controller.start_quiz(self.last_hashed_path)

    def _notify_quiz_list_updated(self) -> None:
        """Informuje listę quizów w zakładce rozwiązywania o pojawieniu się nowego pliku."""
        if self.controller and hasattr(self.controller, "quiz_list_view"):
            if hasattr(self.controller.quiz_list_view, "load_quizes"):
                self.controller.quiz_list_view.load_quizes()

    def on_show(self) -> None:
        """Wywoływane przy przełączeniu na zakładkę Hashera."""
        self.load_quizes()
