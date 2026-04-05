import api from './api';

export type Gender = 'male' | 'female' | 'other';
export type ActivityLevel = 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  age: number;
  gender: Gender;
  height_cm: number;
  weight_kg: number;
  diseases: string[];
  medications: string[];
  injuries: string[];
  activity_level: ActivityLevel;
  exercise_days_per_month: number;
  goal_lose_weight: boolean;
  goal_build_muscle: boolean;
  goal_endurance: boolean;
  mood?: string;
  motivation_text?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
}

export interface TrainingPlanResponse {
  id: number;
  week_number: number;
  risk_level: string;
  sentiment_label: string;
  recommended_intensity: string;
  weekly_plan: Record<string, unknown>;
  warnings: string[];
  motivational_message: string;
  medical_guidelines: string[];
  created_at: string;
}

export interface UserProfileResponse {
  id: number;
  name: string;
  email: string;
  age: number;
  gender: string;
  weight_kg: number;
  height_cm: number;
  diseases: string[];
  activity_level: string;
  latest_plan: TrainingPlanResponse | null;
  total_plans: number;
  total_checkins: number;
}

export interface CheckinPayload {
  sessions_completed: number;
  avg_energy_level: number;
  avg_pain_level: number;
  weight_kg?: number;
  mood_text?: string;
  feedback_text?: string;
  current_heart_rate?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  sleep_hours?: number;
  daily_steps?: number;
}

export interface CheckinResponse {
  checkin_id: number;
  week_number: number;
  new_plan: TrainingPlanResponse;
  progress_summary: string;
}

export interface AdminOverviewResponse {
  total_users: number;
  total_clients: number;
  total_admins: number;
  total_plans: number;
  total_checkins: number;
  risk_levels: { label: string; count: number }[];
  activity_levels: { label: string; count: number }[];
}

export interface DiseaseMatrixPoint {
  disease: string;
  segment: string;
  count: number;
}

export async function registerClient(payload: RegisterPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/register', payload);
  return data;
}

export async function loginClient(email: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/login', { email, password });
  return data;
}

export async function getMyProfile(): Promise<UserProfileResponse> {
  const { data } = await api.get<UserProfileResponse>('/profile/me');
  return data;
}

export async function getMyPlans(): Promise<TrainingPlanResponse[]> {
  const { data } = await api.get<TrainingPlanResponse[]>('/profile/plans');
  return data;
}

export async function submitCheckin(payload: CheckinPayload): Promise<CheckinResponse> {
  const { data } = await api.post<CheckinResponse>('/checkin', payload);
  return data;
}

export async function getAdminOverview(): Promise<AdminOverviewResponse> {
  const { data } = await api.get<AdminOverviewResponse>('/admin/overview');
  return data;
}

export async function getAdminDiseaseRisk(): Promise<DiseaseMatrixPoint[]> {
  const { data } = await api.get<DiseaseMatrixPoint[]>('/admin/analytics/disease-risk');
  return data;
}

export async function getAdminDiseaseActivity(): Promise<DiseaseMatrixPoint[]> {
  const { data } = await api.get<DiseaseMatrixPoint[]>('/admin/analytics/disease-activity');
  return data;
}

export async function getAdminDiseaseRegion(): Promise<DiseaseMatrixPoint[]> {
  const { data } = await api.get<DiseaseMatrixPoint[]>('/admin/analytics/disease-region');
  return data;
}
