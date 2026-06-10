from __future__ import annotations

import os
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Phrase, Word, WordTopic

TOPICS_DIR = Path(os.getenv("TOPICS_DIR", "/data/topics"))

LEVEL_RANK = {"A2": 0, "B1": 1, "B2": 2, "C1": 3}
MAX_EXAMPLES = 8


def _topics_dir() -> Path:
    root = Path(__file__).resolve().parents[3]
    local = root / "data" / "topics"
    if local.exists():
        return local
    return TOPICS_DIR


def list_topic_slugs() -> list[str]:
    folder = _topics_dir()
    if not folder.exists():
        return []
    slugs: list[str] = []
    for path in sorted(folder.glob("*.topic.yaml")):
        slugs.append(path.name.replace(".topic.yaml", ""))
    return slugs


def load_topic_pack(slug: str) -> dict | None:
    path = _topics_dir() / f"{slug}.topic.yaml"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return None
    return data


def format_examples(raw_examples: list) -> list[str]:
    out: list[str] = []
    for item in raw_examples or []:
        if isinstance(item, str):
            out.append(item.strip())
            continue
        if isinstance(item, dict):
            de = str(item.get("de", "")).strip()
            ru = str(item.get("ru", "")).strip()
            if de and ru:
                out.append(f"{de} ({ru})")
            elif de:
                out.append(de)
    return out


def example_key(text: str) -> str:
    """Ключ для дедупликации: немецкая часть до « (ru)»."""
    de = text.split(" (", 1)[0].strip().lower()
    return de


def merge_examples(existing: list, incoming: list) -> list[str]:
    """Объединяет примеры без дублей; сохраняет порядок (сначала старые)."""
    seen: set[str] = set()
    merged: list[str] = []
    for item in (existing or []) + (incoming or []):
        text = str(item).strip()
        if not text:
            continue
        key = example_key(text)
        if key in seen:
            continue
        seen.add(key)
        merged.append(text)
        if len(merged) >= MAX_EXAMPLES:
            break
    return merged


def pick_level(current: str, incoming: str) -> str:
    """Берёт более высокий уровень (B2 > B1 > A2)."""
    cur_rank = LEVEL_RANK.get(current.strip(), 1)
    new_rank = LEVEL_RANK.get(incoming.strip(), 1)
    return incoming.strip() if new_rank > cur_rank else current.strip()


def grammar_yaml_to_data(row: dict) -> dict | None:
    """YAML grammar → grammar_data для words.grammar_data."""
    grammar = row.get("grammar")
    if not isinstance(grammar, dict):
        return None

    word_type = str(row.get("word_type", "")).strip()
    status = str(grammar.get("status", "partial")).strip()
    if grammar.get("verified"):
        status = "ok"

    data: dict = {
        "status": status,
        "type": word_type,
        "source": str(grammar.get("source", "topic_pack")).strip(),
    }
    if grammar.get("source_url"):
        data["source_url"] = grammar["source_url"]

    noun = grammar.get("noun")
    if isinstance(noun, dict) and noun.get("declension"):
        data["declension"] = noun["declension"]
        if noun.get("plural"):
            data["plural"] = noun["plural"]

    verb = grammar.get("verb")
    if isinstance(verb, dict):
        data["conjugation"] = verb

    if not data.get("declension") and not data.get("conjugation"):
        return None
    return data


def merge_grammar_data(current: dict | None, incoming: dict | None) -> dict | None:
    """Новая грамматика дополняет пустые поля; не затирает уже заполненное."""
    if not incoming:
        return current
    if not current:
        return incoming

    merged = dict(current)
    for key, value in incoming.items():
        if value is None:
            continue
        if key not in merged or merged[key] in (None, {}, []):
            merged[key] = value
    return merged


def normalize_article(raw) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text or text == "null":
        return None
    return text


def normalize_german_lemma(german: str, article: str | None) -> tuple[str, str | None]:
    """german в БД — лемма без артикля; article отдельно."""
    lemma = german.strip()
    art = normalize_article(article)
    for candidate in ("der", "die", "das"):
        prefix = f"{candidate} "
        if lemma.lower().startswith(prefix):
            if not art:
                art = candidate
            lemma = lemma[len(prefix) :].strip()
            break
    return lemma, art


