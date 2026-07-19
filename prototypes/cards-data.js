/* =====================================================================
   Real cards, pulled verbatim from the live enrichment.db (2026-07-19) via
   the same shaping search.card_out() does. Prototype-only: the design has to
   be judged on what the base actually holds, not on invented sample text.

   Deliberate spread — every branch the card renderer has to survive:
     Wirkung          die-noun, singular invariant in all 4 cases (44.2% of nouns)
     Student          der-noun, n-declension — the ONLY case the table earns its keep
     Herz             das-noun, irregular (gen Herzens, dat Herzen, akk Herz)
     Verantwortung    noun WITH rektion (für + Akk.) — rare, 3.2% of the base
     Auswirkung       noun with rektion + mittel frequency + long compound
     Nachhaltigkeit   long lemma — the headline has to survive 14 characters
     entwickeln       verb with rektion (21% of verbs) + 3 distinct meanings
     berücksichtigen  verb WITHOUT rektion, very long infinitive
     nachhaltig       adjective, comparable
     online           adjective, NOT comparable — no paradigm at all
     durchaus         adverb — grammar block is empty for 100% of adverbs
     gemacht          form card (form_kind=inflection) — must not pose as a word
   ===================================================================== */
'use strict';

const PROTO_CARDS = {
 "Wirkung": {
  "lemma": "Wirkung",
  "ru": "действие",
  "ru_all": [
   "действие",
   "влияние",
   "эффект"
  ],
  "level": "b1",
  "band": "B1",
  "freq": "haeufig",
  "type": "die",
  "pos": "noun",
  "article": "die",
  "topic": "ursache_wirkung",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": {
   "sg": {
    "nom": "Wirkung",
    "gen": "Wirkung",
    "dat": "Wirkung",
    "akk": "Wirkung"
   },
   "pl": {
    "nom": "Wirkungen",
    "gen": "Wirkungen",
    "dat": "Wirkungen",
    "akk": "Wirkungen"
   }
  },
  "definition_de": "Die Folge oder der Effekt, den etwas auf jemanden oder etwas hat.",
  "grammar": {
   "genitiv": "der Wirkung",
   "plural": "die Wirkungen"
  },
  "rektion": "",
  "synonyms": [
   "Effekt",
   "Einfluss"
  ],
  "collocations": [
   "Wirkung zeigen",
   "Wirkung haben"
  ],
  "examples": [
   {
    "de": "Das Medikament hat eine schnelle **Wirkung**.",
    "ru": "Лекарство оказывает быстрое действие."
   },
   {
    "de": "Seine Worte hatten eine starke **Wirkung** auf sie.",
    "ru": "Его слова произвели на неё сильное впечатление."
   },
   {
    "de": "Die **Wirkung** dieser Maßnahme ist noch nicht absehbar.",
    "ru": "Эффект этой меры пока ещё не предсказуем."
   }
  ]
 },
 "Student": {
  "lemma": "Student",
  "ru": "студент",
  "ru_all": [
   "студент",
   "учащийся (в Австрии)"
  ],
  "level": "a1",
  "band": "B1",
  "freq": "haeufig",
  "type": "der",
  "pos": "noun",
  "article": "der",
  "topic": "studium_hochschule",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": {
   "sg": {
    "nom": "Student",
    "gen": "Studenten",
    "dat": "Studenten",
    "akk": "Studenten"
   },
   "pl": {
    "nom": "Studenten",
    "gen": "Studenten",
    "dat": "Studenten",
    "akk": "Studenten"
   }
  },
  "definition_de": "Eine Person, die an einer Hochschule oder Universität studiert.",
  "grammar": {
   "genitiv": "des Studenten",
   "plural": "die Studenten"
  },
  "rektion": "",
  "synonyms": [
   "Studierender",
   "Hochschüler"
  ],
  "collocations": [
   "Student der Medizin",
   "Student im ersten Semester",
   "Student werden"
  ],
  "examples": [
   {
    "de": "Der **Student** schreibt morgen eine Prüfung.",
    "ru": "Студент завтра сдаёт экзамен."
   },
   {
    "de": "Ich bin **Studentin** an der Universität.",
    "ru": "Я студентка университета."
   },
   {
    "de": "Viele **Studenten** wohnen in Wohngemeinschaften.",
    "ru": "Многие студенты живут в общежитиях."
   }
  ]
 },
 "entwickeln": {
  "lemma": "entwickeln",
  "ru": "развивать",
  "ru_all": [
   "развивать (способности, идеи)",
   "разрабатывать (план, проект)",
   "проявлять (фото)"
  ],
  "level": "b1",
  "band": "B1",
  "freq": "haeufig",
  "type": "verb",
  "pos": "verb",
  "article": null,
  "topic": "wissenschaft_forschung",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": {
   "praesens": {
    "ich": "entwickle",
    "du": "entwickelst",
    "er": "entwickelt",
    "wir": "entwickeln",
    "ihr": "entwickelt",
    "sie": "entwickeln"
   },
   "praeteritum": "entwickelte",
   "partizip2": "entwickelt",
   "hilfsverb": "haben",
   "imperativ_du": "entwickle",
   "imperativ_ihr": "entwickelt",
   "konjunktiv2": "entwickelte"
  },
  "definition_de": "Etwas schrittweise verbessern, gestalten oder hervorbringen.",
  "grammar": {
   "praeteritum": "entwickelte",
   "partizip2": "entwickelt",
   "hilfsverb": "haben"
  },
  "rektion": "etw. (Akk.) | sich (zu etw. Dat.)",
  "synonyms": [
   "gestalten",
   "ausbauen",
   "fördern"
  ],
  "collocations": [
   "eine Theorie entwickeln",
   "Fähigkeiten entwickeln",
   "einen Film entwickeln"
  ],
  "examples": [
   {
    "de": "Die Kinder **entwickeln** ihre sprachlichen Fähigkeiten schnell.",
    "ru": "Дети быстро развивают свои языковые способности."
   },
   {
    "de": "Das Unternehmen **entwickelt** ein neues Produkt.",
    "ru": "Компания разрабатывает новый продукт."
   },
   {
    "de": "Er **entwickelte** die Fotos im Labor.",
    "ru": "Он проявил фотографии в лаборатории."
   }
  ]
 },
 "nachhaltig": {
  "lemma": "nachhaltig",
  "ru": "устойчивый",
  "ru_all": [
   "устойчивый",
   "долгосрочный",
   "неизгладимый"
  ],
  "level": "b2",
  "band": "B2",
  "freq": "haeufig",
  "type": "adj",
  "pos": "adj",
  "article": null,
  "topic": "umweltschutz_oekologie",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": {
   "komparativ": "nachhaltiger",
   "superlativ": "am nachhaltigsten"
  },
  "definition_de": "Langfristig wirksam oder umweltfreundlich; dauerhaft.",
  "grammar": {
   "komparativ": "nachhaltiger",
   "superlativ": "am nachhaltigsten"
  },
  "rektion": "",
  "synonyms": [
   "dauerhaft",
   "langfristig",
   "umweltfreundlich"
  ],
  "collocations": [
   "nachhaltige Entwicklung",
   "nachhaltige Wirkung"
  ],
  "examples": [
   {
    "de": "Die Firma setzt auf **nachhaltige** Produktion.",
    "ru": "Компания делает ставку на устойчивое производство."
   },
   {
    "de": "Sein Vortrag hinterließ einen **nachhaltigen** Eindruck.",
    "ru": "Его доклад оставил неизгладимое впечатление."
   },
   {
    "de": "Wir brauchen **nachhaltige** Lösungen für die Zukunft.",
    "ru": "Нам нужны долгосрочные решения на будущее."
   }
  ]
 },
 "durchaus": {
  "lemma": "durchaus",
  "ru": "совершенно",
  "ru_all": [
   "совершенно",
   "абсолютно",
   "непременно"
  ],
  "level": "unlisted",
  "band": "C1",
  "freq": "haeufig",
  "type": "adj",
  "pos": "adv",
  "article": null,
  "topic": "allgemein_funktionswoerter",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": null,
  "definition_de": "In vollem Maße oder ohne Einschränkung; betont eine Aussage oder Absicht.",
  "grammar": {},
  "rektion": "",
  "synonyms": [
   "absolut",
   "unbedingt",
   "völlig"
  ],
  "collocations": [
   "durchaus möglich",
   "durchaus nicht"
  ],
  "examples": [
   {
    "de": "Das ist **durchaus** richtig.",
    "ru": "Это совершенно верно."
   },
   {
    "de": "Ich möchte **durchaus** mitkommen.",
    "ru": "Я непременно хочу пойти с вами."
   },
   {
    "de": "Das ist **durchaus** nicht meine Absicht.",
    "ru": "Это абсолютно не входит в мои намерения."
   }
  ]
 },
 "Nachhaltigkeit": {
  "lemma": "Nachhaltigkeit",
  "ru": "устойчивость",
  "ru_all": [
   "устойчивость",
   "стабильность",
   "долгосрочность"
  ],
  "level": "b2",
  "band": "B2",
  "freq": "mittel",
  "type": "die",
  "pos": "noun",
  "article": "die",
  "topic": "umweltschutz_oekologie",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": {
   "sg": {
    "nom": "Nachhaltigkeit",
    "gen": "Nachhaltigkeit",
    "dat": "Nachhaltigkeit",
    "akk": "Nachhaltigkeit"
   }
  },
  "definition_de": "Das Prinzip, Ressourcen so zu nutzen, dass sie auch für zukünftige Generationen erhalten bleiben.",
  "grammar": {
   "genitiv": "der Nachhaltigkeit",
   "plural": "—"
  },
  "rektion": "",
  "synonyms": [
   "Dauerhaftigkeit",
   "Zukunftsfähigkeit"
  ],
  "collocations": [
   "Nachhaltigkeit fördern",
   "nachhaltige Entwicklung",
   "ökologische Nachhaltigkeit"
  ],
  "examples": [
   {
    "de": "**Nachhaltigkeit** ist ein zentrales Thema in der modernen Umweltpolitik.",
    "ru": "Устойчивость — центральная тема в современной экологической политике."
   },
   {
    "de": "Das Unternehmen setzt auf **Nachhaltigkeit** und umweltfreundliche Produktion.",
    "ru": "Компания делает ставку на устойчивость и экологичное производство."
   },
   {
    "de": "Die Konferenz diskutierte über Strategien für mehr **Nachhaltigkeit**.",
    "ru": "На конференции обсуждались стратегии для повышения устойчивости."
   }
  ]
 },
 "Verantwortung": {
  "lemma": "Verantwortung",
  "ru": "ответственность",
  "ru_all": [
   "ответственность",
   "обязанность"
  ],
  "level": "b1",
  "band": "B1",
  "freq": "haeufig",
  "type": "die",
  "pos": "noun",
  "article": "die",
  "topic": "werte_normen",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": {
   "sg": {
    "nom": "Verantwortung",
    "gen": "Verantwortung",
    "dat": "Verantwortung",
    "akk": "Verantwortung"
   },
   "pl": {
    "nom": "Verantwortungen",
    "gen": "Verantwortungen",
    "dat": "Verantwortungen",
    "akk": "Verantwortungen"
   }
  },
  "definition_de": "Die Pflicht, für etwas einzustehen oder die Folgen seines Handelns zu tragen.",
  "grammar": {
   "genitiv": "der Verantwortung",
   "plural": "die Verantwortungen"
  },
  "rektion": "für + Akk.",
  "synonyms": [
   "Pflicht",
   "Haftung"
  ],
  "collocations": [
   "Verantwortung tragen",
   "Verantwortung übernehmen",
   "Verantwortung ablehnen"
  ],
  "examples": [
   {
    "de": "Er übernimmt die **Verantwortung** für seine Fehler.",
    "ru": "Он берёт на себя ответственность за свои ошибки."
   },
   {
    "de": "Sie trägt die **Verantwortung** für das Projekt.",
    "ru": "Она несёт ответственность за проект."
   },
   {
    "de": "Man sollte nicht vor der **Verantwortung** weglaufen.",
    "ru": "Не стоит убегать от ответственности."
   }
  ]
 },
 "berücksichtigen": {
  "lemma": "berücksichtigen",
  "ru": "учитывать",
  "ru_all": [
   "учитывать",
   "принимать во внимание"
  ],
  "level": "c1",
  "band": "C1",
  "freq": "haeufig",
  "type": "verb",
  "pos": "verb",
  "article": null,
  "topic": "allgemein_funktionswoerter",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": {
   "praesens": {
    "ich": "berücksichtige",
    "du": "berücksichtigst",
    "er": "berücksichtigt",
    "wir": "berücksichtigen",
    "ihr": "berücksichtigt",
    "sie": "berücksichtigen"
   },
   "praeteritum": "berücksichtigte",
   "partizip2": "berücksichtigt",
   "hilfsverb": "haben",
   "imperativ_du": "berücksichtig",
   "imperativ_ihr": "berücksichtigt",
   "konjunktiv2": "berücksichtigte"
  },
  "definition_de": "Etwas in seine Überlegungen oder Handlungen einbeziehen.",
  "grammar": {
   "praeteritum": "berücksichtigte",
   "partizip2": "berücksichtigt",
   "hilfsverb": "haben"
  },
  "rektion": "",
  "synonyms": [
   "beachten",
   "einbeziehen"
  ],
  "collocations": [
   "berücksichtigen müssen",
   "alle Faktoren berücksichtigen"
  ],
  "examples": [
   {
    "de": "Man muss die Kosten **berücksichtigen**.",
    "ru": "Нужно учитывать расходы."
   },
   {
    "de": "Sie **berücksichtigte** alle Meinungen bei ihrer Entscheidung.",
    "ru": "Она учла все мнения при принятии решения."
   },
   {
    "de": "Hast du die Wettervorhersage **berücksichtigt**?",
    "ru": "Ты учёл прогноз погоды?"
   }
  ]
 },
 "Herz": {
  "lemma": "Herz",
  "ru": "сердце",
  "ru_all": [
   "сердце",
   "душа",
   "центр",
   "червы (карты)"
  ],
  "level": "b1",
  "band": "B1",
  "freq": "haeufig",
  "type": "das",
  "pos": "noun",
  "article": "das",
  "topic": "koerper_anatomie",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": {
   "sg": {
    "nom": "Herz",
    "gen": "Herzens",
    "dat": "Herzen",
    "akk": "Herz"
   },
   "pl": {
    "nom": "Herzen",
    "gen": "Herzen",
    "dat": "Herzen",
    "akk": "Herzen"
   }
  },
  "definition_de": "Das Organ, das das Blut durch den Körper pumpt; auch Symbol für Gefühle, Liebe oder den Mittelpunkt von etwas.",
  "grammar": {
   "genitiv": "des Herzens",
   "plural": "die Herzen"
  },
  "rektion": "",
  "synonyms": [
   "Seele",
   "Mitte"
  ],
  "collocations": [
   "ein großes Herz haben",
   "das Herz schlägt",
   "mit ganzem Herzen"
  ],
  "examples": [
   {
    "de": "Ihr **Herz** klopfte vor Aufregung.",
    "ru": "Её **сердце** билось от волнения."
   },
   {
    "de": "Er hat ein **Herz** aus Gold.",
    "ru": "У него **золотое сердце**."
   },
   {
    "de": "Im **Herzen** der Stadt gibt es viele Geschäfte.",
    "ru": "В **центре** города много магазинов."
   }
  ]
 },
 "gemacht": {
  "lemma": "gemacht",
  "ru": "деланный, искусственный",
  "ru_all": [
   "деланный",
   "неестественный",
   "искусственный",
   "сделавший карьеру"
  ],
  "level": "unlisted",
  "band": "C1",
  "freq": "haeufig",
  "type": "adj",
  "pos": "adj",
  "article": null,
  "topic": "charakter_persoenlichkeit",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": "inflection",
  "form_of": "machen",
  "morphology": null,
  "definition_de": "Nicht natürlich oder echt wirkend, oft übertrieben oder unnatürlich.",
  "grammar": {
   "komparativ": "gemachter",
   "superlativ": "am gemachtsten"
  },
  "rektion": "",
  "synonyms": [
   "gekünstelt",
   "unnatürlich",
   "affektiert"
  ],
  "collocations": [
   "ein **gemachter** Mann",
   "**gemachte** Freude",
   "**gemachtes** Lächeln"
  ],
  "examples": [
   {
    "de": "Ihr Lächeln wirkte **gemacht** und nicht ehrlich.",
    "ru": "Её улыбка казалась деланной и неискренней."
   },
   {
    "de": "Er ist ein **gemachter** Mann und muss sich keine Sorgen mehr machen.",
    "ru": "Он человек, сделавший карьеру, и ему больше не о чем беспокоиться."
   },
   {
    "de": "Die Szene im Film wirkte sehr **gemacht** und unrealistisch.",
    "ru": "Сцена в фильме выглядела очень искусственной и нереалистичной."
   }
  ]
 },
 "Auswirkung": {
  "lemma": "Auswirkung",
  "ru": "последствие",
  "ru_all": [
   "последствие",
   "влияние",
   "воздействие"
  ],
  "level": "unlisted",
  "band": "C1",
  "freq": "mittel",
  "type": "die",
  "pos": "noun",
  "article": "die",
  "topic": "ursache_wirkung",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": {
   "sg": {
    "nom": "Auswirkung",
    "gen": "Auswirkung",
    "dat": "Auswirkung",
    "akk": "Auswirkung"
   },
   "pl": {
    "nom": "Auswirkungen",
    "gen": "Auswirkungen",
    "dat": "Auswirkungen",
    "akk": "Auswirkungen"
   }
  },
  "definition_de": "Die Folge oder der Effekt, den eine Handlung oder ein Ereignis auf etwas hat.",
  "grammar": {
   "genitiv": "der Auswirkung",
   "plural": "die Auswirkungen"
  },
  "rektion": "auf + Akk.",
  "synonyms": [
   "Folge",
   "Effekt",
   "Konsequenz"
  ],
  "collocations": [
   "Auswirkungen haben",
   "negative Auswirkungen",
   "langfristige Auswirkungen"
  ],
  "examples": [
   {
    "de": "Die **Auswirkungen** des Klimawandels sind weltweit spürbar.",
    "ru": "Последствия изменения климата ощущаются во всём мире."
   },
   {
    "de": "Die neue Regelung hat positive **Auswirkungen** auf die Wirtschaft.",
    "ru": "Новое регулирование оказывает положительное влияние на экономику."
   },
   {
    "de": "Man sollte die **Auswirkungen** seiner Entscheidungen bedenken.",
    "ru": "Следует обдумывать последствия своих решений."
   }
  ]
 },
 "online": {
  "lemma": "online",
  "ru": "онлайн",
  "ru_all": [
   "онлайн",
   "в сети"
  ],
  "level": "unlisted",
  "band": "C1",
  "freq": "haeufig",
  "type": "adj",
  "pos": "adj",
  "article": null,
  "topic": "digitalisierung_computer",
  "topic_de": "",
  "confidence": "high",
  "register": "neutral",
  "form_kind": null,
  "form_of": null,
  "morphology": null,
  "definition_de": "Mit dem Internet verbunden oder im Internet verfügbar.",
  "grammar": {},
  "rektion": "",
  "synonyms": [
   "verbunden",
   "im Netz"
  ],
  "collocations": [
   "online sein",
   "online einkaufen",
   "online lernen"
  ],
  "examples": [
   {
    "de": "Ich bin jetzt **online** und kann mit dir chatten.",
    "ru": "Я сейчас **онлайн** и могу с тобой пообщаться."
   },
   {
    "de": "Viele Kurse werden **online** angeboten.",
    "ru": "Многие курсы предлагаются **онлайн**."
   },
   {
    "de": "Sie hat das Kleid **online** bestellt.",
    "ru": "Она заказала платье **онлайн**."
   }
  ]
 }
};
