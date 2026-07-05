from __future__ import annotations

import asyncio
import json
import logging
import re
import time

import httpx

from app.config import settings
from app.pipeline.mistral_http import post_mistral_json


logger = logging.getLogger(__name__)


PART_ORDER = ["einleitung", "argument1", "argument2", "schluss"]
PART_LABELS = {
    "einleitung": "Einleitung",
    "argument1": "Argument Eins",
    "argument2": "Argument Zwei",
    "schluss": "Schluss",
}


def _build_part_prompt(
    *,
    part_key: str,
    part_label: str,
    text: str,
    essay_type: str,
    level: str,
    previous_points: list[str],
) -> str:
    previous_points_json = json.dumps(previous_points[:8], ensure_ascii=False)
    return (
        "Ты — строгий и доброжелательный преподаватель немецкого языка.\n"
        "Проверь только один фрагмент эссе и верни только JSON (без markdown).\n"
        f"Часть эссе: {part_label} ({part_key})\n"
        f"Тип эссе: {essay_type}\n"
        f"Уровень ученика: {level}\n"
        "Категории ошибок: grammar|style|weak|vocabulary.\n"
        "Серьезность: critical|medium|suggestion.\n"
        "Верни объект с полями part_score(0..100), part_feedback_ru, errors[].\n"
        "Каждый элемент errors содержит:\n"
        "start, end, excerpt, type, severity, annotation_kind, explanation_ru, correction, corrected_sentence_de, rule,\n"
        "annotation_kind: critical|style|b2_potential|good_fragment|suggestion.\n"
        "what_wrong_ru, why_bad_ru, how_to_fix_ru,\n"
        "b1_variant_de, b2_variant_de, b1_explain_ru, b2_explain_ru, study_phrases_de[].\n"
        "excerpt — точный проблемный фрагмент из текста (обязательно).\n"
        "correction — ОБЯЗАТЕЛЬНО: исправленная версия ИМЕННО этого excerpt (тот же кусок, но верно).\n"
        "  Для good_fragment (удачное место) correction = сам excerpt.\n"
        "corrected_sentence_de — ОБЯЗАТЕЛЬНО: всё предложение (из текста), где находится excerpt,\n"
        "  переписанное грамматически верно, сохраняя мысль автора. Готовая корректная версия целиком,\n"
        "  а не только исправленный кусок. Для good_fragment — само предложение без изменений.\n"
        "what_wrong_ru — объясни, почему НЕВЕРНО именно в этой конструкции/предложении, а не общее правило.\n"
        "Требования к explanation_ru:\n"
        "Пиши в 3 строках с префиксами:\n"
        "Что не так: ...\n"
        "Почему: ...\n"
        "Как исправить: ...\n"
        "Очень важно:\n"
        "1) Не давай сухие грамматические термины без практического смысла.\n"
        "2) Фокус на намерении студента: объясни, что он хотел сказать и как выразить это лучше.\n"
        "3) how_to_fix_ru делай полезным и практичным: минимум 2 коротких стратегии улучшения.\n"
        "4) b1_variant_de и b2_variant_de должны передавать исходную мысль автора, а не менять позицию.\n"
        "5) study_phrases_de: 1..3 короткие конструкции (полезные выражения), которые можно добавить в словарь.\n"
        "6) Если correction и b2_variant_de совпадают, correction можно оставить пустым.\n"
        "7) Если ошибка minor/suggestion, давай короткий комментарий и короткий совет без длинных объяснений.\n"
        "8) Не повторяй уже выданные ранее замечания, если смысл совпадает.\n"
        "9) how_to_fix_ru должен учитывать текущую часть эссе и не дублировать советы, данные выше.\n"
        "10) Возвращай только реальные ошибки; количество зависит от текста и может быть 0..8.\n"
        "11) excerpt — дословная подстрока из текста (3..80 символов), иначе такую ошибку не добавляй.\n"
        "12) Ищи грамматику, артикли, порядок слов, слабые связки, повторы и неточный словарь.\n"
        "13) Если явных ошибок нет, верни errors: [].\n"
        "14) Для каждой найденной ошибки заполняй what_wrong_ru и how_to_fix_ru.\n"
        "15) КРИТИЧНО: excerpt должен быть МИНИМАЛЬНЫМ — ровно проблемное слово или короткая фраза (обычно 1..4 слова).\n"
        "16) КРИТИЧНО: фрагменты НЕ должны пересекаться и НЕ должны вкладываться друг в друга.\n"
        "    Не возвращай длинную версию того же места и короткую отдельно — выбери один минимальный фрагмент.\n"
        "    Пример НЕПРАВИЛЬНО: 'von dumme', затем 'von dumme Möglichkeiten', затем 'voll der Varianten: von dumme'.\n"
        "    Пример ПРАВИЛЬНО: одна ошибка на 'von dumme' (или на 'dumme'), и всё.\n"
        "17) Каждое проблемное место в тексте — ровно одна ошибка. Не дроби одно место на несколько строк.\n"
        f"Уже выданные смысловые замечания (не повторять): {previous_points_json}\n"
        "start/end должны быть валидными индексами внутри этого фрагмента.\n"
        f"Текст фрагмента:\n{text}\n"
    )


