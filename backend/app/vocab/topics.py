"""Topic catalog for B1–C1 vocabulary (~150 themes).

Each word gets 1..N topics attached during enrichment. The catalog mixes
THEMATIC areas (everyday life, society, environment, ...) with a few
NOTIONAL/FUNCTIONAL areas (time, quantity, cause/effect, ...) so that general
and function words (solch-, ander-, jed-, ...) also have a home — those fall
under the `allgemein_funktionswoerter` topic or the relevant functional area.

Structure: AREAS maps a macro-area label (de / ru) to a list of topics.
Each topic = (slug, ru, de). `slug` is ascii snake_case and is the stable key
stored in word_topics.topic.

Draft v1 — 2026-07-13, for review. Edit freely.
"""
from __future__ import annotations

GENERAL_TOPIC = "allgemein_funktionswoerter"

AREAS: dict[str, list[tuple[str, str, str]]] = {
    "Mensch & Identität / Человек и личность": [
        ("aussehen_koerper", "Внешность и тело", "Aussehen & Körper"),
        ("charakter_persoenlichkeit", "Характер и личность", "Charakter & Persönlichkeit"),
        ("gefuehle_emotionen", "Чувства и эмоции", "Gefühle & Emotionen"),
        ("sinne_wahrnehmung", "Ощущения и восприятие", "Sinne & Wahrnehmung"),
        ("lebensphasen_alter", "Возраст и этапы жизни", "Lebensphasen & Alter"),
        ("identitaet_herkunft", "Идентичность и происхождение", "Identität & Herkunft"),
        ("koerpersprache_gestik", "Мимика и жесты", "Körpersprache & Gestik"),
        ("talent_faehigkeiten", "Таланты и способности", "Talent & Fähigkeiten"),
    ],
    "Familie & Beziehungen / Семья и отношения": [
        ("familie_verwandtschaft", "Семья и родство", "Familie & Verwandtschaft"),
        ("partnerschaft_liebe", "Отношения и любовь", "Partnerschaft & Liebe"),
        ("freundschaft_bekannte", "Дружба и знакомые", "Freundschaft & Bekannte"),
        ("erziehung_kindheit", "Воспитание и детство", "Erziehung & Kindheit"),
        ("konflikte_streit", "Конфликты и ссоры", "Konflikte & Streit"),
        ("hochzeit_scheidung", "Свадьба и развод", "Hochzeit & Scheidung"),
        ("haustiere", "Домашние животные", "Haustiere"),
    ],
    "Alltag & Wohnen / Быт и жильё": [
        ("wohnen_zuhause", "Жильё и дом", "Wohnen & Zuhause"),
        ("haushalt_alltag", "Домашнее хозяйство", "Haushalt & Alltag"),
        ("moebel_einrichtung", "Мебель и обстановка", "Möbel & Einrichtung"),
        ("reparatur_heimwerken", "Ремонт и починка", "Reparatur & Heimwerken"),
        ("kleidung_mode", "Одежда и мода", "Kleidung & Mode"),
        ("einkaufen_konsum", "Покупки и потребление", "Einkaufen & Konsum"),
        ("nachbarschaft", "Соседство", "Nachbarschaft"),
    ],
    "Essen & Trinken / Еда и напитки": [
        ("lebensmittel_ernaehrung", "Продукты и питание", "Lebensmittel & Ernährung"),
        ("kochen_kueche", "Готовка и кухня", "Kochen & Küche"),
        ("restaurant_gastronomie", "Ресторан и общепит", "Restaurant & Gastronomie"),
        ("getraenke", "Напитки", "Getränke"),
        ("essgewohnheiten_diaet", "Пищевые привычки и диета", "Essgewohnheiten & Diät"),
        ("obst_gemuese", "Фрукты и овощи", "Obst & Gemüse"),
        ("fleisch_fisch", "Мясо и рыба", "Fleisch & Fisch"),
        ("backen_suesses", "Выпечка и сладости", "Backen & Süßes"),
    ],
    "Gesundheit & Körper / Здоровье": [
        ("koerper_anatomie", "Части тела и анатомия", "Körper & Anatomie"),
        ("krankheit_symptome", "Болезни и симптомы", "Krankheit & Symptome"),
        ("medizin_behandlung", "Медицина и лечение", "Medizin & Behandlung"),
        ("arzt_krankenhaus", "Врач и больница", "Arzt & Krankenhaus"),
        ("fitness_wohlbefinden", "Спорт и самочувствие", "Fitness & Wohlbefinden"),
        ("koerperpflege_hygiene", "Гигиена и уход за собой", "Körperpflege & Hygiene"),
        ("sucht_psyche", "Зависимости и психика", "Sucht & Psyche"),
        ("erste_hilfe_notfall", "Первая помощь и ЧП", "Erste Hilfe & Notfall"),
    ],
    "Bildung & Wissen / Образование": [
        ("schule_unterricht", "Школа и уроки", "Schule & Unterricht"),
        ("studium_hochschule", "Вуз и учёба", "Studium & Hochschule"),
        ("lernen_pruefungen", "Обучение и экзамены", "Lernen & Prüfungen"),
        ("sprachen_lernen", "Языки и их изучение", "Sprachen & Sprachenlernen"),
        ("wissen_bildungssystem", "Знание и система образования", "Wissen & Bildungssystem"),
        ("weiterbildung", "Повышение квалификации", "Weiterbildung"),
        ("schulfaecher", "Школьные предметы", "Schulfächer"),
    ],
    "Arbeit & Beruf / Работа": [
        ("berufe_taetigkeiten", "Профессии и занятия", "Berufe & Tätigkeiten"),
        ("arbeitsplatz_alltag", "Рабочее место и будни", "Arbeitsplatz & Alltag"),
        ("bewerbung_karriere", "Трудоустройство и карьера", "Bewerbung & Karriere"),
        ("arbeitsbedingungen_rechte", "Условия труда и права", "Arbeitsbedingungen & Rechte"),
        ("selbststaendigkeit_unternehmen", "Самозанятость и бизнес", "Selbstständigkeit & Unternehmen"),
        ("arbeitslosigkeit", "Безработица", "Arbeitslosigkeit"),
        ("teamarbeit_fuehrung", "Команда и руководство", "Teamarbeit & Führung"),
        ("gehalt_lohn", "Зарплата и доход", "Gehalt & Lohn"),
    ],
    "Wirtschaft & Finanzen / Экономика и финансы": [
        ("geld_finanzen", "Деньги и финансы", "Geld & Finanzen"),
        ("banken_zahlungen", "Банки и платежи", "Banken & Zahlungen"),
        ("markt_handel", "Рынок и торговля", "Markt & Handel"),
        ("wirtschaft_konjunktur", "Экономика и конъюнктура", "Wirtschaft & Konjunktur"),
        ("werbung_marketing", "Реклама и маркетинг", "Werbung & Marketing"),
        ("versicherung_steuern", "Страхование и налоги", "Versicherung & Steuern"),
        ("globalisierung", "Глобализация", "Globalisierung"),
        ("armut_reichtum", "Бедность и богатство", "Armut & Reichtum"),
    ],
    "Staat, Politik & Recht / Государство, политика, право": [
        ("politik_staat", "Политика и государство", "Politik & Staat"),
        ("wahlen_demokratie", "Выборы и демократия", "Wahlen & Demokratie"),
        ("recht_gesetz", "Право и закон", "Recht & Gesetz"),
        ("kriminalitaet_justiz", "Преступность и правосудие", "Kriminalität & Justiz"),
        ("verwaltung_buerokratie", "Администрация и бюрократия", "Verwaltung & Bürokratie"),
        ("internationale_beziehungen", "Международные отношения", "Internationale Beziehungen"),
        ("krieg_frieden", "Война и мир", "Krieg & Frieden"),
        ("migration_integration", "Миграция и интеграция", "Migration & Integration"),
        ("menschenrechte", "Права человека", "Menschenrechte"),
        ("eu_europa", "ЕС и Европа", "EU & Europa"),
    ],
    "Gesellschaft & Soziales / Общество": [
        ("gesellschaft_zusammenleben", "Общество и сосуществование", "Gesellschaft & Zusammenleben"),
        ("soziale_probleme", "Социальные проблемы", "Soziale Probleme"),
        ("gleichberechtigung_diskriminierung", "Равноправие и дискриминация", "Gleichberechtigung & Diskriminierung"),
        ("religion_weltanschauung", "Религия и мировоззрение", "Religion & Weltanschauung"),
        ("werte_normen", "Ценности и нормы", "Werte & Normen"),
        ("generationen", "Поколения", "Generationen"),
        ("ehrenamt_engagement", "Волонтёрство и активизм", "Ehrenamt & Engagement"),
        ("demografie_bevoelkerung", "Демография и население", "Demografie & Bevölkerung"),
    ],
    "Umwelt & Natur / Экология и природа": [
        ("umweltschutz_oekologie", "Охрана среды и экология", "Umweltschutz & Ökologie"),
        ("klimawandel", "Изменение климата", "Klimawandel"),
        ("energie_ressourcen", "Энергия и ресурсы", "Energie & Ressourcen"),
        ("natur_landschaft", "Природа и ландшафт", "Natur & Landschaft"),
        ("tiere_pflanzen", "Животные и растения", "Tiere & Pflanzen"),
        ("wetter_klima", "Погода и климат", "Wetter & Klima"),
        ("nachhaltigkeit_recycling", "Устойчивость и переработка", "Nachhaltigkeit & Recycling"),
        ("naturkatastrophen", "Стихийные бедствия", "Naturkatastrophen"),
        ("wasser_luft_boden", "Вода, воздух, почва", "Wasser, Luft & Boden"),
    ],
    "Wissenschaft & Technik / Наука и техника": [
        ("wissenschaft_forschung", "Наука и исследования", "Wissenschaft & Forschung"),
        ("technik_erfindungen", "Техника и изобретения", "Technik & Erfindungen"),
        ("digitalisierung_computer", "Цифровизация и компьютеры", "Digitalisierung & Computer"),
        ("internet_soziale_medien", "Интернет и соцсети", "Internet & soziale Medien"),
        ("kuenstliche_intelligenz", "Искусственный интеллект", "Künstliche Intelligenz"),
        ("mathematik_zahlen", "Математика и числа", "Mathematik & Zahlen"),
        ("weltraum_astronomie", "Космос и астрономия", "Weltraum & Astronomie"),
        ("physik_chemie", "Физика и химия", "Physik & Chemie"),
        ("biologie_leben", "Биология и жизнь", "Biologie & Leben"),
    ],
    "Medien & Kommunikation / Медиа и коммуникация": [
        ("medien_presse", "СМИ и пресса", "Medien & Presse"),
        ("kommunikation_gespraech", "Коммуникация и разговор", "Kommunikation & Gespräch"),
        ("kommunikationsmittel", "Средства связи", "Kommunikationsmittel"),
        ("information_nachrichten", "Информация и новости", "Information & Nachrichten"),
        ("fernsehen_radio", "ТВ и радио", "Fernsehen & Radio"),
        ("journalismus", "Журналистика", "Journalismus"),
        ("datenschutz_privatsphaere", "Защита данных и приватность", "Datenschutz & Privatsphäre"),
    ],
    "Kultur, Kunst & Freizeit / Культура и досуг": [
        ("kunst_kultur", "Искусство и культура", "Kunst & Kultur"),
        ("literatur_buecher", "Литература и книги", "Literatur & Bücher"),
        ("musik", "Музыка", "Musik"),
        ("film_theater", "Кино и театр", "Film & Theater"),
        ("freizeit_hobby", "Досуг и хобби", "Freizeit & Hobby"),
        ("feste_traditionen", "Праздники и традиции", "Feste & Traditionen"),
        ("sport", "Спорт", "Sport"),
        ("spiele_unterhaltung", "Игры и развлечения", "Spiele & Unterhaltung"),
        ("museum_ausstellung", "Музеи и выставки", "Museum & Ausstellung"),
        ("geschichte_vergangenheit", "История и прошлое", "Geschichte & Vergangenheit"),
    ],
    "Reisen & Verkehr / Путешествия и транспорт": [
        ("reisen_tourismus", "Путешествия и туризм", "Reisen & Tourismus"),
        ("verkehr_transport", "Транспорт и движение", "Verkehr & Transport"),
        ("auto_strassenverkehr", "Авто и дорожное движение", "Auto & Straßenverkehr"),
        ("oeffentliche_verkehrsmittel", "Общественный транспорт", "Öffentliche Verkehrsmittel"),
        ("urlaub_erholung", "Отпуск и отдых", "Urlaub & Erholung"),
        ("orientierung_wege", "Ориентирование и маршруты", "Orientierung & Wege"),
        ("unterkunft_hotel", "Проживание и отель", "Unterkunft & Hotel"),
        ("flug_flughafen", "Перелёт и аэропорт", "Flug & Flughafen"),
    ],
    "Stadt, Land & Geografie / Город, страна, география": [
        ("stadt_land", "Город и деревня", "Stadt & Land"),
        ("laender_nationen", "Страны и нации", "Länder & Nationen"),
        ("geografie_orte", "География и места", "Geografie & Orte"),
        ("gebaeude_architektur", "Здания и архитектура", "Gebäude & Architektur"),
        ("infrastruktur", "Инфраструктура", "Infrastruktur"),
        ("sehenswuerdigkeiten", "Достопримечательности", "Sehenswürdigkeiten"),
    ],
    "Zeit, Raum & Menge (функциональные)": [
        ("zeit_zeitangaben", "Время и указания времени", "Zeit & Zeitangaben"),
        ("raum_lage", "Пространство и расположение", "Raum & Lage"),
        ("menge_zahlen", "Количество и числа", "Menge & Zahlen"),
        ("haeufigkeit_wiederholung", "Частота и повторение", "Häufigkeit & Wiederholung"),
        ("reihenfolge_ablauf", "Порядок и последовательность", "Reihenfolge & Ablauf"),
        ("masse_einheiten", "Меры и единицы", "Maße & Einheiten"),
        ("bewegung_richtung", "Движение и направление", "Bewegung & Richtung"),
        ("kalender_jahreszeiten", "Календарь и времена года", "Kalender & Jahreszeiten"),
    ],
    "Denken, Sprache & Relationen (функциональные)": [
        ("denken_meinung", "Мышление и мнение", "Denken & Meinung"),
        ("ursache_wirkung", "Причина и следствие", "Ursache & Wirkung"),
        ("vergleich_gegensatz", "Сравнение и противопоставление", "Vergleich & Gegensatz"),
        ("bewertung_einstellung", "Оценка и отношение", "Bewertung & Einstellung"),
        ("moeglichkeit_notwendigkeit", "Возможность и необходимость", "Möglichkeit & Notwendigkeit"),
        ("zustimmung_ablehnung", "Согласие и отказ", "Zustimmung & Ablehnung"),
        ("sprache_ausdruck", "Язык и выражение", "Sprache & Ausdruck"),
        ("textstruktur_konnektoren", "Связки и структура текста", "Textstruktur & Konnektoren"),
        ("wunsch_absicht", "Желание и намерение", "Wunsch & Absicht"),
        ("gewissheit_zweifel", "Уверенность и сомнение", "Gewissheit & Zweifel"),
        (GENERAL_TOPIC, "Общие и служебные слова", "Allgemein & Funktionswörter"),
    ],
}

# flattened
TOPICS: list[dict] = [
    {"area": area, "slug": slug, "ru": ru, "de": de}
    for area, items in AREAS.items()
    for (slug, ru, de) in items
]
TOPIC_SLUGS = [t["slug"] for t in TOPICS]

if __name__ == "__main__":
    print(f"{len(AREAS)} areas, {len(TOPICS)} topics")
    assert len(TOPIC_SLUGS) == len(set(TOPIC_SLUGS)), "duplicate slug!"
