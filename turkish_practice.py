import os
import sys
import json
import random
from datetime import datetime

# Enable ANSI colors on Windows
os.system("")

# Colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
DIM = "\033[2m"
NC = "\033[0m"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCAB_DIR = os.path.join(BASE_DIR, "vocab")
STATS_FILE = os.path.join(BASE_DIR, "stats.json")
NUM_QUESTIONS = 5
NUM_CHOICES = 6


# --- Stats ---

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"words": {}, "modules": {}, "sessions": 0}


def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def word_key(module, eng, tur):
    return f"{module}|{eng}|{tur}"


def record_answer(stats, module, eng, tur, direction, correct):
    key = word_key(module, eng, tur)
    if key not in stats["words"]:
        stats["words"][key] = {
            "module": module,
            "english": eng,
            "turkish": tur,
            "en_to_tr": {"seen": 0, "correct": 0},
            "tr_to_en": {"seen": 0, "correct": 0},
            "last_seen": None,
        }
    w = stats["words"][key]
    w[direction]["seen"] += 1
    if correct:
        w[direction]["correct"] += 1
    w["last_seen"] = datetime.now().isoformat()


def record_session(stats, module, direction, score, total):
    if module not in stats["modules"]:
        stats["modules"][module] = {
            "sessions": 0,
            "en_to_tr": {"asked": 0, "correct": 0},
            "tr_to_en": {"asked": 0, "correct": 0},
        }
    m = stats["modules"][module]
    m["sessions"] += 1
    m[direction]["asked"] += total
    m[direction]["correct"] += score
    stats["sessions"] += 1


def get_word_accuracy(stats, module, eng, tur, direction):
    key = word_key(module, eng, tur)
    w = stats["words"].get(key)
    if not w or w[direction]["seen"] == 0:
        return None
    return w[direction]["correct"] / w[direction]["seen"]


def show_session_stats(stats, module, direction, results):
    """Show per-word breakdown after a round. results = [(eng, tur, correct), ...]"""
    print(f"{CYAN}{BOLD}--- Word Breakdown ---{NC}")
    for eng, tur, correct in results:
        acc = get_word_accuracy(stats, module, eng, tur, direction)
        if direction == "en_to_tr":
            word_display = f"{eng} -> {tur}"
        else:
            word_display = f"{tur} -> {eng}"

        mark = f"{GREEN}+{NC}" if correct else f"{RED}x{NC}"
        acc_str = f"{DIM}{acc:.0%} all-time{NC}" if acc is not None else ""
        print(f"  {mark} {word_display}  {acc_str}")
    print()

    # Module-level stats
    m = stats["modules"].get(module)
    if m:
        d = m[direction]
        if d["asked"] > 0:
            pct = d["correct"] / d["asked"]
            print(f"{DIM}Module '{module}' ({direction.replace('_', ' ')}): "
                  f"{d['correct']}/{d['asked']} ({pct:.0%}) over {m['sessions']} sessions{NC}")
            print()


def show_weak_words(stats, module, direction, top_n=5):
    """Show worst-performing words for this module/direction."""
    weak = []
    for key, w in stats["words"].items():
        if w["module"] != module:
            continue
        d = w[direction]
        if d["seen"] < 1:
            continue
        acc = d["correct"] / d["seen"]
        if acc < 1.0:
            weak.append((acc, d["seen"], w["english"], w["turkish"]))

    if not weak:
        return

    weak.sort()  # lowest accuracy first
    weak = weak[:top_n]

    print(f"{YELLOW}{BOLD}Weak spots:{NC}")
    for acc, seen, eng, tur in weak:
        print(f"  {RED}{acc:.0%}{NC} ({seen} seen)  {eng} / {tur}")
    print()


# --- Vocab ---

def load_vocab(filepath):
    pairs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "|" in line:
                eng, tur = line.split("|", 1)
                pairs.append((eng.strip(), tur.strip()))
    return pairs


def module_name(filepath):
    return os.path.basename(filepath).replace(".txt", "")


# --- UI ---