def _build_final_prompt(*, essay_type: str, level: str, blocks: dict[str, str], part_reports: list[dict]) -> str:
    blocks_json = json.dumps(
        [
            {"part": key, "label": PART_LABELS[key], "text": blocks.get(key, "")}
            for key in PART_ORDER
        ],
        ensure_ascii=False,
    )
    reports_json = json.dumps(part_reports, ensure_ascii=False)
    return (
        "Ты оцениваешь общее качество структуры немецкого эссе.\n"
        "Верни только JSON с полями:\n"
        "structure_feedback_ru, topic_feedback_ru, strengths_ru[], next_steps_ru[], overall_comment_ru.\n"
        "Пиши коротко, конкретно, по делу и дружелюбно.\n"
        "Если блок пустой — явно укажи, что эта часть не написана.\n"
        f"Тип эссе: {essay_type}\n"
        f"Уровень ученика: {level}\n"
        f"Части эссе JSON: {blocks_json}\n"
        f"Результаты анализа частей JSON: {reports_json}\n"
    )


def _extract_parts(text: str) -> dict[str, str]:
    text = text or ""
    labels = list(PART_LABELS.values())
    pattern = "|".join(re.escape(label) for label in labels)
    regex = re.compile(rf"(?P<label>{pattern}):\n", re.MULTILINE)
    matches = list(regex.finditer(text))

    if not matches:
        return {"einleitung": text.strip(), "argument1": "", "argument2": "", "schluss": ""}

    result = {key: "" for key in PART_ORDER}
    label_to_key = {v: k for k, v in PART_LABELS.items()}

    for idx, match in enumerate(matches):
        label = match.group("label")
        key = label_to_key.get(label)
        if not key:
            continue
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        result[key] = text[start:end].strip()
    return result


