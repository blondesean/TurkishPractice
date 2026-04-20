import os
import shutil

# Colors (matching main app)
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
MAGENTA = "\033[0;35m"
BLUE = "\033[0;34m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREY = "\033[90m"       # dark grey for filled mastery bars
LIGHT_GREY = "\033[37m"  # light grey for empty bar space
NC = "\033[0m"

# Rotating colors for per-module distinction in charts
MODULE_COLORS = [GREEN, CYAN, YELLOW, MAGENTA, BLUE, RED]

GRAPH_HEIGHT = 10
BAR_CHAR = "\u2588"
BAR_EMPTY = "\u2591"


def _strip_ansi(text):
    """Return the visible length of a string, ignoring ANSI escape codes."""
    import re
    return len(re.sub(r"\033\[[0-9;]*m", "", text))


def _pad(text, width):
    """Pad a string with ANSI codes to a visible width."""
    visible = _strip_ansi(text)
    return text + " " * max(0, width - visible)


def _bucket_average(values, max_slots):
    """Reduce a list of values to fit max_slots by averaging consecutive groups."""
    if len(values) <= max_slots:
        return values
    bucket_size = len(values) / max_slots
    result = []
    i = 0.0
    while i < len(values):
        end = min(i + bucket_size, len(values))
        bucket = values[int(i):int(end)]
        if bucket:
            result.append(sum(bucket) / len(bucket))
        i = end
    return result[:max_slots]


def _render_line_chart(pcts, title_text, color, width, height):
    """Shared line chart renderer with moving-average bucketing."""
    lines = []
    lines.append(f"{BOLD}{title_text}{NC}")

    if not pcts:
        lines.append(f"{DIM}  No session history yet.{NC}")
        for _ in range(height):
            lines.append("")
        return lines

    chart_width = width - 7
    pcts = _bucket_average(pcts, chart_width)

    for row in range(height, -1, -1):
        threshold = row * (100 / height)
        label = f"{int(threshold):>3}%{DIM}|{NC}"
        cells = ""
        for p in pcts:
            if abs(p - threshold) <= (100 / height / 2):
                cells += f"{color}*{NC}"
            elif row == 0:
                cells += f"{DIM}-{NC}"
            else:
                cells += " "
        lines.append(label + cells)

    axis_pad = "     " + f"{DIM}+{NC}"
    lines.append(axis_pad + f"{DIM}{'-' * len(pcts)}{NC}")
    if len(pcts) <= 10:
        nums = "".join(str(i + 1) for i in range(len(pcts)))
    else:
        nums = "1" + " " * (len(pcts) - 2) + str(len(pcts))
    lines.append("      " + f"{DIM}{nums}{NC}")

    return lines


def render_session_accuracy(session_scores, width=38, height=GRAPH_HEIGHT):
    """Render a line chart of this sitting's quiz scores, color-coded by module."""
    lines = []
    lines.append(f"{BOLD}This Session{NC}")

    if not session_scores:
        lines.append(f"{GREY}  No quizzes yet this session.{NC}")
        for _ in range(height):
            lines.append("")
        return lines

    # Assign a color to each module
    modules_seen = []
    for s in session_scores:
        if s["module"] not in modules_seen:
            modules_seen.append(s["module"])
    mod_color = {m: MODULE_COLORS[i % len(MODULE_COLORS)] for i, m in enumerate(modules_seen)}

    pcts = [s["score"] / s["total"] * 100 if s["total"] > 0 else 0 for s in session_scores]
    colors = [mod_color[s["module"]] for s in session_scores]

    chart_width = width - 7
    # Bucket if needed
    if len(pcts) > chart_width:
        bucket_size = len(pcts) / chart_width
        new_pcts = []
        new_colors = []
        i = 0.0
        while i < len(pcts):
            end = min(i + bucket_size, len(pcts))
            bucket_p = pcts[int(i):int(end)]
            bucket_c = colors[int(i):int(end)]
            if bucket_p:
                new_pcts.append(sum(bucket_p) / len(bucket_p))
                new_colors.append(bucket_c[-1])  # use last module color in bucket
            i = end
        pcts = new_pcts[:chart_width]
        colors = new_colors[:chart_width]

    for row in range(height, -1, -1):
        threshold = row * (100 / height)
        label = f"{int(threshold):>3}%{GREY}|{NC}"
        cells = ""
        for j, p in enumerate(pcts):
            if abs(p - threshold) <= (100 / height / 2):
                cells += f"{colors[j]}*{NC}"
            elif row == 0:
                cells += f"{GREY}-{NC}"
            else:
                cells += " "
        lines.append(label + cells)

    axis_pad = "     " + f"{GREY}+{NC}"
    lines.append(axis_pad + f"{GREY}{'-' * len(pcts)}{NC}")
    if len(pcts) <= 10:
        nums = "".join(str(i + 1) for i in range(len(pcts)))
    else:
        nums = "1" + " " * (len(pcts) - 2) + str(len(pcts))
    lines.append("      " + f"{GREY}{nums}{NC}")

    # Legend
    legend_parts = [f"{mod_color[m]}*{NC} {m}" for m in modules_seen]
    lines.append("      " + "  ".join(legend_parts))

    return lines


def render_mastery_change(stats, module, direction, quiz_results, width=None):
    """Render all reviewed words sorted by current mastery (least to most).

    Bar for each word:
      [dark grey = current mastery] [light grey = empty to 100]

    If the word was quizzed this round, the change portion overlays:
      - Green cells at the END of the dark grey = mastery gained
      - Red cells REPLACING dark grey from the right = mastery lost

    Numbers: current mastery (points/100), then change from this round in points.
    Change is stable because mastery = cumulative correct/seen.
    """
    term_width = width or shutil.get_terminal_size((80, 24)).columns - 4
    lines = []
    title = f"{BOLD}Word Mastery (by current accuracy){NC}"
    lines.append(title)

    # Build lookup of what was quizzed this round: {(eng, tur): (times_seen, times_correct)}
    quizzed = {}
    for eng, tur, correct in quiz_results:
        key = (eng, tur)
        if key not in quizzed:
            quizzed[key] = [0, 0]
        quizzed[key][0] += 1
        if correct:
            quizzed[key][1] += 1

    words = []
    for key, w in stats.get("words", {}).items():
        if w["module"] != module:
            continue
        d = w[direction]
        if d["seen"] == 0:
            continue
        current_mastery = d["correct"] / d["seen"]

        # Check if quizzed this round
        q_key = (w["english"], w["turkish"])
        change_pts = None
        if q_key in quizzed:
            round_seen, round_correct = quizzed[q_key]
            old_seen = d["seen"] - round_seen
            old_correct = d["correct"] - round_correct
            if old_seen > 0:
                old_mastery = old_correct / old_seen
                change_pts = round((current_mastery - old_mastery) * 100)
            else:
                # First time seeing this word -- treat whole mastery as new
                change_pts = round(current_mastery * 100)

        if direction == "en_to_tr":
            label = w["english"]
        else:
            label = w["turkish"]
        words.append((current_mastery, d["seen"], label, change_pts))

    if not words:
        lines.append(f"{GREY}  No word data yet.{NC}")
        return lines

    words.sort()  # lowest mastery first

    label_width = min(max(len(w[2]) for w in words), 16)
    bar_width = max(term_width - label_width - 20, 10)

    for mastery, seen, label, change_pts in words:
        short_label = label[:label_width].ljust(label_width)
        mastery_pct = round(mastery * 100)
        total_filled = int(mastery * bar_width)

        if change_pts is not None and change_pts != 0:
            change_cells = max(abs(int((change_pts / 100) * bar_width)), 1)

            if change_pts > 0:
                # Gained: dark grey for old level, green for gain
                grey_cells = max(total_filled - change_cells, 0)
                empty_cells = bar_width - grey_cells - change_cells
                bar = (f"{GREY}{BAR_CHAR * grey_cells}{NC}"
                       f"{GREEN}{BAR_CHAR * change_cells}{NC}"
                       f"{LIGHT_GREY}{BAR_EMPTY * max(empty_cells, 0)}{NC}")
                trend = f"{GREEN}+{change_pts:>3d}{NC}"
            else:
                # Lost: dark grey for current level, red for what was lost
                grey_cells = total_filled
                empty_cells = bar_width - grey_cells - change_cells
                bar = (f"{GREY}{BAR_CHAR * grey_cells}{NC}"
                       f"{RED}{BAR_CHAR * change_cells}{NC}"
                       f"{LIGHT_GREY}{BAR_EMPTY * max(empty_cells, 0)}{NC}")
                trend = f"{RED}{change_pts:>4d}{NC}"
        else:
            # Not quizzed this round or no change
            empty_cells = bar_width - total_filled
            bar = f"{GREY}{BAR_CHAR * total_filled}{NC}{LIGHT_GREY}{BAR_EMPTY * empty_cells}{NC}"
            trend = f"{GREY}    {NC}" if change_pts is None else f"{GREY}  +0{NC}"

        lines.append(f"  {short_label} {bar} {mastery_pct:>3d} {trend}")

    return lines


def render_module_mastery_over_time(session_history, module, width=60, height=GRAPH_HEIGHT):
    """Render a line chart of cumulative module mastery over time with moving averages."""
    sessions = [s for s in session_history if s["module"] == module]
    cum_correct = 0
    cum_total = 0
    pcts = []
    for s in sessions:
        cum_correct += s["score"]
        cum_total += s["total"]
        pcts.append(cum_correct / cum_total * 100 if cum_total > 0 else 0)
    title = f"Module Mastery Over Time ({module})"
    return _render_line_chart(pcts, title, CYAN, width, height)


def render_module_ranking(stats, current_module, quiz_results, width=None):
    """Render all modules ranked by overall mastery, with change shown for the current module."""
    term_width = width or shutil.get_terminal_size((80, 24)).columns - 4
    lines = []
    title = f"{BOLD}All Modules Ranked by Mastery{NC}"
    lines.append(title)

    modules = {}
    for key, w in stats.get("words", {}).items():
        mod = w["module"]
        if mod not in modules:
            modules[mod] = {"seen": 0, "correct": 0}
        for d in ("en_to_tr", "tr_to_en"):
            modules[mod]["seen"] += w[d]["seen"]
            modules[mod]["correct"] += w[d]["correct"]

    if not modules:
        lines.append(f"{GREY}  No data yet.{NC}")
        return lines

    # Compute how many answers this round contributed to the current module
    round_seen = len(quiz_results)
    round_correct = sum(1 for _, _, c in quiz_results if c)

    ranked = []
    for mod, counts in modules.items():
        if counts["seen"] == 0:
            continue
        acc = counts["correct"] / counts["seen"]
        change_pts = None
        if mod == current_module and round_seen > 0:
            old_seen = counts["seen"] - round_seen
            old_correct = counts["correct"] - round_correct
            if old_seen > 0:
                old_acc = old_correct / old_seen
                change_pts = round((acc - old_acc) * 100)
            else:
                change_pts = round(acc * 100)
        ranked.append((acc, counts["seen"], mod, change_pts))

    ranked.sort(reverse=True)  # best first

    label_width = min(max(len(r[2]) for r in ranked), 24)
    bar_width = max(term_width - label_width - 22, 10)

    for rank, (acc, seen, mod, change_pts) in enumerate(ranked, 1):
        short_label = mod[:label_width].ljust(label_width)
        mastery_pct = round(acc * 100)
        total_filled = int(acc * bar_width)

        if change_pts is not None and change_pts != 0:
            change_cells = max(abs(int((change_pts / 100) * bar_width)), 1)
            if change_pts > 0:
                grey_cells = max(total_filled - change_cells, 0)
                empty_cells = bar_width - grey_cells - change_cells
                bar = (f"{GREY}{BAR_CHAR * grey_cells}{NC}"
                       f"{GREEN}{BAR_CHAR * change_cells}{NC}"
                       f"{LIGHT_GREY}{BAR_EMPTY * max(empty_cells, 0)}{NC}")
                trend = f"{GREEN}+{change_pts:>3d}{NC}"
            else:
                grey_cells = total_filled
                empty_cells = bar_width - grey_cells - change_cells
                bar = (f"{GREY}{BAR_CHAR * grey_cells}{NC}"
                       f"{RED}{BAR_CHAR * change_cells}{NC}"
                       f"{LIGHT_GREY}{BAR_EMPTY * max(empty_cells, 0)}{NC}")
                trend = f"{RED}{change_pts:>4d}{NC}"
        else:
            empty_cells = bar_width - total_filled
            bar = f"{GREY}{BAR_CHAR * total_filled}{NC}{LIGHT_GREY}{BAR_EMPTY * empty_cells}{NC}"
            trend = f"{GREY}    {NC}"

        lines.append(f"  {rank:>2}. {short_label} {bar} {mastery_pct:>3d} {trend}")

    return lines


def show_graphs(stats, module, direction, session_scores, quiz_results):
    """Print all four charts stacked vertically."""
    term_width = shutil.get_terminal_size((80, 24)).columns
    chart_width = min(term_width - 4, 60)

    session_history = stats.get("session_history", [])

    print()
    print(f"{CYAN}{BOLD}--- Progress ---{NC}")

    # 1. This sitting's quiz scores (resets when app closes), color-coded by module
    for line in render_session_accuracy(session_scores, width=chart_width):
        print(f"  {line}")
    print()

    # 2. All-time module mastery over time (persisted)
    for line in render_module_mastery_over_time(session_history, module, width=chart_width):
        print(f"  {line}")
    print()

    # 3. Per-word mastery with this round's change
    for line in render_mastery_change(stats, module, direction, quiz_results, width=term_width - 4):
        print(f"  {line}")
    print()

    # 4. All modules ranked
    for line in render_module_ranking(stats, module, quiz_results, width=term_width - 4):
        print(f"  {line}")
    print()
