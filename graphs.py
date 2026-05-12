import os
import shutil

from mastery import compute_mastery

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
    """Reduce a list of values to fit max_slots by averaging consecutive groups.

    None values are skipped within each bucket; a bucket of only Nones stays None.
    """
    if len(values) <= max_slots:
        return list(values)
    bucket_size = len(values) / max_slots
    result = []
    i = 0.0
    while i < len(values):
        end = min(i + bucket_size, len(values))
        bucket = [v for v in values[int(i):int(end)] if v is not None]
        if bucket:
            result.append(sum(bucket) / len(bucket))
        else:
            result.append(None)
        i = end
    return result[:max_slots]


def _render_line_chart(series, title_text, width, height):
    """Render one or more series on shared axes.

    `series` is a list of (pcts, color, marker, legend_label) tuples sharing the
    same x-axis. None values inside a pcts list are treated as missing data
    (no marker drawn). Pass legend_label=None to omit from the legend.
    """
    lines = [f"{BOLD}{title_text}{NC}"]

    if not any(s[0] for s in series):
        lines.append(f"{DIM}  No session history yet.{NC}")
        for _ in range(height + 2):
            lines.append("")
        return lines

    chart_width = width - 7
    bucketed = [(_bucket_average(s[0], chart_width), s[1], s[2], s[3]) for s in series]
    max_cols = max(len(b[0]) for b in bucketed)

    for row in range(height, -1, -1):
        threshold = row * (100 / height)
        label = f"{int(threshold):>3}%{DIM}|{NC}"
        cells = ""
        for col in range(max_cols):
            cell = " " if row > 0 else f"{DIM}-{NC}"
            for pcts, color, marker, _ in bucketed:
                if col >= len(pcts) or pcts[col] is None:
                    continue
                if abs(pcts[col] - threshold) <= (100 / height / 2):
                    cell = f"{color}{marker}{NC}"
            cells += cell
        lines.append(label + cells)

    axis_pad = "     " + f"{DIM}+{NC}"
    lines.append(axis_pad + f"{DIM}{'-' * max_cols}{NC}")
    if max_cols <= 10:
        nums = "".join(str(i + 1) for i in range(max_cols))
    else:
        nums = "1" + " " * (max_cols - 2) + str(max_cols)
    lines.append("      " + f"{DIM}{nums}{NC}")

    legend = [(c, m, l) for _, c, m, l in bucketed if l]
    if legend:
        parts = [f"{c}{m}{NC} {l}" for c, m, l in legend]
        lines.append("      " + "  ".join(parts))

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
        history = d.get("history", [])
        if not history:
            continue
        current_mastery = compute_mastery(history)

        q_key = (w["english"], w["turkish"])
        change_pts = None
        if q_key in quizzed:
            round_seen, _ = quizzed[q_key]
            old_history = history[:-round_seen] if round_seen else history
            old_mastery = compute_mastery(old_history)
            change_pts = round((current_mastery - old_mastery) * 100)

        label = w["english"] if direction == "en_to_tr" else w["turkish"]
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


def render_module_progress_over_time(session_history, module, width=60, height=GRAPH_HEIGHT):
    """Two lines per module across past sessions:

    - Test Accuracy: cumulative correct/asked. Long-run record of how often the
      user got questions right.
    - Mastery: snapshot of module mastery taken when each session was recorded
      (None for sessions logged before snapshots were added).
    """
    sessions = [s for s in session_history if s["module"] == module]
    cum_correct = 0
    cum_total = 0
    acc_pcts = []
    mast_pcts = []
    for s in sessions:
        cum_correct += s["score"]
        cum_total += s["total"]
        acc_pcts.append(cum_correct / cum_total * 100 if cum_total > 0 else 0)
        m = s.get("mastery")
        mast_pcts.append(m * 100 if m is not None else None)
    title = f"Module Progress Over Time ({module})"
    series = [
        (acc_pcts, CYAN, "*", "Test Accuracy"),
        (mast_pcts, YELLOW, "o", "Mastery"),
    ]
    return _render_line_chart(series, title, width, height)


def render_module_ranking(stats, current_module, current_direction, quiz_results, module_index, width=None):
    """Render all modules ranked by average word mastery.

    Mastery is averaged over every (word, direction) pair in the module. Untested
    pairs count as 0, so a module can never exceed (tested_pairs / total_pairs)
    in mastery, even with perfect test results.
    """
    term_width = width or shutil.get_terminal_size((80, 24)).columns - 4
    lines = []
    title = f"{BOLD}All Modules Ranked by Mastery{NC}"
    lines.append(title)

    if not module_index:
        lines.append(f"{GREY}  No modules.{NC}")
        return lines

    # Per-word delta lookup for the active direction this round
    quizzed = {}
    for eng, tur, _ in quiz_results:
        quizzed[(eng, tur)] = quizzed.get((eng, tur), 0) + 1

    words_dict = stats.get("words", {})

    ranked = []
    for mod, mod_words in module_index.items():
        if not mod_words:
            continue
        total_now = 0.0
        total_old = 0.0
        for eng, tur in mod_words:
            w = words_dict.get(f"{mod}|{eng}|{tur}")
            h_en = w["en_to_tr"].get("history", []) if w else []
            h_tr = w["tr_to_en"].get("history", []) if w else []
            m_en = compute_mastery(h_en)
            m_tr = compute_mastery(h_tr)
            total_now += m_en + m_tr

            if mod == current_module:
                round_n = quizzed.get((eng, tur), 0)
                if current_direction == "en_to_tr":
                    old_h = h_en[:-round_n] if round_n else h_en
                    total_old += compute_mastery(old_h) + m_tr
                else:
                    old_h = h_tr[:-round_n] if round_n else h_tr
                    total_old += m_en + compute_mastery(old_h)

        denom = len(mod_words) * 2
        mastery = total_now / denom
        change_pts = None
        if mod == current_module and quizzed:
            old_mastery = total_old / denom
            change_pts = round((mastery - old_mastery) * 100)

        # Hide untouched modules to avoid a wall of 0%s; always show current
        if mastery == 0 and mod != current_module:
            continue
        ranked.append((mastery, len(mod_words), mod, change_pts))

    if not ranked:
        lines.append(f"{GREY}  No data yet.{NC}")
        return lines

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


def show_graphs(stats, module, direction, session_scores, quiz_results, module_index):
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

    # 2. Test accuracy + mastery over time for this module
    for line in render_module_progress_over_time(session_history, module, width=chart_width):
        print(f"  {line}")
    print()

    # 3. Per-word mastery with this round's change
    for line in render_mastery_change(stats, module, direction, quiz_results, width=term_width - 4):
        print(f"  {line}")
    print()

    # 4. All modules ranked by mastery (untested words count as 0%)
    for line in render_module_ranking(stats, module, direction, quiz_results, module_index, width=term_width - 4):
        print(f"  {line}")
    print()
