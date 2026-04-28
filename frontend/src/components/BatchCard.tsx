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
      <p className="card-description">{batch.cover_summary || "暂无批次说明。"}</p>
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
            <strong>评分汇总暂不显示</strong>
            <span>当前账号暂无查看权限</span>
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
          测评
        </Link>
      </footer>
    </article>
  );
}