async def _find_word_by_lemma(session: AsyncSession, german: str) -> Word | None:
    lemma = german.strip()
    result = await session.execute(
        select(Word).where(Word.german.ilike(lemma)).order_by(Word.id.asc())
    )
    return result.scalars().first()


async def ensure_word_topic(session: AsyncSession, word_id: int, topic: str) -> bool:
    """Добавляет связь слово↔тема. True — если связь создана впервые."""
    exists = await session.execute(
        select(WordTopic).where(WordTopic.word_id == word_id, WordTopic.topic == topic)
    )
    if exists.scalar_one_or_none():
        return False
    session.add(WordTopic(word_id=word_id, topic=topic))
    return True


def _apply_word_row(word: Word, row: dict, topic_slug: str, *, is_new: bool) -> bool:
    """Обновляет поля слова из YAML. True — если что-то изменилось."""
    changed = is_new
    german, article = normalize_german_lemma(
        str(row.get("german", word.german)).strip(),
        normalize_article(row.get("article")),
    )

    if word.german != german:
        word.german = german
        changed = True
    if article and word.article != article:
        word.article = article
        changed = True

    word_type = str(row.get("word_type", "")).strip()
    if word_type and word.word_type != word_type:
        word.word_type = word_type
        changed = True

    translation = str(row.get("translation_ru", "")).strip()
    if translation and (is_new or not word.translation_ru.strip()):
        if word.translation_ru != translation:
            word.translation_ru = translation
            changed = True

    level = str(row.get("level", "")).strip()
    if level:
        new_level = pick_level(word.level, level) if not is_new else level
        if word.level != new_level:
            word.level = new_level
            changed = True

    incoming_examples = format_examples(row.get("examples") or [])
    if incoming_examples:
        merged = merge_examples(word.examples or [], incoming_examples)
        if merged != (word.examples or []):
            word.examples = merged
            changed = True

    incoming_grammar = grammar_yaml_to_data(row)
    if incoming_grammar:
        merged_grammar = merge_grammar_data(word.grammar_data, incoming_grammar)
        if merged_grammar != word.grammar_data:
            word.grammar_data = merged_grammar
            changed = True

    if is_new:
        word.source = f"topic_pack:{topic_slug}"

    return changed


_BRACKETS_RE = __import__("re").compile(r"\s*\([^)]*\)|\s*\[[^\]]*\]")


async def fix_word_lemmas(session: AsyncSession) -> int:
    """Приводит german к лемме: без артикля, скобок и LLM-аннотаций."""
    result = await session.execute(select(Word))
    fixed = 0
    for word in result.scalars().all():
        cleaned = _BRACKETS_RE.sub("", word.german).strip(" ,;.:-–—")
        new_german, new_article = normalize_german_lemma(cleaned, word.article)
        if new_german != word.german or new_article != word.article:
            word.german = new_german
            word.article = new_article
            fixed += 1
    if fixed:
        await session.commit()
    return fixed


async def normalize_topic_case(session: AsyncSession) -> int:
    """Приводит topic в word_topics/phrases к lowercase (наследие v1)."""
    changed = 0
    result = await session.execute(select(WordTopic))
    for link in result.scalars().all():
        lower = link.topic.strip().lower()
        if link.topic == lower:
            continue
        dup = await session.execute(
            select(WordTopic).where(
                WordTopic.word_id == link.word_id, WordTopic.topic == lower
            )
        )
        if dup.scalar_one_or_none():
            await session.delete(link)  # lowercase link already exists
        else:
            link.topic = lower
        changed += 1

    result = await session.execute(select(Phrase))
    for phrase in result.scalars().all():
        if phrase.topic and phrase.topic != phrase.topic.strip().lower():
            phrase.topic = phrase.topic.strip().lower()
            changed += 1

    if changed:
        await session.commit()
    return changed


async def dedupe_words_by_german(session: AsyncSession) -> int:
    """Сливает дубликаты с одинаковой леммой (после нормализации артикля)."""
    result = await session.execute(
        select(Word).options(selectinload(Word.topics)).order_by(Word.id.asc())
    )
    words = list(result.scalars().all())
    by_lemma: dict[str, Word] = {}
    removed = 0

    for word in words:
        key = word.german.strip().lower()
        keeper = by_lemma.get(key)
        if not keeper:
            by_lemma[key] = word
            continue

        for link in list(word.topics):
            await ensure_word_topic(session, keeper.id, link.topic)
            await session.delete(link)
        await session.flush()
        await session.delete(word)
        removed += 1

    if removed:
        await session.commit()
    return removed


