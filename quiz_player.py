from __future__ import annotations
import json
import sys
import os
import hashlib
import glob
from pathlib import Path
from datetime import datetime


def load_questions(filename: str) -> dict:
    if not os.path.exists(filename):
        print(f"Błąd: Nie znaleziono pliku {filename}.")
        sys.exit(1)

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Błąd: Plik {filename} nie jest poprawnym plikiem JSON.")
        sys.exit(1)
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas wczytywania pliku: {e}")
        sys.exit(1)


def show_summary(results: list) -> None:
    # Wyświetla tabelkę z pytaniami i odpowiedziami ucznia
    print("\n" + "=" * 60)
    print(" PODSUMOWANIE ".center(60, "="))
    print("=" * 60)
    for i, r in enumerate(results, 1):
        status = "✓" if r['correct'] else "✗"
        short_q = r['question'][:45] + "..." if len(r['question']) > 45 else r['question']
        if r['correct']:
            print(f"{i:2}. [{status}] {short_q}")
            print(f"      Twoja odpowiedź: {r['your_answer']}")
        else:
            print(f"{i:2}. [{status}] {short_q}")
            print(f"      Twoja: {r['your_answer']}  |  Poprawna: {r['correct_answer']}")
    print("=" * 60)


def save_results(title: str, results: list, score: int, total: int) -> None:
    # Zapisuje wyniki do pliku JSON z timestampem (symulacja wysyłania do serwera)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        'quiz': title,
        'timestamp': timestamp,
        'score': score,
        'total': total,
        'percentage': round((score / total) * 100, 2) if total > 0 else 0,
        'results': results,
    }
    filename = f"wyniki_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"\nWyniki zapisane do pliku: {filename}")


def run_quiz(quiz_data: dict) -> None:
    title = quiz_data.get('title', 'WITAJ W QUIZIE POWTÓRZENIOWYM!')
    questions = quiz_data.get('questions', [])

    print("=" * 40)
    print(f" {title} ".center(40, "="))
    print("=" * 40, "\n")

    score = 0
    total_questions = len(questions)
    results = []

    for i, q in enumerate(questions, 1):
        print(f"Pytanie {i}/{total_questions}: {q['question']}")

        for option in q.get('options', []):
            print(f"  {option}")

        while True:
            answer = input("\nTwoja odpowiedź (np. A, B, C...): ").strip().upper()
            if answer:
                break
            print("Proszę podać odpowiedź.")

        # Hashujemy odpowiedź z solą (numer pytania)
        hashed_answer = hashlib.sha256((answer + str(i)).encode('utf-8')).hexdigest()

        # Odzyskujemy poprawną literę do wyświetlenia i zapisu wyników
        correct_letter = "?"
        for letter in ['A', 'B', 'C', 'D']:
            if hashlib.sha256((letter + str(i)).encode('utf-8')).hexdigest() == q['answer']:
                correct_letter = letter
                break

        if hashed_answer == q['answer']:
            print("=> Poprawna odpowiedź!\n")
            score += 1
            results.append({
                'question': q['question'],
                'your_answer': answer,
                'correct_answer': correct_letter,
                'correct': True,
            })
        else:
            print(f"=> Niestety, poprawna odpowiedź to: {correct_letter}\n")
            results.append({
                'question': q['question'],
                'your_answer': answer,
                'correct_answer': correct_letter,
                'correct': False,
            })

    print("=" * 40)
    print(" KONIEC QUIZU ".center(40, "="))
    print("=" * 40)

    percentage = (score / total_questions) * 100 if total_questions > 0 else 0
    print(f"\nTwój wynik to: {score} z {total_questions} możliwych punktów ({percentage:.2f}%).")

    if percentage == 100:
        print("Gratulacje! Odpowiedziałeś bezbłędnie!")
    elif percentage >= 50:
        print("Dobry wynik, ale zawsze może być lepiej!")
    else:
        print("Może następnym razem pójdzie lepiej. Warto poćwiczyć!")

    # Podsumowanie i zapis wyników
    show_summary(results)
    save_results(title, results, score, total_questions)


def choose_quiz(folder: str) -> str | None:
    quizes = glob.glob(f'{folder}/*.json')

    if not quizes:
        print(f'Brak quizów. Umieść plik JSON z pytaniami w folderze {folder}')
        return None

    for i, q in enumerate(quizes):
        print(f"{i}. {q.replace(f'{folder}/', '')}")

    while True:
        try:
            answer = int(input("\nWybierz quiz: ").strip())
            if 0 <= answer < len(quizes):
                return quizes[answer]
        except Exception:
            print('niepoprawny wybór')


def main() -> None:
    questions_file = choose_quiz('quizes')
    quiz_data = load_questions(questions_file)

    if not quiz_data or 'questions' not in quiz_data or not quiz_data['questions']:
        print("Brak pytań do wyświetlenia. Plik JSON jest pusty lub ma niepoprawny format.")
        return

    # Opcja ponownego grania po zakończeniu quizu
    while True:
        run_quiz(quiz_data)
        again = input("\nCzy chcesz zagrać jeszcze raz? (t/n): ").strip().lower()
        if again != 't':
            break

    print("Do zobaczenia!")


if __name__ == "__main__":
    main()
