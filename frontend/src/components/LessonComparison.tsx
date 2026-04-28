import { LessonPlanDocument } from "../api/types";
import { InlineIcon } from "./InlineIcon";

export interface LessonCardMeta {
  subject: string;
  gradeLevel: string;
  theme?: string;
  uploaderName: string;
}

function buildPdfPreviewUrl(url: string) {
  return `${url}#toolbar=1&navpanes=0&view=FitH`;
}

export function DocumentPreview({
  document,
  expanded
}: {
  document: LessonPlanDocument;
  expanded: boolean;
}) {
  if (document.parse_status !== "ready") {
    return (
      <div className="empty-preview lesson-empty-preview">
        {document.parse_status === "failed"
          ? `解析失败：${document.parse_error || "请下载原文查看。"}`
          : "文档正在处理中，请稍后刷新查看。"}
      </div>
    );
  }

  if (document.display_mode === "pdf" && document.preview_url) {
    return (
      <div className="document-preview-shell">
        <iframe
          className={`document-frame ${expanded ? "document-frame-expanded" : ""}`}
          loading="lazy"
          src={buildPdfPreviewUrl(document.preview_url)}
          title={`${document.title} 版式预览`}
        />
      </div>
    );
  }

  return (
    <div
      className={`document-preview ${expanded ? "document-preview-expanded" : ""}`}
      dangerouslySetInnerHTML={{ __html: document.rendered_html || "<p>暂无预览内容。</p>" }}
    />
  );
}

export function LessonCard({
  document,
  meta,
  expanded,
  collapsed,
  copied,
  onCopy,
  onRefresh,
  onToggleFocus
}: {
  document: LessonPlanDocument;
  meta: LessonCardMeta;
  expanded: boolean;
  collapsed: boolean;
  copied: boolean;
  onCopy: () => void;
  onRefresh: () => void;
  onToggleFocus: () => void;
}) {
  const slotLabel = document.slot_number === 1 ? "A" : "B";
  const previewMode = document.display_mode === "pdf" ? "PDF 文档" : "文档内容";

  return (
    <article
      className={`lesson-card ${expanded ? "lesson-card-expanded" : ""} ${
        collapsed ? "lesson-card-collapsed" : ""
      }`}
    >
      <button className="lesson-card-collapsed-label" onClick={onToggleFocus} title={`展开教案 ${slotLabel}`} type="button">
        <span>教案 {slotLabel}</span>
      </button>

      <div className="lesson-card-main">
        <header className="lesson-card-head">
          <div className="lesson-card-title">
            <span className="lesson-slot-badge">教案 {slotLabel}</span>
            <div>
              <h3>{document.title}</h3>
              <p>
                {meta.subject} · {meta.gradeLevel || "未设置年级"}
                {meta.theme ? ` · ${meta.theme}` : ""}
              </p>
            </div>
          </div>

          <div className="lesson-card-actions" aria-label={`教案 ${slotLabel} 操作`}>
            <button className="icon-button" onClick={onRefresh} title="刷新" type="button">
              <InlineIcon name="refresh" />
            </button>
            <button className="icon-button" onClick={onCopy} title="复制文本" type="button">
              <InlineIcon name="copy" />
              <span className="sr-only">{copied ? "已复制" : "复制文本"}</span>
            </button>
            <button
              className={`icon-button ${expanded ? "icon-button-active" : ""}`}
              onClick={onToggleFocus}
              title={expanded ? "恢复双栏" : `查看教案 ${slotLabel}`}
              type="button"
            >
              <InlineIcon name="maximize" />
            </button>
            <a className="icon-button" href={document.original_file} rel="noreferrer" target="_blank" title="下载原文">
              <InlineIcon name="download" />
            </a>
          </div>
        </header>

        <div className="lesson-meta-row">
          <span>{previewMode}</span>
          <span>{document.file_extension.toUpperCase()}</span>
          <span>{document.page_count ? `${document.page_count} 页` : `${document.word_count || 0} 字`}</span>
          <span>上传者 {meta.uploaderName}</span>
          {copied ? <strong>已复制</strong> : null}
        </div>

        <DocumentPreview document={document} expanded={expanded} />
      </div>
    </article>
  );
}

export function VoteBar({
  disabled,
  hasExistingReview,
  isSubmitting,
  showRubric,
  onToggleRubric
}: {
  disabled?: boolean;
  hasExistingReview: boolean;
  isSubmitting: boolean;
  showRubric: boolean;
  onToggleRubric: () => void;
}) {
  return (
    <section className="vote-bar review-action-bar" aria-label="专业评分操作">
      <p className="review-action-note">专业维度评分</p>

      <div className="vote-bar-actions">
        <button className="secondary-button" disabled={disabled || isSubmitting} onClick={onToggleRubric} type="button">
          {showRubric ? "收起评分" : "展开评分"}
        </button>
        <button className="primary-button vote-submit-button" disabled={disabled || isSubmitting} type="submit">
          {isSubmitting ? "提交中..." : hasExistingReview ? "更新评价" : "提交评价"}
        </button>
      </div>
    </section>
  );
}
