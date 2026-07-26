#!/bin/bash
# Stop: не дать закончить сессию с очевидно сломанным деревом.
#
# Что проверяем — только быстрое и детерминированное (вместе ~2 s):
#   * ссылки на ассеты, если трогали фронт;
#   * ruff F, если трогали Python.
#
# Чего НЕ проверяем: `make test` (310 тестов, минуты), визуальные снапшоты
# (нужен поднятый стек), фаззинг (около минуты). Долгое в Stop-хуке означает,
# что хук выключат. Про них напоминаем текстом.
#
# Зацикливания не будет: `stop_hook_active` says, что мы уже один раз
# заблокировали остановку, и второй раз не блокируем.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="$REPO/.venv/bin/python"
RUFF="$REPO/.venv/bin/ruff"

input=$(cat)
[[ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false')" == "true" ]] && exit 0

cd "$REPO" || exit 0
changed=$(git status --porcelain 2>/dev/null | awk '{print $NF}')
[[ -n "$changed" ]] || exit 0

problems=""
notes=""

if printf '%s\n' "$changed" | grep -qE '^(css|js|images|worte)/|\.html$'; then
  if [[ -x "$PY" ]] && ! "$PY" -m pytest tests/frontend/test_asset_links.py -q --no-header -p no:cacheprovider >/dev/null 2>&1; then
    problems+="  • ссылки на ассеты сломаны — uv run pytest tests/frontend/test_asset_links.py"$'\n'
  fi
  notes+="  • визуальные снапшоты: uv run pytest tests/frontend/test_visual.py (нужен make up)"$'\n'
  notes+="  • cache-bust ?v=N в HTML для изменённых css/js"$'\n'
fi

py_changed=$(printf '%s\n' "$changed" | grep -E '^backend/.*\.py$' || true)
if [[ -n "$py_changed" ]]; then
  if [[ -x "$RUFF" ]]; then
    lint=$(printf '%s\n' "$py_changed" | xargs -r "$RUFF" check --select F --output-format concise --quiet 2>/dev/null | grep -v '^warning:' || true)
    [[ -n "$lint" ]] && problems+="  • ruff F:"$'\n'"$(printf '%s\n' "$lint" | sed 's/^/      /')"$'\n'
  fi
  notes+="  • тесты бэкенда: make test (обязательно — правило CLAUDE.md)"$'\n'
  notes+="  • фаззинг API: uv run pytest backend/tests/test_openapi_fuzz.py"$'\n'
fi

if [[ -n "$problems" ]]; then
  jq -nc --arg reason "Дерево оставлять в таком виде нельзя:"$'\n'"$problems"$'\n'"Ещё стоит прогнать:"$'\n'"$notes" \
    '{decision:"block", reason:$reason}'
  exit 0
fi

[[ -n "$notes" ]] && printf 'Правки есть — не забудь:\n%s' "$notes"
exit 0
