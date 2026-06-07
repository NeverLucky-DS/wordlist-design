import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  analyzeEssayStream,
  createEssay,
  fetchEssay,
  fetchLatestAnalysis,
  fetchPhrases,
  fetchTopic,
  fetchWord,
  fetchWords,
  queueWord,
  refreshWordGrammar,
  setPhraseKnown,
  updateEssay,
  type EssayAnalysis,
  type EssayError,
  type Phrase,
  type TopicMeta,
  type Word,
} from "../api";
import { formatGermanHeadline } from "../dictionary/wordDisplay";
import { AnnotationPopover } from "./AnnotationPopover";
import { BLOCKS, DEFAULT_PHRASES } from "./constants";
import { useEditorMeta } from "./editorMetaContext";
import { buildEssayText, countWords, parseEssayText } from "./essayText";
import { clearEditorDraft, loadEditorDraft, saveEditorDraft } from "./editorDraft";
import {
  buildFallbackErrorsFromBlocks,
  countOrphanedErrors,
  countTotalErrors,
  mapErrorsToBlocks,
  reanchorAllBlocks,
} from "./errorUtils";
import { EssayMap } from "./EssayMap";
import { ManuscriptColumn } from "./ManuscriptColumn";
import { NewEssayButton } from "./NewEssayButton";
import { MaterialsDesk } from "./MaterialsDesk";
import type { BlockKey, ErrorAnchor, SelectedError } from "./types";
import { useLiveAnchorRect } from "./useLiveAnchorRect";
import "../dictionary/dictionary.css";
import "./editorial.css";

type AnalysisSnapshot = {
  text: string;
  analyzedAt: string;
};

