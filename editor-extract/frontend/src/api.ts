const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export type Word = {
  id: number;
  german: string;
  article: string | null;
  word_type: string;
  translation_ru: string;
  level: string;
  grammar_data: Record<string, unknown> | null;
  examples: string[];
  source: string;
  topics: string[];
};

export type Essay = {
  id: number;
  title: string;
  text: string;
  essay_type: string;
  topic: string;
  level: string;
  created_at: string;
  updated_at: string;
};

export type EssayListItem = Essay & {
  grade: string | null;
  overall_score: number | null;
  last_analyzed_at: string | null;
};

export type TopicMeta = {
  slug: string;
  title_de: string;
  title_ru: string;
  level_default: string;
  essay_type_hints: string[];
  notes_ru: string;
  word_count: number;
  level_counts: Record<string, number>;
  phrase_count: number;
};

export type AnalyzeStreamEvent =
  | {
      type: "part_start";
      essay_id: number;
      part: string;
      label: string;
    }
  | {
      type: "part_done";
      essay_id: number;
      part: string;
      label: string;
      score: number;
      feedback_ru: string;
      errors: EssayError[];
      errors_count: number;
      all_errors: EssayError[];
      part_reports: EssayAnalysis["part_reports"];
    }
  | ({
      type: "done";
      essay_id: number;
    } & EssayAnalysis);

export type AnnotationKind =
  | "critical"
  | "style"
  | "b2_potential"
  | "good_fragment"
  | "suggestion";

export type EssayError = {
  error_id?: string;
  orphaned?: boolean;
  part?: string;
  excerpt?: string;
  start: number;
  end: number;
  type: "grammar" | "style" | "weak" | "vocabulary" | string;
  severity: "critical" | "medium" | "suggestion" | string;
  annotation_kind?: AnnotationKind | string;
  explanation_ru: string;
  correction: string;
  rule: string;
  what_wrong_ru?: string;
  why_bad_ru?: string;
  how_to_fix_ru?: string;
  b1_variant_de?: string;
  b2_variant_de?: string;
  b1_explain_ru?: string;
  b2_explain_ru?: string;
  study_phrases_de?: string[];
};

export type EssayAnalysisRecord = EssayAnalysis & {
  created_at?: string;
  text_snapshot?: string;
  is_stale?: boolean;
};

export type EssayAnalysis = {
  essay_id: number;
  overall_score: number;
  grade: "A" | "B" | "C" | "D" | string;
  errors: EssayError[];
  part_reports: {
    part: string;
    label: string;
    score: number;
    feedback_ru: string;
    errors_count: number;
    is_empty?: boolean;
  }[];
  final_summary?: {
    structure_feedback_ru: string;
    topic_feedback_ru: string;
    strengths_ru: string[];
    next_steps_ru: string[];
    overall_comment_ru: string;
  } | null;
  model: string;
};

export type Phrase = {
  id: number;
  text_de: string;
  translation_ru: string;
  essay_part: string;
  level: string;
  known: boolean;
};

export type TrainingQueueItem = {
  word_id: number;
  german: string;
  article: string | null;
  translation_ru: string;
  level: string;
  score: number;
};

export type TrainingResult = {
  word_id: number;
  expected: string;
  is_correct: boolean;
  new_score: number;
  delta: number;
};

export type ScoreTrendPoint = {
  essay_id: number;
  title: string;
  score: number;
  grade: string;
  analyzed_at: string;
};

export type RecentEssay = {
  id: number;
  title: string;
  grade: string | null;
  overall_score: number | null;
  updated_at: string;
};

export type Dashboard = {
  streak_current: number;
  streak_last_date: string | null;
  words_learned: number;
  last_grade: string | null;
  last_score: number | null;
  last_essay_title: string | null;
  last_analyzed_at: string | null;
  score_trend: ScoreTrendPoint[];
  recent_essays: RecentEssay[];
};

