import { Link } from "react-router-dom";
import { BatchListItem } from "../api/types";
import { formatScore } from "../utils/number";


const statusText: Record<BatchListItem["status"], string> = {
  processing: "解析中",
  ready: "可评价",
  failed: "解析失败",
  archived: "已归档"
};

export function BatchCard({ batch }: { batch: BatchListItem }) {
  const showSummary = batch.can_view_review_summary;

  return (
    <article className="batch-card">
      <div className="batch-card-head">
        <span className={`status-badge status-${batch.status}`}>{statusText[batch.status]}</span>
        <span className="muted-label">
          {batch.subject} · {batch.grade_level}
        </span>
      </div>
      <h3>{batch.title}</h3>
      <p className="card-description">{batch.cover_summary || "该批次未填写补充说明，评价时请重点结合原文质量与教学设计判断。"}</p>
      <div className="metric-row">
        {showSummary ? (
          <>
            <div>
              <strong>{formatScore(batch.average_total_score)}</strong>
              <span>综合均分</span>
            </div>
            <div>
              <strong>{batch.review_count ?? 0}</strong>
              <span>已提交评价</span>
            </div>
          </>
        ) : (
          <div className="metric-callout">
            <strong>匿名互评进行中</strong>
            <span>他人评分与汇总对当前用户暂不展示</span>
          </div>
        )}
        <div>
          <strong>{batch.ready_document_count}/2</strong>
          <span>已解析文档</span>
        </div>
      </div>
      <footer className="card-footer">
        <div>
          <span className="muted-label">上传人</span>
          <strong>{batch.uploader.display_name}</strong>
        </div>
        <Link className="primary-link" to={`/batches/${batch.id}`}>
          查看详情
        </Link>
      </footer>
    </article>
  );
}