def _fallback_part_analysis(part_key: str, part_text: str) -> dict:
    if not part_text.strip():
        return {
            "part": part_key,
            "part_score": 0,
            "part_feedback_ru": "Часть пустая: текст не написан.",
            "errors": [],
        }

    score = 70 if len(part_text.strip()) > 40 else 55
    return {
        "part": part_key,
        "part_score": score,
        "part_feedback_ru": "Нужно доработать формулировки и связность.",
        "errors": [
            {
                "start": 0,
                "end": min(12, max(0, len(part_text))),
                "excerpt": part_text[:12] if part_text else "",
                "type": "style",
                "severity": "suggestion",
                "annotation_kind": "suggestion",
                "explanation_ru": "Что не так: Формулировка пока общая.\nПочему: Мысль звучит слишком абстрактно.\nКак исправить: Добавьте точный пример и связку.",
                "correction": "",
                "rule": "",
                "what_wrong_ru": "Фраза звучит слишком общей.",
                "why_bad_ru": "Читателю сложно понять, какую именно мысль вы хотите доказать.",
                "how_to_fix_ru": "1) Уточните тезис через конкретный пример. 2) Добавьте причинно-следственную связку.",
                "b1_variant_de": "Ich meine, dass dieses Thema wichtig ist, weil es unser Leben beeinflusst.",
                "b2_variant_de": "Meines Erachtens ist dieses Thema zentral, da es unseren Alltag direkt praegt.",
                "b1_explain_ru": "Простой и понятный вариант с базовой причинной связкой.",
                "b2_explain_ru": "Более академичный вариант с формальной лексикой.",
                "study_phrases_de": ["Ich meine, dass ...", "Meines Erachtens ...", "weil es ... beeinflusst"],
            }
        ],
    }


def _fallback_final_summary() -> dict:
    return {
        "structure_feedback_ru": "Структура эссе заметна, но переходы между частями можно сделать мягче.",
        "topic_feedback_ru": "Тема затронута, но раскрытие пока поверхностное.",
        "strengths_ru": ["Есть попытка сформулировать позицию.", "Используются базовые связки."],
        "next_steps_ru": [
            "Добавьте 1-2 конкретных примера в аргументах.",
            "Сформулируйте более точный итог в Schluss.",
        ],
        "overall_comment_ru": "Хорошая база, следующая цель — точность и глубина аргументации.",
    }


def _ensure_part_markers(all_errors: list[dict], parts: dict[str, str]) -> list[dict]:
    """Если модель не вернула errors — ставим fallback-маркеры по непустым частям."""
    if all_errors:
        return all_errors
    markers: list[dict] = []
    for key in PART_ORDER:
        part_text = parts.get(key, "")
        if not part_text.strip():
            continue
        fb = _fallback_part_analysis(key, part_text)["errors"]
        markers.extend(_normalize_error_ranges(fb, part_text, key))
    return markers


def _fallback_analysis(parts: dict[str, str]) -> dict:
    part_reports = []
    all_errors: list[dict] = []
    total = 0

    for key in PART_ORDER:
        part_text = parts.get(key, "")
        report = _fallback_part_analysis(key, part_text)
        total += report["part_score"]
        normalized = _normalize_error_ranges(report["errors"], part_text, key)
        all_errors.extend(normalized)
        part_reports.append(
            {
                "part": key,
                "label": PART_LABELS[key],
                "score": report["part_score"],
                "feedback_ru": report["part_feedback_ru"],
                "errors_count": len(normalized),
                "is_empty": not part_text.strip(),
            }
        )

    filled_scores = [r["score"] for r in part_reports if not r["is_empty"]]
    avg_score = int(sum(filled_scores) / max(1, len(filled_scores))) if filled_scores else 0
    if avg_score >= 85:
        grade = "A"
    elif avg_score >= 70:
        grade = "B"
    elif avg_score >= 55:
        grade = "C"
    else:
        grade = "D"

    return {
        "overall_score": avg_score,
        "grade": grade,
        "errors": _ensure_part_markers(all_errors, parts),
        "part_reports": part_reports,
        "final_summary": _fallback_final_summary(),
        "model": settings.mistral_model,
    }


def _infer_annotation_kind(err: dict) -> str:
    explicit = str(err.get("annotation_kind", "")).strip().lower()
    allowed = {"critical", "style", "b2_potential", "good_fragment", "suggestion"}
    if explicit in allowed:
        return explicit

    severity = str(err.get("severity", "")).lower()
    err_type = str(err.get("type", "")).lower()
    if severity == "suggestion":
        return "suggestion"
    if err_type in {"good", "strength"}:
        return "good_fragment"
    if err_type == "grammar" or severity == "critical":
        return "critical"
    if err_type == "vocabulary" and str(err.get("b2_variant_de", "")).strip():
        return "b2_potential"
    if err_type in {"style", "weak"}:
        return "style"
    return "style"