def select_module():
    files = sorted(f for f in os.listdir(VOCAB_DIR) if f.endswith(".txt"))
    if not files:
        print("No vocab files found.")
        sys.exit(1)

    if len(files) == 1:
        name = files[0].replace(".txt", "")
        print(f"{CYAN}Module: {BOLD}{name}{NC}")
        return os.path.join(VOCAB_DIR, files[0])

    print(f"{CYAN}{BOLD}Select a module:{NC}")
    for i, f in enumerate(files):
        name = f.replace(".txt", "")
        print(f"  {BOLD}{i + 1}){NC} {name}")
    print()

    while True:
        try:
            choice = int(input("> "))
            if 1 <= choice <= len(files):
                return os.path.join(VOCAB_DIR, files[choice - 1])
        except (ValueError, EOFError):
            pass
        print(f"Pick a number between 1 and {len(files)}")


def select_direction():
    print()
    print(f"{CYAN}{BOLD}Choose direction:{NC}")
    print(f"  {BOLD}1){NC} English -> Turkish")
    print(f"  {BOLD}2){NC} Turkish -> English")
    print()

    while True:
        try:
            choice = input("> ").strip()
            if choice == "1":
                return "en_to_tr"
            elif choice == "2":
                return "tr_to_en"
        except EOFError:
            sys.exit(0)
        print("Pick 1 or 2")


def run_quiz(vocab, direction, stats, mod_name):
    total = len(vocab)
    q_count = min(NUM_QUESTIONS, total)
    questions = random.sample(range(total), q_count)
    score = 0
    results = []

    print()
    print(f"{CYAN}{BOLD}--- Let's go! {q_count} questions ---{NC}")
    print()

    for q_num, qi in enumerate(questions):
        eng, tur = vocab[qi]

        if direction == "en_to_tr":
            prompt, answer = eng, tur
            all_answers = [pair[1] for pair in vocab]
        else:
            prompt, answer = tur, eng
            all_answers = [pair[0] for pair in vocab]

        # Build choices: correct + 5 wrong
        wrong_pool = [a for a in all_answers if a != answer]
        random.shuffle(wrong_pool)
        choices = [answer] + wrong_pool[: NUM_CHOICES - 1]
        random.shuffle(choices)

        # Display
        print(f"{BOLD}Q{q_num + 1}/{q_count}:{NC} What is {YELLOW}{BOLD}{prompt}{NC} ?")
        print()
        for i, c in enumerate(choices):
            print(f"  {BOLD}{i + 1}){NC} {c}")
        print()

        # Get input
        while True:
            try:
                user_input = input("> ").strip()
                choice = int(user_input)
                if 1 <= choice <= len(choices):
                    break
            except (ValueError, EOFError):
                pass
            print(f"Pick a number between 1 and {len(choices)}")

        picked = choices[choice - 1]
        correct = picked == answer

        if correct:
            print(f"{GREEN}{BOLD}  Correct!{NC}")
            score += 1
        else:
            print(f"{RED}{BOLD}  Wrong!{NC} The answer was: {GREEN}{BOLD}{answer}{NC}")
        print()

        record_answer(stats, mod_name, eng, tur, direction, correct)
        results.append((eng, tur, correct))

    # Results
    print(f"{CYAN}{BOLD}--- Results: {score}/{q_count} ---{NC}")
    if score == q_count:
        print(f"{GREEN}{BOLD}Perfect! Harika!{NC}")
    elif score >= q_count // 2:
        print(f"{YELLOW}{BOLD}Not bad! Keep practicing.{NC}")
    else:
        print(f"{RED}{BOLD}Keep at it! Practice makes perfect.{NC}")
    print()

    record_session(stats, mod_name, direction, score, q_count)
    save_stats(stats)

    show_session_stats(stats, mod_name, direction, results)
    show_weak_words(stats, mod_name, direction)


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"{CYAN}{BOLD}=== Turkish Practice ==={NC}")
    print()

    stats = load_stats()

    while True:
        filepath = select_module()
        vocab = load_vocab(filepath)
        mod = module_name(filepath)
        direction = select_direction()
        run_quiz(vocab, direction, stats, mod)

        print(f"{CYAN}{BOLD}Go again? (y/n){NC}")
        try:
            again = input("> ").strip().lower()
        except EOFError:
            break
        if again != "y":
            print(f"{CYAN}Görüşürüz! (See you!){NC}")
            break
        print()


if __name__ == "__main__":
    main()
