import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { BatchDetail } from "../api/types";

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
    return Object.values(value)
      .map(flattenErrorMessage)
      .filter(Boolean)
      .join("；");
  }
  return "";
}

function getUploadErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const message = flattenErrorMessage(error.response?.data);
    if (message) {
      return message;
    }
  }
  return "上传失败，请确认文件格式为 Word(docx)、PDF、TXT 或 Markdown。";
}

export function UploadPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    title: "",
    subject: "",
    grade_level: "",
    academic_year: "",
    teaching_theme: "",
    cover_summary: "",
    review_deadline: ""
  });
  const [documents, setDocuments] = useState<[File | null, File | null]>([null, null]);
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = new FormData();
      Object.entries(form).forEach(([key, value]) => {
        if (value) {
          payload.append(key, value);
        }
      });
      documents.forEach((file) => {
        if (file) {
          payload.append("documents", file);
        }
      });
      const response = await api.post<BatchDetail>("/batches/", payload, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      return response.data;
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["batches"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      navigate(`/batches/${data.id}`);
    }
  });

  const handleFileChange = (index: 0 | 1, file: File | null) => {
    setDocuments((current) => {
      const next: [File | null, File | null] = [...current] as [File | null, File | null];
      next[index] = file;
      return next;
    });
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    if (!documents[0] || !documents[1]) {
      setError("请分别上传两份教案文件。");
      return;
    }
    try {
      await mutation.mutateAsync();
    } catch (caughtError) {
      setError(getUploadErrorMessage(caughtError));
    }
  };

  return (
    <div className="panel-card">
      <div className="section-head">
        <div>
          <p className="eyebrow">Upload Pair</p>
          <h2>创建一组双教案批次</h2>
        </div>
        <p className="muted-label">系统会在上传后自动解析文档，并向全体其他用户开放评价。</p>
      </div>

      <form className="upload-form" onSubmit={handleSubmit}>
        <div className="grid-two">
          <label>
            批次标题
            <input
              value={form.title}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              placeholder="例：七年级语文《春》双版本教案对比"
              required
            />
          </label>
          <label>
            学科
            <input
              value={form.subject}
              onChange={(event) => setForm((current) => ({ ...current, subject: event.target.value }))}
              placeholder="例：语文"
              required
            />
          </label>
        </div>

        <div className="grid-two">
          <label>
            适用学段/年级
            <input
              value={form.grade_level}
              onChange={(event) => setForm((current) => ({ ...current, grade_level: event.target.value }))}
              placeholder="例：七年级"
              required
            />
          </label>
          <label>
            学年
            <input
              value={form.academic_year}
              onChange={(event) => setForm((current) => ({ ...current, academic_year: event.target.value }))}
              placeholder="例：2025-2026 学年"
            />
          </label>
        </div>

        <div className="grid-two">
          <label>
            教学主题
            <input
              value={form.teaching_theme}
              onChange={(event) => setForm((current) => ({ ...current, teaching_theme: event.target.value }))}
              placeholder="例：写景散文阅读"
            />
          </label>
          <label>
            评价截止日期
            <input
              type="date"
              value={form.review_deadline}
              onChange={(event) => setForm((current) => ({ ...current, review_deadline: event.target.value }))}
            />
          </label>
        </div>

        <label>
          批次说明
          <textarea
            rows={4}
            value={form.cover_summary}
            onChange={(event) => setForm((current) => ({ ...current, cover_summary: event.target.value }))}
            placeholder="可补充版本差异、设计意图、适用场景等，帮助评价者更准确理解。"
          />
        </label>

        <div className="grid-two">
          {[0, 1].map((index) => (
            <label className="file-dropzone" key={index}>
              <span className="muted-label">教案 {index === 0 ? "A" : "B"}</span>
              <strong>{documents[index] ? documents[index]?.name : "选择文件"}</strong>
              <p>支持 `.doc`、`.docx`、`.pdf`、`.txt`、`.md`、`.markdown`，单文件默认上限 20MB</p>
              <input
                type="file"
                accept=".doc,.docx,.pdf,.txt,.md,.markdown"
                onChange={(event) => handleFileChange(index as 0 | 1, event.target.files?.[0] ?? null)}
                required
              />
            </label>
          ))}
        </div>

        {error ? <p className="form-error">{error}</p> : null}

        <button className="primary-button" disabled={mutation.isPending} type="submit">
          {mutation.isPending ? "正在创建批次..." : "提交并开始解析"}
        </button>
      </form>
    </div>
  );
}