def _normalize_error_ranges(errors: list[dict], text: str, part_key: str) -> list[dict]:
    max_len = len(text)
    normalized: list[dict] = []

    def resolve_range(start: int, end: int, excerpt: str) -> tuple[int, int]:
        clipped_start = max(0, min(start, max_len))
        clipped_end = max(clipped_start, min(end, max_len))
        if not excerpt.strip():
            return clipped_start, clipped_end

        current = text[clipped_start:clipped_end].strip()
        excerpt_norm = excerpt.strip()
        if current == excerpt_norm:
            return clipped_start, clipped_end

        first_idx = text.find(excerpt_norm)
        if first_idx < 0:
            return clipped_start, clipped_end

        # If multiple matches exist, choose the one nearest to model-provided start.
        nearest = first_idx
        search_pos = first_idx + 1
        while True:
            next_idx = text.find(excerpt_norm, search_pos)
            if next_idx < 0:
                break
            if abs(next_idx - clipped_start) < abs(nearest - clipped_start):
                nearest = next_idx
            search_pos = next_idx + 1
        end_pos = nearest + len(excerpt_norm)
        if end_pos <= nearest and max_len > 0:
            end_pos = min(max_len, nearest + 1)
        return nearest, end_pos

    for err in errors:
        start_raw = int(err.get("start", 0))
        end_raw = int(err.get("end", start_raw))
        excerpt = str(err.get("excerpt", "")).strip()
        start, end = resolve_range(start_raw, end_raw, excerpt)
        if end <= start and max_len > 0:
            end = min(max_len, start + 1)
        normalized.append(
            {
                "part": part_key,
                "excerpt": excerpt,
                "start": start,
                "end": end,
                "type": str(err.get("type", "grammar")),
                "severity": str(err.get("severity", "medium")),
                "annotation_kind": _infer_annotation_kind(err),
                "explanation_ru": str(err.get("explanation_ru", "Нужна доработка фрагмента.")),
                "correction": str(err.get("correction", "")),
                "corrected_sentence_de": str(err.get("corrected_sentence_de", "")),
                "rule": str(err.get("rule", "Общее правило")),
                "what_wrong_ru": str(err.get("what_wrong_ru", "")),
                "why_bad_ru": str(err.get("why_bad_ru", "")),
                "how_to_fix_ru": str(err.get("how_to_fix_ru", "")),
                "b1_variant_de": str(err.get("b1_variant_de", "")),
                "b2_variant_de": str(err.get("b2_variant_de", "")),
                "b1_explain_ru": str(err.get("b1_explain_ru", "")),
                "b2_explain_ru": str(err.get("b2_explain_ru", "")),
                "study_phrases_de": list(err.get("study_phrases_de", []))[:3],
            }
        )
    return normalized


def _text_key(value: str) -> str:
    raw = value.strip().lower()
    cleaned = re.sub(r"\s+", " ", raw)
    return cleaned


def _dedupe_errors_part(errors: list[dict]) -> list[dict]:
    """Дедуп только внутри одной части по excerpt+диапазону."""
    seen: set[str] = set()
    unique: list[dict] = []
    for idx, err in enumerate(errors):
        excerpt = _text_key(str(err.get("excerpt", "")))
        start = int(err.get("start", 0))
        end = int(err.get("end", start))
        what = _text_key(str(err.get("what_wrong_ru", "")))
        if excerpt:
            key = f"{excerpt}|{start}|{end}"
        else:
            key = f"{idx}|{what}|{start}|{end}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(err)
    return unique


_SEVERITY_RANK = {"critical": 0, "medium": 1, "suggestion": 2}


