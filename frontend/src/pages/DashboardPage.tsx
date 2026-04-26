import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { BatchListItem, DashboardStats, PaginatedResponse } from "../api/types";
import { BatchCard } from "../components/BatchCard";
import { StatCard } from "../components/StatCard";
import { formatScore } from "../utils/number";


export function DashboardPage() {
  const dashboardQuery = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get<DashboardStats>("/system/dashboard/")).data
  });

  const pendingQuery = useQuery({
    queryKey: ["batches", "pending-review"],
    queryFn: async () =>
      (await api.get<PaginatedResponse<BatchListItem>>("/batches/", { params: { scope: "pending_review" } })).data
  });

  const myUploadsQuery = useQuery({
    queryKey: ["batches", "mine"],
    queryFn: async () =>
      (await api.get<PaginatedResponse<BatchListItem>>("/batches/", { params: { scope: "mine" } })).data
  });

  if (dashboardQuery.isLoading || pendingQuery.isLoading || myUploadsQuery.isLoading) {
    return <div className="panel-card">正在加载工作台数据...</div>;
  }

  const overview = dashboardQuery.data?.overview;
  const canViewGlobalRankings = dashboardQuery.data?.can_view_global_rankings ?? false;
  const pendingResults = pendingQuery.data?.results ?? [];
  const myUploads = myUploadsQuery.data?.results ?? [];

  return (
    <div className="dashboard-space">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">System Overview</p>
          <h2>围绕“上传两份教案并由全员评价”的完整教研闭环</h2>
          <p>
            仪表盘会同时追踪上传进度、待评任务、均分走势和高分教案，帮助你把日常教研从“资料散落”拉回到可管理的系统流程。
          </p>
        </div>
        <div className="hero-score">
          <span>我的上传均分</span>
          <strong>{formatScore(overview?.my_upload_average_score)}</strong>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard label="总批次数" value={overview?.total_batches ?? 0} helper="系统中所有双教案批次" />
        <StatCard label="可评价批次" value={overview?.ready_batches ?? 0} helper="解析完成并开放互评" />
        <StatCard label="待我评价" value={overview?.pending_review_count ?? 0} helper="尚未完成的互评任务" />
        <StatCard label="我的上传" value={overview?.my_upload_count ?? 0} helper="本人提交的教案组数量" />
      </section>

      <section className="dashboard-columns">
        <div className="panel-card">
          <div className="section-head">
            <div>
              <p className="eyebrow">Pending</p>
              <h3>待我评价的教案组</h3>
            </div>
            <span className="muted-label">{pendingResults.length} 个批次</span>
          </div>
          <div className="card-list">
            {pendingResults.length ? (
              pendingResults.map((item) => <BatchCard key={item.id} batch={item} />)
            ) : (
              <p className="empty-state">当前没有待你评价的教案组，可以先上传新的双教案批次。</p>
            )}
          </div>
        </div>

        <div className="panel-card">
          <div className="section-head">
            <div>
              <p className="eyebrow">My Uploads</p>
              <h3>我的上传批次</h3>
            </div>
          </div>
          <div className="card-list">
            {myUploads.length ? (
              myUploads.map((item) => <BatchCard key={item.id} batch={item} />)
            ) : (
              <p className="empty-state">你还没有上传过批次，现在可以直接创建第一组双教案。</p>
            )}
          </div>
        </div>
      </section>

      <section className="dashboard-columns">
        <div className="panel-card">
          <div className="section-head">
            <div>
              <p className="eyebrow">Recent</p>
              <h3>{canViewGlobalRankings ? "最近开放评价的批次" : "我的最近上传"}</h3>
            </div>
            {!canViewGlobalRankings ? (
              <span className="muted-label">普通用户仅展示自己的上传批次</span>
            ) : null}
          </div>
          <div className="rank-list">
            {(dashboardQuery.data?.latest_batches ?? []).map((item) => (
              <div className="rank-row" key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.subject} · {item.grade_level || "未设置年级"}</p>
                </div>
                <span>{formatScore(item.average_total_score)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel-card">
          <div className="section-head">
            <div>
              <p className="eyebrow">Top Rated</p>
              <h3>{canViewGlobalRankings ? "高分批次" : "我的高评分批次"}</h3>
            </div>
          </div>
          <div className="rank-list">
            {(dashboardQuery.data?.high_score_batches ?? []).map((item) => (
              <div className="rank-row" key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.review_count} 条评价</p>
                </div>
                <span>{formatScore(item.average_total_score)}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
