// Mirrors backend/app/schemas. Keep in sync (or generate from /api/openapi.json).

export type UserRole = "parent" | "health_reviewer" | "analyst" | "institution" | "admin";
export type SymptomCategory = "gastrointestinal" | "respiratory" | "fever" | "skin" | "general";
export type SignalStatus = "detected" | "under_review" | "confirmed" | "dismissed" | "resolved";
export type AlertStatus = "draft" | "pending_approval" | "approved" | "published" | "retracted";
export type AlertSeverity = "info" | "advisory" | "warning";

export interface LatLng {
  latitude: number;
  longitude: number;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  home_area_id: number | null;
}

export interface Child {
  id: number;
  display_name: string;
  date_of_birth: string;
  sex: string;
  school_id: number | null;
  area_id: number | null;
  photo_url: string | null;
  age_months: number;
  learning_interests: string[];
}

export interface Symptom {
  id: number;
  code: string;
  name: string;
  category: SymptomCategory;
}

export interface SymptomReport {
  id: number;
  child_id: number;
  symptoms: Symptom[];
  onset_date: string;
  is_ongoing: boolean;
  recovered_on: string | null;
  visited_facility: boolean;
  school_id: number | null;
  verification: "parent_observation" | "clinically_confirmed";
  notes: string | null;
  created_at: string;
}

export interface NotificationItem {
  id: number;
  kind: string;
  title: string;
  body: string;
  read_at: string | null;
  created_at: string;
}

export interface Area {
  id: number;
  code: string;
  name: string;
  level: string;
  parent_id: number | null;
  centroid: LatLng | null;
}

export interface School {
  id: number;
  name: string;
  area_id: number | null;
  location: LatLng | null;
}

export interface Facility {
  id: number;
  name: string;
  facility_type: string;
  location: LatLng | null;
  phone_number: string | null;
  opening_hours: string | null;
}

export interface Infrastructure {
  id: number;
  name: string;
  asset_type: string;
  location: LatLng | null;
  data_source: string | null;
}

export interface Overview {
  families: number;
  children: number;
  reports_total: number;
  reports_last_7_days: number;
  open_signals: number;
  published_alerts: number;
}

export interface AreaAggregate {
  area_id: number;
  area_name: string;
  centroid: LatLng | null;
  report_count: number | null;
  suppressed: boolean;
  top_category: SymptomCategory | null;
}

export interface CategoryCount {
  category: SymptomCategory;
  count: number;
}

export interface SignalPlace {
  id: number;
  name: string;
  location?: LatLng | null;
  centroid?: LatLng | null;
}

export interface InvestigationNote {
  id: number;
  author_id: number | null;
  body: string;
  status_change: string | null;
  created_at: string;
}

export interface Signal {
  id: number;
  symptom_category: SymptomCategory;
  area: SignalPlace | null;
  school: SignalPlace | null;
  window_start: string;
  window_end: string;
  report_count: number;
  baseline_count: number;
  score: number;
  status: SignalStatus;
  findings: string | null;
  detected_at: string;
  notes?: InvestigationNote[];
}

export interface Alert {
  id: number;
  title: string;
  message: string;
  severity: AlertSeverity;
  status: AlertStatus;
  signal_id: number | null;
  created_by_id: number | null;
  target_area_ids: number[];
  target_school_ids: number[];
  created_at: string;
  published_at: string | null;
}

export interface Article {
  id: number;
  slug: string;
  title: string;
  summary: string;
  category: string;
  cover_image_url: string | null;
}
