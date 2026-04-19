#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

VOCAB_DIR="$(dirname "$0")/vocab"
NUM_QUESTIONS=5
NUM_CHOICES=6

# Load a vocab file into parallel arrays
load_vocab() {
    local file="$1"
    ENGLISH=()
    TURKISH=()
    while IFS='|' read -r eng tur; do
        [[ -z "$eng" ]] && continue
        ENGLISH+=("$eng")
        TURKISH+=("$tur")
    done < "$file"
}

# Pick N unique random indices from a range
pick_random_indices() {
    local count=$1
    local max=$2
    local -n result=$3
    result=()
    while (( ${#result[@]} < count )); do
        local r=$(( RANDOM % max ))
        local dup=0
        for existing in "${result[@]}"; do
            [[ "$existing" == "$r" ]] && { dup=1; break; }
        done
        (( dup == 0 )) && result+=("$r")
    done
}

# Shuffle an array in place
shuffle_array() {
    local -n arr=$1
    local i j tmp
    for (( i=${#arr[@]}-1; i>0; i-- )); do
        j=$(( RANDOM % (i+1) ))
        tmp="${arr[$i]}"
        arr[$i]="${arr[$j]}"
        arr[$j]="$tmp"
    done
}

# Select module
select_module() {
    local files=("$VOCAB_DIR"/*.txt)
    if (( ${#files[@]} == 0 )); then
        echo "No vocab files found in $VOCAB_DIR"
        exit 1
    fi

    if (( ${#files[@]} == 1 )); then
        SELECTED_FILE="${files[0]}"
        local name=$(basename "${files[0]}" .txt)
        echo -e "${CYAN}Module: ${BOLD}${name}${NC}"
        return
    fi

    echo -e "${CYAN}${BOLD}Select a module:${NC}"
    for i in "${!files[@]}"; do
        local name=$(basename "${files[$i]}" .txt)
        echo -e "  ${BOLD}$((i+1)))${NC} $name"
    done
    echo ""
    while true; do
        read -rp "> " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#files[@]} )); then
            SELECTED_FILE="${files[$((choice-1))]}"
            return
        fi
        echo "Pick a number between 1 and ${#files[@]}"
    done
}

# Select direction
select_direction() {
    echo ""
    echo -e "${CYAN}${BOLD}Choose direction:${NC}"
    echo -e "  ${BOLD}1)${NC} English -> Turkish"
    echo -e "  ${BOLD}2)${NC} Turkish -> English"
    echo ""
    while true; do
        read -rp "> " choice
        case "$choice" in
            1) DIRECTION="en_to_tr"; return ;;
            2) DIRECTION="tr_to_en"; return ;;
            *) echo "Pick 1 or 2" ;;
        esac
    done
}

# Run the quiz
run_quiz() {
    local total=${#ENGLISH[@]}
    local score=0

    # Pick question indices
    local q_count=$NUM_QUESTIONS
    (( q_count > total )) && q_count=$total
    local question_indices
    pick_random_indices "$q_count" "$total" question_indices

    echo ""
    echo -e "${CYAN}${BOLD}--- Let's go! $q_count questions ---${NC}"
    echo ""

    for q_num in "${!question_indices[@]}"; do
        local qi=${question_indices[$q_num]}

        # Determine prompt and answer based on direction
        if [[ "$DIRECTION" == "en_to_tr" ]]; then
            local prompt="${ENGLISH[$qi]}"
            local answer="${TURKISH[$qi]}"
            local all_answers=("${TURKISH[@]}")
        else
            local prompt="${TURKISH[$qi]}"
            local answer="${ENGLISH[$qi]}"
            local all_answers=("${ENGLISH[@]}")
        fi

        # Build choices: 1 correct + 5 wrong
        local choices=("$answer")
        local wrong_indices
        pick_random_indices $(( NUM_CHOICES - 1 )) "$total" wrong_indices

        for wi in "${wrong_indices[@]}"; do
            local candidate="${all_answers[$wi]}"
            # Skip if it's the same as the answer
            if [[ "$candidate" == "$answer" ]]; then
                # Try to find a replacement
                for (( try=0; try<total; try++ )); do
                    local dup=0
                    for existing in "${choices[@]}"; do
                        [[ "${all_answers[$try]}" == "$existing" ]] && { dup=1; break; }
                    done
                    if (( dup == 0 )); then
                        candidate="${all_answers[$try]}"
                        break
                    fi
                done
            fi
            # Skip duplicates
            local already=0
            for existing in "${choices[@]}"; do
                [[ "$candidate" == "$existing" ]] && { already=1; break; }
            done
            (( already == 0 )) && choices+=("$candidate")
        done

        # Pad if we don't have enough choices
        while (( ${#choices[@]} < NUM_CHOICES )); do
            for (( try=0; try<total; try++ )); do
                local dup=0
                for existing in "${choices[@]}"; do
                    [[ "${all_answers[$try]}" == "$existing" ]] && { dup=1; break; }
                done
                if (( dup == 0 )); then
                    choices+=("${all_answers[$try]}")
                    break
                fi
            done
            # Safety: break if we can't find more unique choices
            (( ${#choices[@]} < NUM_CHOICES )) && break
        done

        shuffle_array choices

        # Find correct answer position
        local correct_pos=-1
        for ci in "${!choices[@]}"; do
            [[ "${choices[$ci]}" == "$answer" ]] && { correct_pos=$ci; break; }
        done

        # Display question
        echo -e "${BOLD}Q$((q_num+1))/${q_count}:${NC} What is ${YELLOW}${BOLD}${prompt}${NC} ?"
        echo ""
        for ci in "${!choices[@]}"; do
            echo -e "  ${BOLD}$((ci+1)))${NC} ${choices[$ci]}"
        done
        echo ""

        # Get answer
        while true; do
            read -rp "> " user_choice
            if [[ "$user_choice" =~ ^[0-9]+$ ]] && (( user_choice >= 1 && user_choice <= ${#choices[@]} )); then
                break
            fi
            echo "Pick a number between 1 and ${#choices[@]}"
        done

        local picked_index=$((user_choice - 1))

        if [[ "${choices[$picked_index]}" == "$answer" ]]; then
            echo -e "${GREEN}${BOLD}  ✓ Correct!${NC}"
            (( score++ ))
        else
            echo -e "${RED}${BOLD}  ✗ Wrong!${NC} The answer was: ${GREEN}${BOLD}${answer}${NC}"
        fi
        echo ""
    done

    # Score
    echo -e "${CYAN}${BOLD}--- Results ---${NC}"
    echo -e "Score: ${BOLD}${score}/${q_count}${NC}"
    if (( score == q_count )); then
        echo -e "${GREEN}${BOLD}Perfect! Harika!${NC}"
    elif (( score >= q_count / 2 )); then
        echo -e "${YELLOW}${BOLD}Not bad! Keep practicing.${NC}"
    else
        echo -e "${RED}${BOLD}Keep at it! Practice makes perfect.${NC}"
    fi
    echo ""
}

# Main
echo -e "${CYAN}${BOLD}=== Turkish Practice ===${NC}"
echo ""
select_module
load_vocab "$SELECTED_FILE"
select_direction
run_quiz