async def import_topic_pack(session: AsyncSession, slug: str) -> dict:
    pack = load_topic_pack(slug)
    if not pack:
        raise FileNotFoundError(f"Topic pack not found: {slug}")

    lemmas_fixed = await fix_word_lemmas(session)
    deduped = await dedupe_words_by_german(session)

    topic_meta = pack.get("topic") or {}
    topic_slug = str(topic_meta.get("slug", slug)).strip().lower()
    words_added = 0
    words_reused = 0
    words_updated = 0
    topics_linked = 0
    phrases_added = 0

    for row in pack.get("words") or []:
        german_raw = str(row.get("german", "")).strip()
        if not german_raw:
            continue
        german, _article = normalize_german_lemma(
            german_raw,
            normalize_article(row.get("article")),
        )

        word = await _find_word_by_lemma(session, german)
        is_new = word is None
        if is_new:
            word = Word(
                german=german,
                article=_article,
                word_type=str(row.get("word_type", "noun")).strip(),
                translation_ru=str(row.get("translation_ru", "")).strip(),
                level=str(row.get("level", "B1")).strip(),
                examples=[],
                source=f"topic_pack:{topic_slug}",
            )
            session.add(word)
            await session.flush()
            words_added += 1
        else:
            words_reused += 1

        if _apply_word_row(word, row, topic_slug, is_new=is_new):
            if not is_new:
                words_updated += 1

        topics = row.get("topics") or [topic_slug]
        for t in topics:
            t_slug = str(t).strip().lower()
            if t_slug and await ensure_word_topic(session, word.id, t_slug):
                topics_linked += 1

    for cliche in pack.get("cliches") or []:
        text_de = str(cliche.get("text_de", "")).strip()
        if not text_de:
            continue
        essay_part = str(cliche.get("essay_part", "")).strip()
        level = str(cliche.get("level", "B1")).strip()

        exists = await session.execute(
            select(Phrase).where(
                Phrase.topic == topic_slug,
                Phrase.text_de == text_de,
                Phrase.essay_part == essay_part,
            )
        )
        if exists.scalar_one_or_none():
            continue

        session.add(
            Phrase(
                text_de=text_de,
                translation_ru=str(cliche.get("translation_ru", "")).strip(),
                essay_part=essay_part,
                topic=topic_slug,
                level=level,
            )
        )
        phrases_added += 1

    await session.commit()
    return {
        "slug": topic_slug,
        "lemmas_fixed": lemmas_fixed,
        "deduped": deduped,
        "words_added": words_added,
        "words_reused": words_reused,
        "words_updated": words_updated,
        "topics_linked": topics_linked,
        "phrases_added": phrases_added,
        # обратная совместимость для старых логов
        "words_linked": topics_linked,
    }


async def get_topic_meta(session: AsyncSession, slug: str) -> dict | None:
    pack = load_topic_pack(slug)
    if not pack:
        return None

    topic = pack.get("topic") or {}
    topic_slug = str(topic.get("slug", slug)).strip().lower()

    stmt = (
        select(Word)
        .join(WordTopic)
        .where(WordTopic.topic == topic_slug)
        .options(selectinload(Word.topics))
    )
    result = await session.execute(stmt)
    words = list(result.scalars().unique().all())

    level_counts: dict[str, int] = {}
    for word in words:
        level_counts[word.level] = level_counts.get(word.level, 0) + 1

    return {
        "slug": topic_slug,
        "title_de": str(topic.get("title_de", topic_slug)),
        "title_ru": str(topic.get("title_ru", "")),
        "level_default": str(topic.get("level_default", "B1")),
        "essay_type_hints": list(topic.get("essay_type_hints") or []),
        "notes_ru": str(topic.get("notes_ru", "")).strip(),
        "word_count": len(words),
        "level_counts": level_counts,
        "phrase_count": len(pack.get("cliches") or []),
    }
