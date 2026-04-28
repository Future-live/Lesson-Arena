import { FormEvent, useState } from "react";
import { isAxiosError } from "axios";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../providers/AuthProvider";

function flattenErrorMessage(value: unknown): string {
  if (!value) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(flattenErrorMessage).filter(Boolean).join("；");
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([field, detail]) => {
        const message = flattenErrorMessage(detail);
        return message ? `${field}: ${message}` : "";
      })
      .filter(Boolean)
      .join("；");
  }
  return "";
}

function getRegisterErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const message = flattenErrorMessage(error.response?.data);
    if (message) {
      return message;
    }
  }
  return "注册失败，请确认信息完整且用户名/邮箱未被占用。";
}

export function RegisterPage() {
  const { isAuthenticated, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    display_name: "",
    password: "",
    password_confirm: "",
    organization: "",
    title: "",
    role: "teacher"
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await register(form);
      navigate("/", { replace: true });
    } catch (caughtError) {
      setError(getRegisterErrorMessage(caughtError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <section className="auth-hero">
        <p className="eyebrow">用户注册</p>
        <h1>教师账号注册</h1>
        <p>请填写账号信息完成注册。</p>
      </section>

      <form className="auth-card register-card" onSubmit={handleSubmit}>
        <h2>注册账号</h2>
        <div className="grid-two">
          <label>
            用户名
            <input
              value={form.username}
              onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
              required
            />
          </label>
          <label>
            显示名称
            <input
              value={form.display_name}
              onChange={(event) => setForm((current) => ({ ...current, display_name: event.target.value }))}
              required
            />
          </label>
        </div>
        <div className="grid-two">
          <label>
            邮箱
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              required
            />
          </label>
          <label>
            角色
            <select
              value={form.role}
              onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}
            >
              <option value="teacher">教师</option>
              <option value="reviewer">评价成员</option>
            </select>
          </label>
        </div>
        <div className="grid-two">
          <label>
            学校/单位
            <input
              value={form.organization}
              onChange={(event) => setForm((current) => ({ ...current, organization: event.target.value }))}
            />
          </label>
          <label>
            职称/岗位
            <input
              value={form.title}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            />
          </label>
        </div>
        <div className="grid-two">
          <label>
            密码
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              required
            />
          </label>
          <label>
            确认密码
            <input
              type="password"
              value={form.password_confirm}
              onChange={(event) => setForm((current) => ({ ...current, password_confirm: event.target.value }))}
              required
            />
          </label>
        </div>
        {error ? <p className="form-error">{error}</p> : null}
        <button className="primary-button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "注册中..." : "创建并进入系统"}
        </button>
        <p className="auth-footer">
          已有账号？<Link to="/login">返回登录</Link>
        </p>
      </form>
    </div>
  );
}