export function EditorShell() {
  const { essayId: routeEssayId } = useParams<{ essayId?: string }>();
  const { level, setLevel } = useEditorMeta();
  const [essayMeta, setEssayMeta] = useState({
    title: "Deutsch Essay",
    essay_type: "argumentativ",
    topic: "technologie",
    level: "B1",
  });
  const [blocks, setBlocks] = useState<Record<BlockKey, string>>({
    einleitung: "",
    argument1: "",
    argument2: "",
    schluss: "",
  });
  const [essayId, setEssayId] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<EssayAnalysis | null>(null);
  const [analysisSnapshot, setAnalysisSnapshot] = useState<AnalysisSnapshot | null>(null);
  const [errorsByBlock, setErrorsByBlock] = useState<Record<BlockKey, EssayError[]>>({
    einleitung: [],
    argument1: [],
    argument2: [],
    schluss: [],
  });
  const [selectedError, setSelectedError] = useState<SelectedError | null>(null);
  const [errorAnchor, setErrorAnchor] = useState<ErrorAnchor | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [loadingEssay, setLoadingEssay] = useState(false);
  const [message, setMessage] = useState("");
  const [lastAnalyzedAt, setLastAnalyzedAt] = useState<string | null>(null);
  const [activeBlock, setActiveBlock] = useState<BlockKey>("einleitung");
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [topicWords, setTopicWords] = useState<Word[]>([]);
  const [topicMeta, setTopicMeta] = useState<TopicMeta | null>(null);
  const [sidebarError, setSidebarError] = useState("");
  const [floatWord, setFloatWord] = useState<Word | null>(null);
  const [floatWordLoading, setFloatWordLoading] = useState(false);
  const [floatWordError, setFloatWordError] = useState("");
  const appliedTopicSlug = useRef("");
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [analyzeProgress, setAnalyzeProgress] = useState<string | null>(null);
  const reanchorTimer = useRef<number | null>(null);
  const autosaveTimer = useRef<number | null>(null);
  const blocksRef = useRef(blocks);
  const essayMetaRef = useRef(essayMeta);
  const essayIdRef = useRef(essayId);
  const navigate = useNavigate();
  blocksRef.current = blocks;
  essayMetaRef.current = essayMeta;
  essayIdRef.current = essayId;

  const liveAnchorRect = useLiveAnchorRect(errorAnchor);

  const wordCount = useMemo(() => countWords(blocks), [blocks]);
  const blockWordCounts = useMemo(
    () =>
      BLOCKS.reduce(
        (acc, block) => {
          acc[block.key] = countBlockWords(blocks[block.key]);
          return acc;
        },
        { einleitung: 0, argument1: 0, argument2: 0, schluss: 0 } as Record<BlockKey, number>,
      ),
    [blocks],
  );

  const isTextStale = useMemo(() => {
    if (!analysisSnapshot) return false;
    return buildEssayText(blocks).text !== analysisSnapshot.text;
  }, [blocks, analysisSnapshot]);

  const staleHint = useMemo(() => {
    if (!analysis || !analysisSnapshot) return null;
    const total = countTotalErrors(errorsByBlock);
    const orphaned = countOrphanedErrors(errorsByBlock);
    if (total > 0 && orphaned / total > 0.3) {
      return "Analyse veraltet — erneut analysieren empfohlen.";
    }
    if (isTextStale) {
      return "Text geändert — Markierungen angepasst.";
    }
    return null;
  }, [analysis, analysisSnapshot, errorsByBlock, isTextStale]);

  useEffect(() => {
    setEssayMeta((prev) => (prev.level === level ? prev : { ...prev, level }));
  }, [level]);

  useEffect(() => {
    if (routeEssayId) return;
    const draft = loadEditorDraft();
    if (draft?.essayId) {
      navigate(`/editor/${draft.essayId}`, { replace: true });
    }
  }, [routeEssayId, navigate]);

  useEffect(() => {
    saveEditorDraft({ essayId, blocks, essayMeta });
  }, [essayId, blocks, essayMeta]);

  const applyAnalysis = useCallback(
    (
      result: EssayAnalysis,
      snapshotText: string,
      analyzedAt: string,
      currentBlocks: Record<BlockKey, string> = blocksRef.current,
    ) => {
      const { ranges } = buildEssayText(currentBlocks);
      setAnalysis(result);
      setAnalysisSnapshot({ text: snapshotText, analyzedAt });
      setLastAnalyzedAt(analyzedAt);

      const sourceErrors =
        result.errors.length > 0
          ? result.errors
          : buildFallbackErrorsFromBlocks(currentBlocks);
      const byBlock = mapErrorsToBlocks(sourceErrors, currentBlocks, ranges);
      setErrorsByBlock(byBlock);
      return byBlock;
    },
    [],
  );

  const applyPartialAnalysis = useCallback(
    (
      allErrors: EssayError[],
      partReports: EssayAnalysis["part_reports"],
      essayIdValue: number,
    ) => {
      const currentBlocks = blocksRef.current;
      const { ranges } = buildEssayText(currentBlocks);
      const byBlock = mapErrorsToBlocks(allErrors, currentBlocks, ranges);
      setErrorsByBlock(byBlock);
      setAnalysis((prev) => ({
        essay_id: essayIdValue,
        overall_score: prev?.overall_score ?? 0,
        grade: prev?.grade ?? "D",
        errors: allErrors,
        part_reports: partReports,
        final_summary: prev?.final_summary ?? null,
        model: prev?.model ?? "mistral",
      }));
      return byBlock;
    },
    [],
  );

  useEffect(() => {
    const id = routeEssayId ? Number(routeEssayId) : NaN;
    if (!Number.isFinite(id) || id <= 0) return;

    let cancelled = false;
    setLoadingEssay(true);
    setMessage("");

    fetchEssay(id)
      .then(async (essay) => {
        if (cancelled) return;
        setEssayId(essay.id);
        setEssayMeta({
          title: essay.title,
          essay_type: essay.essay_type,
          topic: essay.topic,
          level: essay.level,
        });
        setLevel(essay.level);
        const parsed = parseEssayText(essay.text);
        setBlocks(parsed);

        const latest = await fetchLatestAnalysis(id);
        if (cancelled || !latest) return;

        const analyzedAt = latest.created_at || new Date().toISOString();
        const reanchored = reanchorAllBlocks(
          parsed,
          mapErrorsToBlocks(
            latest.errors.length > 0 ? latest.errors : buildFallbackErrorsFromBlocks(parsed),
            parsed,
            buildEssayText(parsed).ranges,
          ),
        );
        setAnalysis(latest);
        setAnalysisSnapshot({ text: latest.text_snapshot || essay.text, analyzedAt });
        setLastAnalyzedAt(analyzedAt);
        setErrorsByBlock(reanchored);

        if (latest.is_stale) {
          setMessage("Analyse geladen — Text wurde seitdem geändert.");
        } else {
          setMessage(`Analyse geladen: ${latest.grade} (${latest.overall_score}).`);
        }
      })
      .catch((e) => {
        if (cancelled) return;
        const msg = e instanceof Error ? e.message : "Essay konnte nicht geladen werden";
        setMessage(msg.includes("fetch") ? "Не удалось загрузить эссе. Проверьте API." : msg);
      })
      .finally(() => {
        if (!cancelled) setLoadingEssay(false);
      });

    return () => {
      cancelled = true;
    };
  }, [routeEssayId, setLevel]);

  function resetAnalysisState() {
    setAnalysis(null);
    setAnalysisSnapshot(null);
    setSelectedError(null);
    setErrorAnchor(null);
    setErrorsByBlock({
      einleitung: [],
      argument1: [],
      argument2: [],
      schluss: [],
    });
  }

  function updateEssayMeta(patch: Partial<typeof essayMeta>) {
    if (patch.level) setLevel(patch.level);
    setEssayMeta((prev) => ({ ...prev, ...patch }));
    if (analysis) {
      resetAnalysisState();
      setMessage("Parameter geändert. Bitte Analyse erneut starten.");
    }
  }

  useEffect(() => {
    const slug = essayMeta.topic.trim().toLowerCase();
    if (!slug) {
      setTopicMeta(null);
      appliedTopicSlug.current = "";
      return;
    }
    let cancelled = false;
    fetchTopic(slug)
      .then((meta) => {
        if (cancelled) return;
        setTopicMeta(meta);
        if (appliedTopicSlug.current !== meta.slug) {
          appliedTopicSlug.current = meta.slug;
          setEssayMeta((prev) => ({ ...prev, level: meta.level_default }));
          setLevel(meta.level_default);
        }
      })
      .catch(() => {
        if (!cancelled) setTopicMeta(null);
      });
    return () => {
      cancelled = true;
    };
  }, [essayMeta.topic, setLevel]);

  useEffect(() => {
    let cancelled = false;
    setSidebarError("");
    const topicSlug = essayMeta.topic.trim().toLowerCase() || undefined;
    Promise.all([
      fetchPhrases({ part: activeBlock, topic: topicSlug }),
      fetchWords({ topic: topicSlug }),
    ])
      .then(([phrasesData, wordsData]) => {
        if (cancelled) return;
        const fallback = DEFAULT_PHRASES[activeBlock].map((phrase, idx) => ({
          id: -(idx + 1),
          text_de: phrase.text_de,
          translation_ru: phrase.translation_ru,
          essay_part: activeBlock,
          level: essayMeta.level,
          known: false,
        }));
        setPhrases(phrasesData.length > 0 ? phrasesData : fallback);
        setTopicWords(wordsData);
      })
      .catch((e) => {
        if (cancelled) return;
        setSidebarError(e instanceof Error ? e.message : "Fehler beim Laden");
      });
    return () => {
      cancelled = true;
    };
  }, [essayMeta.topic, activeBlock]);

  function scheduleReanchor(nextBlocks: Record<BlockKey, string>) {
    if (!analysis) return;
    if (reanchorTimer.current) window.clearTimeout(reanchorTimer.current);
    reanchorTimer.current = window.setTimeout(() => {
      setErrorsByBlock((prev) => reanchorAllBlocks(nextBlocks, prev));
    }, 300);
  }

  function onBlockChange(block: BlockKey, value: string) {
    setBlocks((prev) => {
      const next = { ...prev, [block]: value };
      scheduleReanchor(next);
      scheduleAutosave(next);
      return next;
    });
    setActiveBlock(block);
  }

  async function saveEssay(
    text: string,
    silent = false,
    options?: { updateUrl?: boolean },
  ): Promise<number | null> {
    const hasContent = BLOCKS.some((block) => blocksRef.current[block.key].trim().length > 0);
    if (!hasContent) return null;

    const updateUrl = options?.updateUrl ?? true;

    if (!silent) setSaveStatus("saving");
    try {
      const payload = {
        title: essayMetaRef.current.title,
        text,
        essay_type: essayMetaRef.current.essay_type,
        topic: essayMetaRef.current.topic,
        level: essayMetaRef.current.level,
      };
      const currentId = essayIdRef.current;
      const saved = currentId
        ? await updateEssay(currentId, payload)
        : await createEssay(payload);
      setEssayId(saved.id);
      if (updateUrl && (!routeEssayId || Number(routeEssayId) !== saved.id)) {
        navigate(`/editor/${saved.id}`, { replace: true });
      }
      if (!silent) setSaveStatus("saved");
      return saved.id;
    } catch (e) {
      if (!silent) {
        setSaveStatus("error");
        const msg = e instanceof Error ? e.message : "";
        setMessage(
          msg.includes("fetch") || msg === "Failed to fetch"
            ? "Не удалось сохранить. Проверьте, что backend запущен (порт 8000)."
            : "Speichern fehlgeschlagen.",
        );
      }
      return null;
    }
  }

  function scheduleAutosave(nextBlocks: Record<BlockKey, string>) {
    if (autosaveTimer.current) window.clearTimeout(autosaveTimer.current);
    autosaveTimer.current = window.setTimeout(() => {
      const { text } = buildEssayText(nextBlocks);
      void saveEssay(text, true);
    }, 2000);
  }

  async function flushSave() {
    if (autosaveTimer.current) window.clearTimeout(autosaveTimer.current);
    const { text } = buildEssayText(blocksRef.current);
    await saveEssay(text, true, { updateUrl: false });
  }

  useEffect(() => {
    const onHide = () => {
      if (document.visibilityState === "hidden") void flushSave();
    };
    const onUnload = () => {
      void flushSave();
    };
    document.addEventListener("visibilitychange", onHide);
    window.addEventListener("beforeunload", onUnload);
    return () => {
      document.removeEventListener("visibilitychange", onHide);
      window.removeEventListener("beforeunload", onUnload);
      void flushSave();
    };
  }, []);

  function startNewEssay() {
    if (reanchorTimer.current) window.clearTimeout(reanchorTimer.current);
    if (autosaveTimer.current) window.clearTimeout(autosaveTimer.current);
    resetAnalysisState();
    setEssayId(null);
    setBlocks({
      einleitung: "",
      argument1: "",
      argument2: "",
      schluss: "",
    });
    setEssayMeta({
      title: "Deutsch Essay",
      essay_type: "argumentativ",
      topic: "technologie",
      level: essayMeta.level,
    });
    setMessage("");
    setSaveStatus("idle");
    setLastAnalyzedAt(null);
    setActiveBlock("einleitung");
    clearEditorDraft();
    navigate("/editor", { replace: true });
  }

  async function handleAnalyze() {
    const { text } = buildEssayText(blocks);
    const hasContent = BLOCKS.some((block) => blocks[block.key].trim().length > 0);
    if (!hasContent) {
      setMessage("Bitte mindestens einen Abschnitt schreiben.");
      return;
    }

    setAnalyzing(true);
    setAnalyzeProgress("Analyse startet…");
    setSelectedError(null);
    setErrorAnchor(null);
    setMessage("");
    let apiErrorCount = 0;

    try {
      const id = await saveEssay(text);
      if (!id) return;

      await analyzeEssayStream(id, (event) => {
        if (event.type === "part_start") {
          setAnalyzeProgress(`Analysiere ${event.label}…`);
          return;
        }
        if (event.type === "part_done") {
          apiErrorCount = event.all_errors.length;
          applyPartialAnalysis(event.all_errors, event.part_reports, id);
          setAnalyzeProgress(`${event.label} fertig (${event.errors_count} Hinweise)`);
          setMessage(`${event.label}: ${event.errors_count} Hinweis(e)`);
          return;
        }
        if (event.type === "done") {
          const analyzedAt = new Date().toISOString();
          apiErrorCount = event.errors.length;
          const result: EssayAnalysis = {
            essay_id: id,
            overall_score: event.overall_score,
            grade: event.grade,
            errors: event.errors,
            part_reports: event.part_reports,
            final_summary: event.final_summary,
            model: event.model,
          };
          const byBlock = applyAnalysis(result, text, analyzedAt, blocks);
          const markCount = Object.values(byBlock).reduce(
            (n, list) => n + list.filter((e) => !e.orphaned).length,
            0,
          );
          if (markCount === 0) {
            setMessage(
              `Analyse fertig: ${result.grade} (${result.overall_score}). API: ${apiErrorCount} → 0 Markierungen.`,
            );
          } else {
            setMessage(
              `Analyse fertig: ${result.grade} (${result.overall_score}). API: ${apiErrorCount} → ${markCount} Markierung(en).`,
            );
          }
        }
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Analyse fehlgeschlagen";
      setMessage(
        msg.includes("fetch") || msg === "Failed to fetch"
          ? "Анализ недоступен. Запустите backend."
          : msg,
      );
    } finally {
      setAnalyzing(false);
      setAnalyzeProgress(null);
    }
  }

  function jumpToBlock(block: BlockKey) {
    setActiveBlock(block);
  }

  function insertPhrase(text: string) {
    setBlocks((prev) => {
      const current = prev[activeBlock].trim();
      const separator = current ? "\n" : "";
      const next = { ...prev, [activeBlock]: `${prev[activeBlock]}${separator}${text.trim()}` };
      scheduleReanchor(next);
      scheduleAutosave(next);
      return next;
    });
    setMessage("Phrase eingefügt.");
  }

  async function onTogglePhraseKnown(phrase: Phrase, known: boolean) {
    if (phrase.id < 0) {
      setPhrases((prev) => prev.map((p) => (p.id === phrase.id ? { ...p, known } : p)));
      return;
    }
    try {
      await setPhraseKnown(phrase.id, known);
      setPhrases((prev) => prev.map((p) => (p.id === phrase.id ? { ...p, known } : p)));
    } catch (e) {
      setSidebarError(e instanceof Error ? e.message : "Update fehlgeschlagen");
    }
  }

  async function addWordToTraining(wordId: number) {
    try {
      await queueWord(wordId);
      setMessage("Wort zur Übung hinzugefügt.");
    } catch (e) {
      setSidebarError(e instanceof Error ? e.message : "Hinzufügen fehlgeschlagen");
    }
  }

  async function addStudyPhraseToTraining(phrase: string) {
    try {
      const words = await fetchWords({ q: phrase, level: essayMeta.level });
      if (!words.length) {
        setMessage("Phrase eingefügt. Wort nicht im Wörterbuch.");
        return;
      }
      await queueWord(words[0].id);
      setMessage("Konstruktion zur Übung hinzugefügt.");
    } catch (e) {
      setSidebarError(e instanceof Error ? e.message : "Hinzufügen fehlgeschlagen");
    }
  }

  function insertHelperWord(word: string) {
    setBlocks((prev) => {
      const current = prev[activeBlock];
      const separator = current.trim() && !current.endsWith(" ") ? " " : "";
      const next = { ...prev, [activeBlock]: `${current}${separator}${word}` };
      scheduleReanchor(next);
      scheduleAutosave(next);
      return next;
    });
    setMessage("Wort eingefügt.");
  }

  async function selectSidebarWord(word: Word) {
    if (floatWord?.id === word.id) {
      setFloatWord(null);
      setFloatWordError("");
      return;
    }
    setFloatWord(word);
    setFloatWordError("");
    setFloatWordLoading(true);
    try {
      setFloatWord(await fetchWord(word.id));
    } catch (e) {
      setFloatWordError(e instanceof Error ? e.message : "Karte konnte nicht geladen werden");
    } finally {
      setFloatWordLoading(false);
    }
  }

  function closeFloatWord() {
    setFloatWord(null);
    setFloatWordError("");
  }

  async function refreshFloatWord() {
    if (!floatWord) return;
    setFloatWordLoading(true);
    setFloatWordError("");
    try {
      const updated = await refreshWordGrammar(floatWord.id);
      setFloatWord(updated);
      setTopicWords((prev) => prev.map((w) => (w.id === updated.id ? updated : w)));
    } catch (e) {
      setFloatWordError(e instanceof Error ? e.message : "Wiktionary-Fehler");
    } finally {
      setFloatWordLoading(false);
    }
  }

  function insertFloatWord() {
    if (!floatWord) return;
    insertHelperWord(formatGermanHeadline(floatWord));
  }

  function onInlineErrorClick(block: BlockKey, err: EssayError, errorId: string) {
    setSelectedError({ block, error: err });
    setErrorAnchor({ block, errorId });
    setActiveBlock(block);
  }

  function closeErrorPopover() {
    setSelectedError(null);
    setErrorAnchor(null);
  }

  const statusLine = useMemo(() => {
    if (loadingEssay) return "Essay wird geladen…";
    if (message) return message;
    if (saveStatus === "saving") return "Speichern…";
    if (saveStatus === "saved") return "Gespeichert.";
    if (saveStatus === "error") return "Speichern fehlgeschlagen.";
    return "";
  }, [loadingEssay, message, saveStatus]);

  return (
    <section className="editorial-workbench">
      <span className="editorial-side-label" aria-hidden="true">
        MANUSKRIPT
      </span>
      <div className="editorial-sheet">
        <div className="editorial-hero">
          <p className="editorial-eyebrow">Schreiben</p>
          <h1 className="editorial-hero-title">Editor</h1>
          <p className="editorial-hero-lede">
            Schreiben, prüfen, verbessern — Ihr Aufsatz mit KI-Feedback, Abschnitt für Abschnitt.
          </p>
        </div>
        <div className="editorial-layout">
        <EssayMap
          activeBlock={activeBlock}
          wordCount={wordCount}
          blockWordCounts={blockWordCounts}
          onJump={jumpToBlock}
        />

        <div className="editorial-center">
          <div className="editorial-meta-strip">
            <NewEssayButton onClick={startNewEssay} />
            <label className="editorial-meta-cell">
              <span className="editorial-meta-label">Form</span>
              <select
                value={essayMeta.essay_type}
                onChange={(e) => updateEssayMeta({ essay_type: e.target.value })}
              >
                <option value="argumentativ">argumentativ</option>
                <option value="erorterung">Erörterung</option>
                <option value="kommentar">Kommentar</option>
                <option value="textanalyse">Textanalyse</option>
              </select>
            </label>
            <label className="editorial-meta-cell">
              <span className="editorial-meta-label">Thema</span>
              <input
                type="text"
                value={essayMeta.topic}
                onChange={(e) => updateEssayMeta({ topic: e.target.value })}
                placeholder="Technologie"
              />
            </label>
            <label className="editorial-meta-cell editorial-meta-cell--level">
              <span className="editorial-meta-label">Niveau</span>
              <select value={level} onChange={(e) => setLevel(e.target.value)}>
                <option value="B1">B1</option>
                <option value="B2">B2</option>
                <option value="C1">C1</option>
              </select>
            </label>
          </div>

          <ManuscriptColumn
            blocks={blocks}
            activeBlock={activeBlock}
            topic={essayMeta.topic}
            blockWordCount={blockWordCounts[activeBlock]}
            errorsByBlock={errorsByBlock}
            analysis={analysis}
            message={statusLine}
            floatWord={floatWord}
            floatWordLoading={floatWordLoading}
            floatWordError={floatWordError}
            onBlockChange={onBlockChange}
            onFocusBlock={setActiveBlock}
            onErrorClick={onInlineErrorClick}
            onCloseFloatWord={closeFloatWord}
            onQueueFloatWord={() => floatWord && addWordToTraining(floatWord.id)}
            onRefreshFloatWord={refreshFloatWord}
            onInsertFloatWord={insertFloatWord}
          />

        </div>

        <MaterialsDesk
          topic={essayMeta.topic}
          topicMeta={topicMeta}
          essayType={essayMeta.essay_type}
          phrases={phrases}
          topicWords={topicWords}
          sidebarError={sidebarError}
          lastAnalyzedAt={lastAnalyzedAt}
          analyzing={analyzing}
          level={essayMeta.level}
          grade={analysis?.grade ?? null}
          staleHint={staleHint}
          analyzeProgress={analyzeProgress}
          onAnalyze={handleAnalyze}
          onInsertPhrase={insertPhrase}
          onToggleKnown={onTogglePhraseKnown}
          onSelectWord={selectSidebarWord}
          selectedWordId={floatWord?.id ?? null}
        />
        </div>
      </div>

      {selectedError && liveAnchorRect && (
        <AnnotationPopover
          error={selectedError.error}
          anchorRect={liveAnchorRect}
          onInsert={insertPhrase}
          onAddToTraining={addStudyPhraseToTraining}
          onClose={closeErrorPopover}
        />
      )}
    </section>
  );
}

function countBlockWords(text: string): number {
  return text
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}
