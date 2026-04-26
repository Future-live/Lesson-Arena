import { PropsWithChildren } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { BatchListItem, PaginatedResponse } from "../api/types";
import { useAuth } from "../providers/AuthProvider";
import { IconName, InlineIcon } from "./InlineIcon";

const navItems: Array<{ label: string; to?: string; icon: IconName }> = [
  { label: "首页", to: "/", icon: "home" },
  { label: "上传教案", to: "/upload", icon: "upload" },
  { label: "评价任务", icon: "bookOpen" },
  { label: "数据统计", icon: "barChart" }
];

function getToolbarCopy(pathname: string) {
  if (pathname.startsWith("/batches/")) {
    return {
      title: "Lesson Battle Mode",
      subtitle: "教案对比评价",
      helper: "当前任务：综合评价"
    };
  }

  if (pathname === "/upload") {
    return {
      title: "Upload Studio",
      subtitle: "上传双教案批次",
      helper: "每批次固定上传 2 份教案"
    };
  }

  return {
    title: "Lesson Arena",
    subtitle: "教案评价工作台",
    helper: "数据看板与待评任务"
  };
}

function userInitial(name: string | undefined) {
  return (name || "U").trim().slice(0, 1).toUpperCase();
}

export function AppShell({ children }: PropsWithChildren) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const toolbar = getToolbarCopy(location.pathname);

  const sidebarBatchesQuery = useQuery({
    queryKey: ["sidebar-batches"],
    queryFn: async () =>
      (
        await api.get<PaginatedResponse<BatchListItem>>("/batches/", {
          params: { ordering: "-created_at" }
        })
      ).data
  });

  const sidebarBatches = sidebarBatchesQuery.data?.results.slice(0, 5) ?? [];

  return (
    <div className="app-shell">
      <aside className="sidebar-rail" aria-label="全局导航">
        <Link className="rail-logo" to="/" title="教案竞技场">
          <InlineIcon name="fileText" />
        </Link>

        <nav className="rail-nav">
          {navItems.map((item) =>
            item.to ? (
              <NavLink
                aria-label={item.label}
                className={({ isActive }) => `rail-link ${isActive ? "rail-link-active" : ""}`}
                end={item.to === "/"}
                key={item.label}
                title={item.label}
                to={item.to}
              >
                <InlineIcon name={item.icon} />
              </NavLink>
            ) : (
              <button
                aria-label={`${item.label}（待接入）`}
                className="rail-link rail-link-muted"
                disabled
                key={item.label}
                title={`${item.label}（待接入）`}
                type="button"
              >
                <InlineIcon name={item.icon} />
              </button>
            )
          )}
        </nav>

        <div className="rail-recents" aria-label="最近批次">
          {sidebarBatches.map((batch, index) => (
            <Link
              className={`rail-recent-dot ${location.pathname === `/batches/${batch.id}` ? "rail-recent-dot-active" : ""}`}
              key={batch.id}
              title={`${batch.title} · ${batch.subject}`}
              to={`/batches/${batch.id}`}
            >
              {index + 1}
            </Link>
          ))}
        </div>

        <div className="rail-footer">
          <button className="rail-link" onClick={logout} title="退出登录" type="button">
            <InlineIcon name="logOut" />
          </button>
        </div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div className="topbar-title">
            <div className="mode-picker">
              <InlineIcon name="menu" />
              <span>{toolbar.title}</span>
              <InlineIcon name="chevronDown" />
            </div>
            <strong>{toolbar.subtitle}</strong>
          </div>

          <div className="topbar-actions">
            <span className="metric-pill">{toolbar.helper}</span>
            <Link className="secondary-button topbar-upload" to="/upload">
              上传教案
            </Link>
            <button className="icon-button" title="更多" type="button">
              <InlineIcon name="more" />
            </button>
            <div className="user-menu" title={user?.display_name}>
              <span>{userInitial(user?.display_name)}</span>
              <strong>{user?.display_name || "用户"}</strong>
            </div>
          </div>
        </header>

        <main className="content-panel">{children}</main>
      </div>
    </div>
  );
}
