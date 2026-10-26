from __future__ import annotations
import json
import sys
import os
import hashlib
import glob
import pathlib


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


def choose_quiz(folder: str) -> str | None:
    quizes = glob.glob(f'{folder}/*.json')

    if not quizes:
        print(f'Brak quizów. Umieść plik JSON z pytaniami w folderze {folder}')
        return None

    for i, q in enumerate(quizes):
        print(f"{i}. {os.path.basename(q)}")

    while True:
        try:
            quiz_num = int(input("\nWybierz quiz: ").strip())
            if 0 <= quiz_num < len(quizes):
                return quizes[quiz_num]
        except Exception:
            print('niepoprawny wybór')


def hash_answers(questions: list, use_salt: bool = False, answer_key: str = 'answer') -> None:
    # Hashujemy każdą odpowiedź; opcjonalnie dodajemy sól (numer pytania)
    for i, q in enumerate(questions, 1):
        answer = str(q[answer_key]).upper()
        if use_salt:
            answer = answer + str(i)
        q[answer_key] = hashlib.sha256(answer.encode('utf-8')).hexdigest()


def main() -> None:
    file_name = choose_quiz('quizes')
    quiz = load_questions(file_name)

    salt_choice = input("\nCzy dodać sól do hashowania? (t/n): ").strip().lower()
    use_salt = salt_choice == 't'

    hash_answers(quiz['questions'], use_salt=use_salt)

    suffix = '_hashed_salt' if use_salt else '_hashed'
    new_file = file_name.replace('.json', '') + suffix + '.json'
    with open(new_file, 'w', encoding='utf-8') as f:
        json.dump(quiz, f, indent=4, ensure_ascii=False)

    print(f'Zahashowany quiz zapisany do: {new_file}')


if __name__ == "__main__":
    main()
