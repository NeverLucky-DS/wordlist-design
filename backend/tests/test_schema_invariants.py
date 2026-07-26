"""Индексы поиска обязаны быть объявлены в моделях, а не только в миграции.

`alembic revision --autogenerate` сравнивает базу с `Base.metadata` и всё, чего
в моделях нет, предлагает УДАЛИТЬ. Замер 2026-07-26 на чистой БД, поднятой
`alembic upgrade head`: `alembic check` выдавал восемь операций удаления, и
среди них три GIN-trgm индекса, на которых стоит весь поиск Wörterbuch. То есть
достаточно было один раз выполнить `make migration` после правки любой модели и
применить результат не глядя — поиск бы молча деградировал до full scan по
92 000 строк, а тесты остались бы зелёными.

Тест дешёвый и намеренно не ходит в Postgres: он стережёт ровно тот шаг, с
которого начинается беда, — исчезновение объявления из модели.
"""
from __future__ import annotations

from app.db.models import AuthSession, GuestSession, User, VocabCard, VocabCardTranslation


def _index_names(model) -> set[str]:
    return {i.name for i in model.__table__.indexes}


def test_search_indexes_are_declared_on_the_model():
    assert {
        "ix_vocab_cards_lemma_trgm",       # немецкая сторона поиска
        "ix_vocab_cards_lemma_ascii_trgm",  # она же без умляутов
        "ix_vocab_cards_zipf",              # тайбрейк по частоте (PLANS I0)
        "ix_vocab_cards_form_kind",         # опускание словоформ
        "ix_vocab_cards_band",              # кисть
    } <= _index_names(VocabCard)

    assert "ix_vocab_card_translations_ru_trgm" in _index_names(VocabCardTranslation)


def test_trigram_indexes_are_gin_on_postgres():
    """Обычный btree по этим колонкам не даст ни `similarity()`, ни LIKE '%x%'."""
    by_name = {i.name: i for i in VocabCard.__table__.indexes}
    for name, column in (
        ("ix_vocab_cards_lemma_trgm", "lemma_norm"),
        ("ix_vocab_cards_lemma_ascii_trgm", "lemma_ascii"),
    ):
        kw = by_name[name].dialect_options["postgresql"]
        assert kw["using"] == "gin", name
        assert kw["ops"] == {column: "gin_trgm_ops"}, name


def test_unique_constraints_match_what_the_migration_created():
    """`unique=True` на колонке — это уникальный ИНДЕКС, а первая миграция
    создала ещё и CONSTRAINT. Пока его нет в модели, автоген предлагает его
    снести, и вместе с ним уходит единственность email и токена сессии."""
    for model, name in (
        (User, "users_email_key"),
        (AuthSession, "auth_sessions_token_hash_key"),
        (GuestSession, "guest_sessions_token_hash_key"),
    ):
        names = {c.name for c in model.__table__.constraints}
        assert name in names, f"{model.__tablename__}: нет {name}"
