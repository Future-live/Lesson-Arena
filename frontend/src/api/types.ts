export interface User {
  id: number;
  username: string;
  email: string;
  display_name: string;
  role: string;
  organization: string;
  title: string;
  bio: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface DashboardOverview {
  total_batches: number;
  ready_batches: number;
  my_upload_count: number;
  my_review_count: number;
  pending_review_count: number;
  my_upload_average_score: number;
}

export interface DashboardBatchItem {
  id: string;
  title: string;
  subject: string;
  grade_level?: string;
  average_total_score: number | string | null;
  review_count: number | null;
  uploader_name?: string;
}

export interface DashboardStats {
  overview: DashboardOverview;
  can_view_global_rankings: boolean;
  latest_batches: DashboardBatchItem[];
  high_score_batches: DashboardBatchItem[];
  recommendation_totals: Record<string, number>;
}

export interface BatchUploader {
  id: number;
  username: string;
  display_name: string;
  organization: string;
  title: string;
}

export interface LessonPlanDocument {
  id: string;
  slot_number: number;
  title: string;
  original_file: string;
  original_filename: string;
  file_extension: string;
  file_size: number;
  parse_status: "pending" | "processing" | "ready" | "failed";
  display_mode: "html" | "pdf";
  preview_file: string | null;
  preview_url: string | null;
  rendered_html: string;
  extracted_text: string;
  parse_error: string;
  page_count: number;
  word_count: number;
}

export interface ReviewDimensionDefinition {
  key: string;
  label: string;
  description: string;
  weight: number;
}

export interface ReviewDimensionScore {
  dimension_key: string;
  dimension_name: string;
  weight: number;
  score: number;
  score_a: number;
  score_b: number;
  comment: string;
}

export interface Review {
  id: string;
  reviewer: number;
  reviewer_name: string;
  total_score: number;
  total_score_a: number;
  total_score_b: number;
  recommendation: string;
  overall_comment: string;
  comparative_comment: string;
  strengths: string;
  improvement_suggestions: string;
  submitted_at: string;
  dimension_scores: ReviewDimensionScore[];
}

export interface ReviewSummary {
  review_count: number;
  average_total_score: number;
  recommendation_distribution: Record<string, number>;
  dimension_averages: Array<{
    key: string;
    label: string;
    weight: number;
    average_score: number;
    average_score_a: number;
    average_score_b: number;
  }>;
  recent_reviews: Array<{
    id: string;
    reviewer_name: string;
    recommendation: string;
    total_score: number;
    total_score_a: number;
    total_score_b: number;
    submitted_at: string;
  }>;
}

export interface BatchListItem {
  id: string;
  title: string;
  subject: string;
  grade_level: string;
  academic_year: string;
  teaching_theme: string;
  cover_summary: string;
  review_deadline: string | null;
  status: "processing" | "ready" | "failed" | "archived";
  ready_document_count: number;
  review_count: number | null;
  average_total_score: number | string | null;
  created_at: string;
  uploader: BatchUploader;
  can_current_user_review: boolean;
  current_user_reviewed: boolean;
  can_view_review_summary: boolean;
}

export interface BatchDetail extends BatchListItem {
  documents: LessonPlanDocument[];
  review_summary: ReviewSummary | null;
  current_user_review: Review | null;
}
