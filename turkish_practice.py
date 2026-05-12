import os
import sys
import json
import csv
import random
from datetime import datetime

from recommenders import ActiveRecommender
from graphs import show_graphs
from mastery import compute_mastery

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
VOCAB_FILE = os.path.join(BASE_DIR, "vocab_turkish.txt")
STATS_FILE = os.path.join(BASE_DIR, "stats.json")
NUM_QUESTIONS = 5
NUM_CHOICES = 6


# --- Stats ---

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            stats = json.load(f)
        _migrate_module_names(stats)
        return stats
    return {"words": {}, "modules": {}, "sessions": 0}


def _migrate_module_names(stats):
    """Normalize module names to title case (e.g. 'animals' -> 'Animals')."""
    # Migrate word entries
    new_words = {}
    for key, w in list(stats.get("words", {}).items()):
        old_mod = w["module"]
        new_mod = old_mod.title()
        if old_mod != new_mod:
            w["module"] = new_mod
            new_key = key.replace(old_mod + "|", new_mod + "|", 1)
            new_words[new_key] = w
        else:
            new_words[key] = w
    stats["words"] = new_words

    # Migrate module-level stats
    new_modules = {}
    for mod, data in list(stats.get("modules", {}).items()):
        new_mod = mod.title()
        if new_mod in new_modules:
            # Merge into existing
            for d in ("en_to_tr", "tr_to_en"):
                new_modules[new_mod][d]["asked"] += data[d]["asked"]
                new_modules[new_mod][d]["correct"] += data[d]["correct"]
            new_modules[new_mod]["sessions"] += data["sessions"]
        else:
            new_modules[new_mod] = data
    stats["modules"] = new_modules

    # Migrate session history
    for s in stats.get("session_history", []):
        s["module"] = s["module"].title()


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
    if "history" not in w[direction]:
        w[direction]["history"] = []
    w[direction]["history"].append(correct)
    w["last_seen"] = datetime.now().isoformat()


def record_session(stats, module, direction, score, total, module_words):
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

    # Snapshot module mastery (mean across all words × both directions) so the
    # progress chart can plot it over time.
    mastery_snapshot = None
    if module_words:
        total_m = 0.0
        for eng, tur in module_words:
            w = stats["words"].get(word_key(module, eng, tur))
            for d in ("en_to_tr", "tr_to_en"):
                h = w[d].get("history", []) if w else []
                total_m += compute_mastery(h)
        mastery_snapshot = total_m / (len(module_words) * 2)

    if "session_history" not in stats:
        stats["session_history"] = []
    stats["session_history"].append({
        "timestamp": datetime.now().isoformat(),
        "module": module,
        "direction": direction,
        "score": score,
        "total": total,
        "mastery": mastery_snapshot,
    })


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
    """Show lowest-mastery words for this module/direction."""
    weak = []
    for key, w in stats["words"].items():
        if w["module"] != module:
            continue
        d = w[direction]
        history = d.get("history", [])
        if not history:
            continue
        mastery = compute_mastery(history)
        if mastery < 1.0:
            weak.append((mastery, d["seen"], w["english"], w["turkish"]))

    if not weak:
        return

    # Lowest mastery first; ties broken by most-seen first
    weak.sort(key=lambda x: (x[0], -x[1]))
    weak = weak[:top_n]

    print(f"{YELLOW}{BOLD}Lowest Mastery:{NC}")
    for mastery, seen, eng, tur in weak:
        print(f"  {RED}{mastery:.0%}{NC} seen {seen} times  {eng} / {tur}")
    print()


# --- Vocab ---

def load_csv():
    """Load vocab_turkish.txt (UTF-16, tab-delimited) and return {category: {subcategory: [(eng, tur), ...]}}."""
    data = {}
    with open(VOCAB_FILE, "r", encoding="utf-16") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # skip header
        for row in reader:
            if len(row) < 4:
                continue
            cat, sub, eng, tur = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
            if cat not in data:
                data[cat] = {}
            if sub not in data[cat]:
                data[cat][sub] = []
            data[cat][sub].append((eng, tur))
    return data


