#!/bin/bash
# PreToolUse(Bash): спросить перед командой, которая гасит контейнеры.
#
# Это не паранойя, а записанное правило проекта: воркеры обогащения держат
# состояние в памяти процесса, и один `docker compose restart` убивает их все
# разом, обрывая прогон, который идёт часами. `make up` тоже пересоздаёт
# контейнеры.
#
# Не `deny`, а `ask`: docker в этом проекте нужен постоянно, запретить его
# насовсем — значит сделать хук вредным. Запрос показывает цену действия в тот
# момент, когда решение принимается.
set -uo pipefail

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
[[ -n "$cmd" ]] || exit 0

if printf '%s' "$cmd" | grep -qE '(docker[- ]compose|docker)\s+(compose\s+)?(down|restart|stop|kill|rm)\b|make\s+(down|restart|up|clean)\b'; then
  jq -nc --arg reason \
"Эта команда пересоздаёт или гасит контейнеры.

В контейнере бэкенда живут воркеры обогащения словаря: их состояние — в памяти
процесса, оно нигде не сохраняется, и рестарт обрывает прогон целиком.
Проверить, идёт ли обогащение прямо сейчас:

    curl -s http://localhost:8000/api/vocab/enrich/progress

Если прогон идёт — дождаться. Если нет — можно продолжать." \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$reason}}'
fi
exit 0
