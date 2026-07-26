#!/bin/bash
# Ralph — автономный цикл агента. Оригинал: https://github.com/snarktank/ralph
#
# Чем эта копия отличается от апстрима (каждое отличие намеренное):
#
#  1. Промпт лежит в `ralph-prompt.md`, а НЕ в `CLAUDE.md`. Claude Code
#     подхватывает любой CLAUDE.md как инструкции проекта, когда работает с
#     файлами рядом с ним. Апстримовский CLAUDE.md начинается словами «You are
#     an autonomous coding agent… commit ALL changes» — попади он в обычную
#     сессию, обычная сессия начнёт коммитить всё подряд. Имя другое, чтобы
#     этого не случилось.
#
#  2. Передаём `--settings ralph-settings.json` с deny-правилами. Это
#     единственная НАСТОЯЩАЯ защита: документация Claude Code прямо говорит, что
#     правила применяет сам Claude Code, а не модель, и что инструкции в промпте
#     «shape what Claude tries to do, but they don't change what Claude Code
#     allows». deny переживает --dangerously-skip-permissions.
#
#  3. claude запускается из КОРНЯ репозитория, а не из этой папки, и пути к
#     prd.json/progress.txt переданы явно. В апстриме агент должен был сам
#     догадаться, что «в той же директории, что и этот файл».
#
#  4. Преflight-проверки перед стартом: git-репозиторий, jq, prd.json,
#     чистое рабочее дерево. Цикл коммитит сам — стартовать поверх
#     незакоммиченных правок значит смешать свою работу с его.
#
#  5. Поддержка Amp убрана: amp тут не установлен, а мёртвая ветка в скрипте,
#     который гоняют без присмотра, — это ловушка.
#
# Использование:  ./scripts/ralph/ralph.sh [макс_итераций]
#        пример:  ./scripts/ralph/ralph.sh 10

set -euo pipefail

MAX_ITERATIONS=10
[[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]] && MAX_ITERATIONS="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PROMPT_FILE="$SCRIPT_DIR/ralph-prompt.md"
SETTINGS_FILE="$SCRIPT_DIR/ralph-settings.json"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"

die() { echo "ralph: $1" >&2; exit 1; }

# ---------- preflight ----------
command -v jq     >/dev/null 2>&1 || die "нет jq (brew install jq)"
command -v claude >/dev/null 2>&1 || die "нет claude в PATH"
[ -f "$PROMPT_FILE" ]   || die "нет $PROMPT_FILE"
[ -f "$SETTINGS_FILE" ] || die "нет $SETTINGS_FILE — без deny-правил цикл не запускается"
[ -f "$PRD_FILE" ] || die "нет $PRD_FILE. Сначала: /prd в Claude Code, потом /ralph — он соберёт prd.json"

jq empty "$PRD_FILE" 2>/dev/null || die "$PRD_FILE — не валидный JSON"

cd "$REPO_ROOT"
git rev-parse --git-dir >/dev/null 2>&1 || die "$REPO_ROOT — не git-репозиторий"

if [ -n "$(git status --porcelain)" ]; then
  die "рабочее дерево грязное. Ralph коммитит сам — сначала закоммить или спрячь свои правки (git stash)."
fi

TOTAL=$(jq '[.userStories[]] | length' "$PRD_FILE")
REMAINING=$(jq '[.userStories[] | select(.passes == false)] | length' "$PRD_FILE")
BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE")

[ "$REMAINING" -eq 0 ] && { echo "ralph: в $PRD_FILE не осталось незакрытых историй — делать нечего."; exit 0; }

# ---------- архив прошлого прогона ----------
if [ -f "$LAST_BRANCH_FILE" ]; then
  LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || echo "")
  if [ -n "$BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$BRANCH" != "$LAST_BRANCH" ]; then
    ARCHIVE_FOLDER="$ARCHIVE_DIR/$(date +%Y-%m-%d)-$(echo "$LAST_BRANCH" | sed 's|^ralph/||')"
    echo "ralph: архивирую прошлый прогон ($LAST_BRANCH) → $ARCHIVE_FOLDER"
    mkdir -p "$ARCHIVE_FOLDER"
    [ -f "$PRD_FILE" ]      && cp "$PRD_FILE" "$ARCHIVE_FOLDER/"
    [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    { echo "# Ralph Progress Log"; echo "Started: $(date)"; echo "---"; } > "$PROGRESS_FILE"
  fi
fi
[ -n "$BRANCH" ] && echo "$BRANCH" > "$LAST_BRANCH_FILE"

if [ ! -f "$PROGRESS_FILE" ]; then
  { echo "# Ralph Progress Log"; echo "Started: $(date)"; echo "---"; } > "$PROGRESS_FILE"
fi

# ---------- цикл ----------
cat <<EOF

  Ralph
  репозиторий : $REPO_ROOT
  ветка PRD   : ${BRANCH:-(не задана)}
  истории     : $REMAINING незакрытых из $TOTAL
  итераций    : максимум $MAX_ITERATIONS
  защита      : $SETTINGS_FILE (deny-правила)

  Каждая итерация — свежий claude с ПУСТЫМ контекстом и без запросов
  разрешений. Он будет коммитить сам. Прервать: Ctrl-C.

EOF

for i in $(seq 1 "$MAX_ITERATIONS"); do
  echo ""
  echo "==============================================================="
  echo "  итерация $i из $MAX_ITERATIONS   ($(date +%H:%M:%S))"
  echo "==============================================================="

  OUTPUT=$(claude \
      --dangerously-skip-permissions \
      --settings "$SETTINGS_FILE" \
      --print < "$PROMPT_FILE" 2>&1 | tee /dev/stderr) || true

  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo ""
    echo "ralph: все истории закрыты (итерация $i из $MAX_ITERATIONS)."
    exit 0
  fi

  LEFT=$(jq '[.userStories[] | select(.passes == false)] | length' "$PRD_FILE" 2>/dev/null || echo "?")
  echo "итерация $i закончена. Осталось историй: $LEFT"
  sleep 2
done

echo ""
echo "ralph: упёрся в лимит итераций ($MAX_ITERATIONS), не закрыв всё."
echo "Что сделано — в $PROGRESS_FILE, что осталось — в $PRD_FILE."
exit 1
