import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { BatchDetail, ReviewDimensionDefinition } from "../api/types";
import { LessonCard, LessonCardMeta, VoteBar } from "../components/LessonComparison";


interface ReviewFormState {
  dimension_scores: Record<string, { score_a: number; score_b: number; comment: string }>;
}

const statusText: Record<BatchDetail["status"], string> = {
  processing: "解析中",
  ready: "开放评价",
  failed: "解析失败",
  archived: "已归档"
};

export function BatchDetailPage() {
  const navigate = useNavigate();
  const { batchId } = useParams();
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [focusedDocumentId, setFocusedDocumentId] = useState<string | null>(null);
  const [showRubric, setShowRubric] = useState(true);
  const [copiedDocumentId, setCopiedDocumentId] = useState<string | null>(null);

  const batchQuery = useQuery({
    queryKey: ["batches", batchId],
    enabled: Boolean(batchId),
    queryFn: async () => (await api.get<BatchDetail>(`/batches/${batchId}/`)).data
  });

  const dimensionsQuery = useQuery({
    queryKey: ["review-dimensions"],
    queryFn: async () => (await api.get<ReviewDimensionDefinition[]>("/reviews/dimensions/")).data
  });

  const initialForm = useMemo<ReviewFormState>(() => {
    const dimensions = dimensionsQuery.data ?? [];
    const existingReview = batchQuery.data?.current_user_review;
    const dimensionMap = Object.fromEntries(
      dimensions.map((dimension) => [
        dimension.key,
        {
          score:
            existingReview?.dimension_scores.find((item) => item.dimension_key === dimension.key)?.score ??
            8,
          score_a:
            existingReview?.dimension_scores.find((item) => item.dimension_key === dimension.key)?.score_a ??
            existingReview?.dimension_scores.find((item) => item.dimension_key === dimension.key)?.score ??
            8,
          score_b:
            existingReview?.dimension_scores.find((item) => item.dimension_key === dimension.key)?.score_b ??
            existingReview?.dimension_scores.find((item) => item.dimension_key === dimension.key)?.score ??
            8,
          comment:
            existingReview?.dimension_scores.find((item) => item.dimension_key === dimension.key)?.comment ??
            ""
        }
      ])
    );

    return {
      dimension_scores: dimensionMap
    };
  }, [batchQuery.data?.current_user_review, dimensionsQuery.data]);

  const [form, setForm] = useState<ReviewFormState>(initialForm);

  useEffect(() => {
    setForm(initialForm);
  }, [initialForm]);

  useEffect(() => {
    setFocusedDocumentId(null);
  }, [batchId]);

  const submitReview = useMutation({
    mutationFn: async () => {
      const payload = {
        recommendation: "recommend",
        overall_comment: "本次评价仅提交八个专业维度评分。",
        comparative_comment: "",
        dimension_scores: (dimensionsQuery.data ?? []).map((dimension) => ({
          dimension_key: dimension.key,
          score_a: form.dimension_scores[dimension.key]?.score_a ?? 8,
          score_b: form.dimension_scores[dimension.key]?.score_b ?? 8,
          comment: ""
        }))
      };

      return api.post(`/reviews/batches/${batchId}/my-review/`, payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["batches", batchId] });
      await queryClient.invalidateQueries({ queryKey: ["batches"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    }
  });

  if (batchQuery.isLoading || dimensionsQuery.isLoading) {
    return <div className="panel-card">正在加载教案详情...</div>;
  }

  const batch = batchQuery.data;
  if (!batch) {
    return <div className="panel-card">未找到对应批次。</div>;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      await submitReview.mutateAsync();
    } catch {
      setError("评价提交失败，请稍后重试。");
    }
  };

  const lessonMeta: LessonCardMeta = {
    subject: batch.subject,
    gradeLevel: batch.grade_level,
    theme: batch.teaching_theme,
    uploaderName: batch.uploader.display_name
  };

  const refreshBatch = async () => {
    await queryClient.invalidateQueries({ queryKey: ["batches", batchId] });
  };

  const copyDocumentText = async (documentId: string) => {
    const document = batch.documents.find((item) => item.id === documentId);
    if (!document) {
      return;
    }

    const text = document.extracted_text || document.title;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedDocumentId(documentId);
      window.setTimeout(() => setCopiedDocumentId(null), 1600);
    } catch {
      setError("复制失败，请确认浏览器已允许剪贴板权限。");
    }
  };

  const focusedDocument = batch.documents.find((document) => document.id === focusedDocumentId);
  const focusClass =
    focusedDocument?.slot_number === 1
      ? "lesson-card-grid-left-expanded"
      : focusedDocument?.slot_number === 2
        ? "lesson-card-grid-right-expanded"
        : "";

  return (
    <div className="detail-space arena-page">
      <section className="battle-summary">
        <div>
          <p className="eyebrow">评价详情</p>
          <h2>{batch.title}</h2>
          <p className="battle-summary-meta">
            {batch.subject} · {batch.grade_level}
            {batch.teaching_theme ? ` · ${batch.teaching_theme}` : ""}
          </p>
          <p className="battle-summary-note">
            {batch.cover_summary || "暂无批次说明。"}
          </p>
        </div>
        <div className="battle-summary-actions">
          <span className="metric-pill">上传者 {batch.uploader.display_name}</span>
          <span className={`status-badge status-${batch.status}`}>{statusText[batch.status]}</span>
          <button className="secondary-button" onClick={() => navigate("/")} type="button">
            返回看板
          </button>
        </div>
      </section>

      <form
        className={`comparison-form ${batch.can_current_user_review ? "" : "comparison-form-readonly"}`}
        onSubmit={handleSubmit}
      >
        <section className="lesson-comparison-section">
          <div className="lesson-section-head">
            <div>
              <p className="eyebrow">教案内容</p>
              <h3>教案原文</h3>
              <p>教案 A 与教案 B</p>
            </div>
            <div className="view-switcher" aria-label="阅读布局切换">
              <button
                className={`view-switcher-button ${focusedDocumentId === null ? "view-switcher-button-active" : ""}`}
                onClick={() => setFocusedDocumentId(null)}
                type="button"
              >
                双栏对照
              </button>
              {batch.documents.map((document) => (
                <button
                  className={`view-switcher-button ${focusedDocumentId === document.id ? "view-switcher-button-active" : ""}`}
                  key={document.id}
                  onClick={() =>
                    setFocusedDocumentId((current) => (current === document.id ? null : document.id))
                  }
                  type="button"
                >
                  查看 {document.slot_number === 1 ? "A" : "B"}
                </button>
              ))}
            </div>
          </div>

          <div className={`lesson-card-grid ${focusClass}`}>
            {batch.documents.map((document) => {
              const expanded = focusedDocumentId === document.id;
              const collapsed = Boolean(focusedDocumentId && focusedDocumentId !== document.id);

              return (
                <LessonCard
                  collapsed={collapsed}
                  copied={copiedDocumentId === document.id}
                  document={document}
                  expanded={expanded}
                  key={document.id}
                  meta={lessonMeta}
                  onCopy={() => copyDocumentText(document.id)}
                  onRefresh={refreshBatch}
                  onToggleFocus={() =>
                    setFocusedDocumentId((current) => (current === document.id ? null : document.id))
                  }
                />
              );
            })}
          </div>
        </section>

        {batch.can_current_user_review ? (
          <>
            {showRubric ? (
              <section className="panel-card rubric-drawer">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">评分维度</p>
                    <h3>专业维度评分</h3>
                    <p className="rubric-helper">教案 A、教案 B 分项评分。</p>
                  </div>
                  <button className="secondary-button" onClick={() => setShowRubric(false)} type="button">
                    收起
                  </button>
                </div>
                <div className="rubric-grid">
                  {(dimensionsQuery.data ?? []).map((dimension) => (
                    <div className="dimension-card compact-dimension-card" key={dimension.key}>
                      <div className="dimension-head">
                        <div>
                          <strong>{dimension.label}</strong>
                          <p>{dimension.description}</p>
                        </div>
                        <span className="metric-pill">{Math.round(dimension.weight * 100)}%</span>
                      </div>
                      <div className="dimension-pair-score-row">
                        <label>
                          <span>
                            教案 A
                            <strong>{form.dimension_scores[dimension.key]?.score_a ?? 8}</strong>
                          </span>
                          <input
                            max="10"
                            min="1"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                dimension_scores: {
                                  ...current.dimension_scores,
                                  [dimension.key]: {
                                    ...current.dimension_scores[dimension.key],
                                    score_a: Number(event.target.value)
                                  }
                                }
                              }))
                            }
                            type="range"
                            value={form.dimension_scores[dimension.key]?.score_a ?? 8}
                          />
                        </label>
                        <label>
                          <span>
                            教案 B
                            <strong>{form.dimension_scores[dimension.key]?.score_b ?? 8}</strong>
                          </span>
                          <input
                            max="10"
                            min="1"
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                dimension_scores: {
                                  ...current.dimension_scores,
                                  [dimension.key]: {
                                    ...current.dimension_scores[dimension.key],
                                    score_b: Number(event.target.value)
                                  }
                                }
                              }))
                            }
                            type="range"
                            value={form.dimension_scores[dimension.key]?.score_b ?? 8}
                          />
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            {error ? <p className="form-error">{error}</p> : null}
            <div className="arena-footbar">
              {!batch.can_view_review_summary ? (
                <p className="arena-footnote">当前为盲评模式，你不会看到他人的汇总评分。</p>
              ) : (
                <button className="arena-summary-link" onClick={() => navigate("/")} type="button">
                  查看评分汇总
                </button>
              )}
            </div>

            <VoteBar
              hasExistingReview={Boolean(batch.current_user_review)}
              isSubmitting={submitReview.isPending}
              onToggleRubric={() => setShowRubric((current) => !current)}
              showRubric={showRubric}
            />
          </>
        ) : (
          <section className="panel-card">
            <h3>当前不可评价</h3>
            <p>该批次尚未开放评价。</p>
          </section>
        )}
      </form>
    </div>
  );
}