def _remove_overlapping_errors(errors: list[dict]) -> list[dict]:
    """Убрать пересекающиеся/вложенные диапазоны — источник «пазл»-эффекта.

    Mistral иногда возвращает одно и то же место несколькими фрагментами
    растущей длины ('von dumme' ⊂ 'von dumme Möglichkeiten' ⊂ …). Для карты
    подчёркиваний в тексте диапазоны обязаны быть непересекающимися. Сортируем
    по (важность, короче — раньше) и жадно оставляем те, что не задевают уже
    принятые.
    """
    def sort_key(err: dict) -> tuple[int, int]:
        rank = _SEVERITY_RANK.get(str(err.get("severity", "medium")).lower(), 1)
        span = int(err.get("end", 0)) - int(err.get("start", 0))
        return (rank, span)

    kept: list[dict] = []
    for err in sorted(errors, key=sort_key):
        start = int(err.get("start", 0))
        end = int(err.get("end", start))
        overlaps = any(
            start < int(k.get("end", 0)) and int(k.get("start", 0)) < end
            for k in kept
        )
        if not overlaps:
            kept.append(err)
    kept.sort(key=lambda e: int(e.get("start", 0)))
    return kept


async def _chat_json(client: httpx.AsyncClient, prompt: str) -> dict:
    headers = {
        "Authorization": f"Bearer {settings.mistral_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.mistral_model,
        "messages": [
            {"role": "system", "content": "Return only valid JSON. No markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    response = await client.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


def _grade_from_scores(scores: list[int]) -> tuple[int, str]:
    overall_score = int(sum(scores) / max(1, len(scores))) if scores else 0
    overall_score = max(0, min(100, overall_score))
    if overall_score >= 85:
        grade = "A"
    elif overall_score >= 70:
        grade = "B"
    elif overall_score >= 55:
        grade = "C"
    else:
        grade = "D"
    return overall_score, grade


def _error_has_anchor(err: dict, part_text: str) -> bool:
    excerpt = str(err.get("excerpt", "")).strip()
    if excerpt and excerpt in part_text:
        return True
    start = int(err.get("start", 0))
    end = int(err.get("end", start))
    if end > start and end <= len(part_text):
        return bool(part_text[start:end].strip())
    return False


async def _analyze_single_part(
    client: httpx.AsyncClient,
    *,
    part_key: str,
    part_text: str,
    essay_type: str,
    level: str,
    previous_points: list[str],
) -> dict:
    if not part_text.strip():
        return {
            "part": part_key,
            "score": 0,
            "feedback_ru": "Часть пустая: текст не написан.",
            "errors": [],
            "is_empty": True,
        }

    part_prompt = _build_part_prompt(
        part_key=part_key,
        part_label=PART_LABELS[part_key],
        text=part_text,
        essay_type=essay_type,
        level=level,
        previous_points=previous_points,
    )
    parsed_part = await _chat_json(client, part_prompt)

    part_score = max(0, min(100, int(parsed_part.get("part_score", 60))))
    part_feedback = str(
        parsed_part.get(
            "part_feedback_ru",
            "Нужно улучшить точность формулировок и связность.",
        )
    )
    errors_raw = parsed_part.get("errors", [])
    if not isinstance(errors_raw, list):
        errors_raw = []

    if errors_raw:
        normalized_errors = _normalize_error_ranges(errors_raw, part_text, part_key)
        anchored = [err for err in normalized_errors if _error_has_anchor(err, part_text)]
        if anchored:
            normalized_errors = anchored
    else:
        normalized_errors = []

    deduped_errors = _dedupe_errors_part(normalized_errors)

    return {
        "part": part_key,
        "score": part_score,
        "feedback_ru": part_feedback,
        "errors": deduped_errors,
        "is_empty": False,
    }


def _call_mistral(prompt_text: str, *, label: str) -> dict:
    """Single Mistral chat call for essay analysis.

    Delegates to the shared `post_mistral_json` helper so essay analysis gets
    the same retry / 429-cooldown behaviour as the enrichment pipeline (they
    used to diverge — see info/known-debt.md). Logs timing and the failure so a
    bad key / rate-limit / deprecated model shows up in the logs instead of
    silently degrading to canned fallback feedback.
    """
    started = time.monotonic()
    logger.info("Mistral analyze call [%s] · model=%s", label, settings.mistral_model)
    try:
        parsed = post_mistral_json(
            [
                {"role": "system", "content": "Return only valid JSON. No markdown."},
                {"role": "user", "content": prompt_text},
            ],
            settings.mistral_api_key,
            settings.mistral_model,
            temperature=0.2,
        )
    except Exception:
        logger.exception(
            "Mistral analyze call [%s] failed after %.1fs",
            label,
            time.monotonic() - started,
        )
        raise
    logger.info(
        "Mistral analyze call [%s] ok in %.1fs", label, time.monotonic() - started
    )
    return parsed


async def iter_analyze_events(
    *, text: str, essay_type: str, level: str, only_part: str | None = None
):
    """Генератор событий анализа: part_start, part_done, done.

    only_part: если задан — проверяем только одну часть эссе («Teil analysieren»),
    без итоговой сводки по структуре.
    """
    parts = _extract_parts(text)
    if only_part and only_part not in PART_ORDER:
        only_part = None
    order = [only_part] if only_part else PART_ORDER

    if not settings.mistral_api_key:
        logger.warning(
            "MISTRAL_API_KEY is empty — returning canned fallback analysis "
            "(no real AI check will run)"
        )
        result = _fallback_analysis(parts)
        if only_part:
            result["errors"] = [e for e in result["errors"] if e.get("part") == only_part]
            result["part_reports"] = [
                r for r in result["part_reports"] if r.get("part") == only_part
            ]
            result["final_summary"] = None
        yield {"type": "done", "only_part": only_part, **result}
        return

    logger.info(
        "Essay analysis start · type=%s level=%s only_part=%s parts_filled=%s",
        essay_type,
        level,
        only_part or "all",
        [k for k in PART_ORDER if parts.get(k, "").strip()],
    )
    part_reports: list[dict] = []
    all_errors: list[dict] = []
    final_summary: dict | None = None
    previous_points: list[str] = []

    try:
        for part_key in order:
            part_text = parts.get(part_key, "")
            yield {
                "type": "part_start",
                "part": part_key,
                "label": PART_LABELS[part_key],
            }

            # Empty part → no Mistral call (saves a slow round-trip and stops
            # the model inventing errors for text that isn't there).
            if not part_text.strip():
                report = {
                    "part": part_key,
                    "label": PART_LABELS[part_key],
                    "score": 0,
                    "feedback_ru": "Часть пустая: текст не написан.",
                    "errors_count": 0,
                    "is_empty": True,
                }
                part_reports.append(report)
                yield {
                    "type": "part_done",
                    "part": part_key,
                    "label": PART_LABELS[part_key],
                    "score": 0,
                    "feedback_ru": report["feedback_ru"],
                    "errors": [],
                    "errors_count": 0,
                    "all_errors": list(all_errors),
                    "part_reports": list(part_reports),
                }
                continue

            try:
                part_prompt = _build_part_prompt(
                    part_key=part_key,
                    part_label=PART_LABELS[part_key],
                    text=part_text,
                    essay_type=essay_type,
                    level=level,
                    previous_points=previous_points,
                )
                parsed_part = await asyncio.to_thread(
                    _call_mistral, part_prompt, label=part_key
                )
                errors_raw = parsed_part.get("errors", [])
                if not isinstance(errors_raw, list):
                    errors_raw = []
                normalized_errors = _normalize_error_ranges(errors_raw, part_text, part_key)
                anchored = [err for err in normalized_errors if _error_has_anchor(err, part_text)]
                if anchored:
                    normalized_errors = anchored
                part_result = {
                    "part": part_key,
                    "score": max(0, min(100, int(parsed_part.get("part_score", 60)))),
                    "feedback_ru": str(
                        parsed_part.get(
                            "part_feedback_ru",
                            "Нужно улучшить точность формулировок и связность.",
                        )
                    ),
                    "errors": _remove_overlapping_errors(
                        _dedupe_errors_part(normalized_errors)
                    ),
                    "is_empty": not part_text.strip(),
                }
            except Exception:
                logger.exception("Part analysis failed [%s] — using per-part fallback", part_key)
                part_result = {
                    "part": part_key,
                    "score": 60 if part_text.strip() else 0,
                    "feedback_ru": (
                        "Не удалось проверить эту часть из-за ошибки сервиса."
                        if part_text.strip()
                        else "Часть пустая: текст не написан."
                    ),
                    "errors": [],
                    "is_empty": not part_text.strip(),
                }

            part_errors = part_result["errors"]
            all_errors.extend(part_errors)
            for err in part_errors:
                point = str(err.get("what_wrong_ru", "")).strip()
                if point:
                    previous_points.append(point)

            report = {
                "part": part_key,
                "label": PART_LABELS[part_key],
                "score": part_result["score"],
                "feedback_ru": part_result["feedback_ru"],
                "errors_count": len(part_errors),
                "is_empty": part_result["is_empty"],
            }
            part_reports.append(report)

            yield {
                "type": "part_done",
                "part": part_key,
                "label": PART_LABELS[part_key],
                "score": part_result["score"],
                "feedback_ru": part_result["feedback_ru"],
                "errors": part_errors,
                "errors_count": len(part_errors),
                "all_errors": list(all_errors),
                "part_reports": list(part_reports),
            }

        if not only_part:
            try:
                final_prompt = _build_final_prompt(
                    essay_type=essay_type,
                    level=level,
                    blocks=parts,
                    part_reports=part_reports,
                )
                final_parsed = await asyncio.to_thread(
                    _call_mistral, final_prompt, label="final_summary"
                )
                final_summary = {
                    "structure_feedback_ru": str(
                        final_parsed.get(
                            "structure_feedback_ru",
                            "Структура частично выдержана, улучшите связки между блоками.",
                        )
                    ),
                    "topic_feedback_ru": str(
                        final_parsed.get(
                            "topic_feedback_ru",
                            "Тема обозначена, но раскрыта неравномерно.",
                        )
                    ),
                    "strengths_ru": list(final_parsed.get("strengths_ru", []))[:4],
                    "next_steps_ru": list(final_parsed.get("next_steps_ru", []))[:4],
                    "overall_comment_ru": str(
                        final_parsed.get(
                            "overall_comment_ru",
                            "Продолжайте: уже есть основа, нужно добавить точности и примеров.",
                        )
                    ),
                }
            except Exception:
                logger.exception("Final-summary analysis failed — using fallback summary")
                final_summary = _fallback_final_summary()
    except Exception:
        logger.exception("Essay analysis aborted — returning full fallback analysis")
        result = _fallback_analysis(parts)
        yield {"type": "done", **result}
        return

    scores = [int(report.get("score", 0)) for report in part_reports if not report.get("is_empty")]
    overall_score, grade = _grade_from_scores(scores)

    logger.info(
        "Essay analysis done · grade=%s score=%d errors=%d",
        grade,
        overall_score,
        len(all_errors),
    )
    yield {
        "type": "done",
        "only_part": only_part,
        "overall_score": overall_score,
        "grade": grade,
        "errors": all_errors,
        "part_reports": part_reports,
        "final_summary": None if only_part else (final_summary or _fallback_final_summary()),
        "model": settings.mistral_model,
    }


async def analyze_essay(*, text: str, essay_type: str, level: str) -> dict:
    final: dict | None = None
    async for event in iter_analyze_events(text=text, essay_type=essay_type, level=level):
        if event.get("type") == "done":
            final = {k: v for k, v in event.items() if k != "type"}
    if final:
        return final
    return _fallback_analysis(_extract_parts(text))
