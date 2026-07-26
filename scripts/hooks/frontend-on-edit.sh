#!/bin/bash
# PostToolUse: правка фронта → проверяем целостность ссылок на ассеты и
# напоминаем про cache-bust.
#
# Две вещи, которые в этом проекте ломались молча и по многу раз:
#   * ссылка на удалённый/переименованный PNG (ловушка 7 CRITICAL-LINKS) —
#     страница не падает, просто теряет фон;
#   * забытый `?v=N` (ловушка 2) — браузер отдаёт старый CSS, и правка
#     выглядит как «не применилась».
#
# Первое проверяется тестом (0.05 s). Второе автоматически не проверить —
# «нужен ли бамп» зависит от того, поедет ли правка в браузер, — поэтому здесь
# просто показываем текущие версии, чтобы решение принималось со свежими
# цифрами перед глазами, а не по памяти.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="$REPO/.venv/bin/python"

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[[ -n "$file" ]] || exit 0

case "$file" in
  *.html|*.css|*.js) ;;
  *) exit 0 ;;
esac
[[ -x "$PY" ]] || exit 0

# ── ссылки на ассеты ────────────────────────────────────────────────────────
if ! out=$("$PY" -m pytest "$REPO/tests/frontend/test_asset_links.py" -q --no-header -p no:cacheprovider 2>&1); then
  {
    echo "Сломаны ссылки на ассеты (tests/frontend/test_asset_links.py):"
    printf '%s\n' "$out" | grep -E '^E |ссылки в никуда|кисти|имя файла' | head -20
    echo
    echo "Это ловушки 7 и 8 из info/CRITICAL-LINKS.md. Почини до следующего шага."
  } >&2
  exit 2
fi

# ── напоминание про cache-bust ──────────────────────────────────────────────
base=$(basename "$file")
case "$file" in
  *.css|*.js)
    refs=$(grep -rhoE "$base\?v=[0-9]+" "$REPO"/*.html 2>/dev/null | sort -u | tr '\n' ' ')
    if [[ -n "$refs" ]]; then
      jq -nc --arg ctx "Файл $base подключён с версией: $refs — если правка должна доехать до браузера, подними ?v= в HTML (ловушка 2, info/CRITICAL-LINKS.md)." \
        '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$ctx}}'
    fi
    ;;
esac
exit 0