def build_module_index(vocab_data):
    """Return {module_name: [(eng, tur), ...]} using the same naming as select_module."""
    index = {}
    for cat, subs in vocab_data.items():
        if len(subs) == 1 and "Main" in subs:
            index[cat] = subs["Main"]
        else:
            for sub, words in subs.items():
                index[f"{cat}/{sub}"] = words
    return index


# --- UI ---

def pick_from_list(prompt_text, options, labels=None):
    """Show a numbered list and return the chosen item. `labels` overrides display text."""
    display = labels if labels is not None else options
    print(f"{CYAN}{BOLD}{prompt_text}{NC}")
    for i, label in enumerate(display):
        print(f"  {BOLD}{i + 1}){NC} {label}")
    print()

    while True:
        try:
            choice = int(input("> "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except (ValueError, EOFError):
            pass
        print(f"Pick a number between 1 and {len(options)}")


def select_module(vocab_data):
    """Let user pick category then subcategory. Returns (module_name, word_pairs)."""
    categories = sorted(vocab_data.keys())
    cat_labels = [
        f"{c} {DIM}({sum(len(w) for w in vocab_data[c].values())} words){NC}"
        for c in categories
    ]
    category = pick_from_list("Select a category:", categories, cat_labels)

    subcategories = sorted(vocab_data[category].keys())

    if len(subcategories) == 1 and subcategories[0] == "Main":
        # Only "Main" — skip subcategory selection
        mod_name = category
        words = vocab_data[category]["Main"]
    else:
        print()
        sub_labels = [
            f"{s} {DIM}({len(vocab_data[category][s])} words){NC}"
            for s in subcategories
        ]
        subcategory = pick_from_list(
            f"Select a topic in {BOLD}{category}{NC}:", subcategories, sub_labels
        )
        mod_name = f"{category}/{subcategory}"
        words = vocab_data[category][subcategory]

    print(f"{CYAN}Module: {BOLD}{mod_name}{NC} ({len(words)} words)")
    return mod_name, words


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


def select_question_count(max_q):
    default = min(NUM_QUESTIONS, max_q)
    print()
    print(f"{CYAN}{BOLD}How many questions? {DIM}[Enter = {default}, max = {max_q}]{NC}")

    while True:
        try:
            raw = input("> ").strip()
        except EOFError:
            sys.exit(0)
        if raw == "":
            return default
        try:
            n = int(raw)
            if 1 <= n <= max_q:
                return n
        except ValueError:
            pass
        print(f"Pick a number between 1 and {max_q}")


def run_quiz(vocab, direction, stats, mod_name, session_scores, q_count, module_index):
    recommender = ActiveRecommender()
    questions = recommender.select_questions(vocab, stats, mod_name, direction, q_count)
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

    record_session(stats, mod_name, direction, score, q_count, vocab)
    save_stats(stats)

    session_scores.append({"module": mod_name, "direction": direction, "score": score, "total": q_count})

    show_weak_words(stats, mod_name, direction)
    show_graphs(stats, mod_name, direction, session_scores, results, module_index)


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"{CYAN}{BOLD}=== Turkish Practice ==={NC}")
    print()

    stats = load_stats()
    vocab_data = load_csv()
    module_index = build_module_index(vocab_data)
    session_scores = []  # this sitting only, resets when app closes

    mod, vocab, direction, q_count = None, None, None, None
    while True:
        if mod is None:
            mod, vocab = select_module(vocab_data)
            direction = select_direction()
            q_count = select_question_count(len(vocab))
        run_quiz(vocab, direction, stats, mod, session_scores, q_count, module_index)

        print(f"{CYAN}{BOLD}Go again? (y = new, r = retry same, n = quit){NC}")
        try:
            again = input("> ").strip().lower()
        except EOFError:
            break
        if again == "r":
            print()
            continue
        if again != "y":
            print(f"{CYAN}Görüşürüz! (See you!){NC}")
            break
        mod, vocab, direction, q_count = None, None, None, None
        print()


if __name__ == "__main__":
    main()