export async function createEssay(payload: {
  title: string;
  text: string;
  essay_type: string;
  topic: string;
  level: string;
}): Promise<Essay> {
  const res = await fetch(`${API_BASE}/api/essays`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Не удалось создать эссе");
  return res.json();
}

export async function fetchEssays(): Promise<EssayListItem[]> {
  const res = await fetch(`${API_BASE}/api/essays`);
  if (!res.ok) throw new Error("Не удалось загрузить список эссе");
  return res.json();
}

export async function fetchEssay(essayId: number): Promise<Essay> {
  const res = await fetch(`${API_BASE}/api/essays/${essayId}`);
  if (!res.ok) throw new Error("Не удалось загрузить эссе");
  return res.json();
}

export async function fetchLatestAnalysis(essayId: number): Promise<EssayAnalysisRecord | null> {
  try {
    const res = await fetch(`${API_BASE}/api/essays/${essayId}/analysis/latest`);
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function updateEssay(
  essayId: number,
  payload: Partial<Omit<Essay, "id" | "created_at" | "updated_at">>,
): Promise<Essay> {
  const res = await fetch(`${API_BASE}/api/essays/${essayId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Не удалось обновить эссе");
  return res.json();
}

export async function analyzeEssayStream(
  essayId: number,
  onEvent: (event: AnalyzeStreamEvent) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/essays/${essayId}/analyze/stream`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Не удалось запустить потоковый анализ");
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error("Поток анализа недоступен");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const line = chunk.trim();
      if (!line.startsWith("data: ")) continue;
      onEvent(JSON.parse(line.slice(6)) as AnalyzeStreamEvent);
    }
  }
}

export async function analyzeEssay(essayId: number): Promise<EssayAnalysis> {
  const res = await fetch(`${API_BASE}/api/essays/${essayId}/analyze`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(
      detail.includes("Internal Server Error")
        ? "Сервер анализа недоступен. Проверьте, что backend запущен и миграции применены."
        : "Не удалось запустить анализ",
    );
  }
  return res.json();
}

export async function fetchWords(params?: {
  topic?: string;
  level?: string;
  q?: string;
}): Promise<Word[]> {
  const search = new URLSearchParams();
  if (params?.topic) search.set("topic", params.topic);
  if (params?.level) search.set("level", params.level);
  if (params?.q) search.set("q", params.q);
  const qs = search.toString();
  const res = await fetch(`${API_BASE}/api/words${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error("Не удалось загрузить слова");
  return res.json();
}

export async function fetchTopic(slug: string): Promise<TopicMeta> {
  const res = await fetch(`${API_BASE}/api/topics/${encodeURIComponent(slug)}`);
  if (!res.ok) throw new Error("Topic nicht gefunden");
  return res.json();
}

export async function fetchPhrases(params?: {
  level?: string;
  part?: string;
  topic?: string;
}): Promise<Phrase[]> {
  const search = new URLSearchParams();
  if (params?.level) search.set("level", params.level);
  if (params?.part) search.set("part", params.part);
  if (params?.topic) search.set("topic", params.topic);
  const qs = search.toString();
  const res = await fetch(`${API_BASE}/api/phrases${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error("Не удалось загрузить клише");
  return res.json();
}

export async function setPhraseKnown(phraseId: number, known: boolean): Promise<void> {
  const res = await fetch(`${API_BASE}/api/phrases/${phraseId}/known`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ known }),
  });
  if (!res.ok) throw new Error("Не удалось обновить статус клише");
}

export async function fetchWord(wordId: number): Promise<Word> {
  const res = await fetch(`${API_BASE}/api/words/${wordId}`);
  if (!res.ok) throw new Error("Не удалось загрузить карточку слова");
  return res.json();
}

export async function queueWord(wordId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/words/${wordId}/queue`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Не удалось добавить в очередь");
}

export async function refreshWordGrammar(wordId: number): Promise<Word> {
  const res = await fetch(`${API_BASE}/api/words/${wordId}/refresh-grammar`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Не удалось обновить грамматику");
  return res.json();
}

export async function fetchHealth(): Promise<boolean> {
  const res = await fetch(`${API_BASE}/health`);
  return res.ok;
}

export async function fetchDashboard(): Promise<Dashboard> {
  const res = await fetch(`${API_BASE}/api/dashboard`);
  if (!res.ok) throw new Error("Dashboard konnte nicht geladen werden");
  return res.json();
}

export async function fetchTrainingQueue(): Promise<TrainingQueueItem[]> {
  const res = await fetch(`${API_BASE}/api/training/queue`);
  if (!res.ok) throw new Error("Не удалось загрузить очередь тренировки");
  return res.json();
}

export async function submitTrainingResult(payload: {
  word_id: number;
  user_answer: string;
  response_ms: number;
}): Promise<TrainingResult> {
  const res = await fetch(`${API_BASE}/api/training/result`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Не удалось сохранить результат тренировки");
  return res.json();
}
