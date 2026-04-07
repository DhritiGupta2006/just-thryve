/**
 * Centralized API client for Just-Thryve / GreenFlowCredit.
 *
 * Reads the backend base URL from VITE_API_URL (falls back to
 * http://localhost:8000 for local development).
 *
 * JWT token is persisted in localStorage under the key `greenflow_token`.
 * Every request that requires authentication attaches it via the
 * `Authorization: Bearer <token>` header automatically.
 */

// API_URL is injected at build time via vite.config.ts `define`.
// The `declare` makes TypeScript aware of this build-time global without @types/node.
declare const process: { env: Record<string, string | undefined> } | undefined;
const BASE_URL =
  (typeof process !== "undefined" && process?.env?.API_URL) ||
  "http://localhost:8000";

const TOKEN_KEY = "greenflow_token";

// ---------------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------------

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean; // default true – attach Bearer token
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true } = opts;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (auth) {
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      detail = errorBody.detail ?? detail;
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(response.status, detail);
  }

  // 204 No Content → return empty object
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Types mirroring backend schemas
// ---------------------------------------------------------------------------

export interface TokenResponse {
  user_id: string;
  token: string;
  role: string;
}

export interface UserResponse {
  user_id: string;
  email: string;
  name: string;
  role: string;
  kyc_verified: boolean;
  created_at: string;
}

export interface SignupPayload {
  email: string;
  password: string;
  name: string;
  role: string; // "borrower" | "lender"
  business_name?: string;
  sector?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ProfileUpdatePayload {
  name?: string;
  business_name?: string;
  sector?: string;
}

export interface LoanApplyPayload {
  amount_requested: number;
  purpose: string;
  tenure_months: number;
}

export interface LoanResponse {
  loan_id: string;
  borrower_id: string;
  amount_requested: number;
  purpose: string;
  tenure_months: number;
  status: string;
  approved_amount?: number;
  approved_rate?: number;
  emi_amount?: number;
  risk_score?: number;
  ml_decision?: string;
  created_at: string;
  submitted_at?: string;
  disbursed_at?: string;
  closed_at?: string;
}

export interface OfferResponse {
  id: string;
  loan_id: string;
  lender_id: string;
  interest_rate: number;
  offered_amount: number;
  tenure_months: number;
  emi_amount: number;
  status: string;
  accepted_at?: string;
  expires_at: string;
  created_at: string;
}

export interface RepaymentScheduleItem {
  id: string;
  loan_id: string;
  installment_number: number;
  due_date: string;
  principal_amount: number;
  interest_amount: number;
  emi_amount: number;
  status: string;
  paid_on?: string;
}

export interface AuditLogEntry {
  id: string;
  loan_id: string;
  model_version: string;
  input_features: Record<string, unknown>;
  prediction_score: number;
  shap_values?: Record<string, unknown>;
  decision: string;
  confidence?: number;
  created_at: string;
}

export interface ConsentGrantPayload {
  loan_id: string;
  consent_types: string[];
}

export interface ESGMetricsResponse {
  renewable_energy_percent: number;
  carbon_intensity: number;
  compliance_score: number;
  waste_recycled_percent: number;
  social_impact_score: number;
}

export interface LoanSummary {
  loan_id: string;
  status: string;
  amount_requested: number;
  approved_amount?: number;
  emi_amount?: number;
  risk_score?: number;
  ml_decision?: string;
  created_at: string;
}

export interface OfferSummary {
  offer_id: string;
  loan_id: string;
  status: string;
  offered_amount: number;
  interest_rate: number;
  tenure_months: number;
  emi_amount: number;
  created_at: string;
}

export interface BorrowerDashboardResponse {
  loan_count: number;
  active_loan_count: number;
  total_requested: number;
  total_approved: number;
  total_repaid: number;
  next_emi_date?: string;
  next_emi_amount?: number;
  loans: LoanSummary[];
}

export interface LenderDashboardResponse {
  offer_count: number;
  accepted_offer_count: number;
  portfolio_value: number;
  average_interest_rate?: number;
  offers: OfferSummary[];
}

export interface NotificationItem {
  id: string;
  title: string;
  description: string;
  category: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------

export const authApi = {
  signup(payload: SignupPayload): Promise<TokenResponse> {
    return request<TokenResponse>("/auth/signup", {
      method: "POST",
      body: payload,
      auth: false,
    });
  },

  login(payload: LoginPayload): Promise<TokenResponse> {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: payload,
      auth: false,
    });
  },

  me(): Promise<UserResponse> {
    return request<UserResponse>("/auth/me");
  },

  updateProfile(payload: ProfileUpdatePayload): Promise<UserResponse> {
    return request<UserResponse>("/auth/profile", {
      method: "PUT",
      body: payload,
    });
  },
};

// ---------------------------------------------------------------------------
// Loan endpoints
// ---------------------------------------------------------------------------

export const loansApi = {
  apply(payload: LoanApplyPayload): Promise<{ loan_id: string; status: string }> {
    return request("/loans/apply", { method: "POST", body: payload });
  },

  list(params?: { status?: string; limit?: number; offset?: number }): Promise<LoanResponse[]> {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.limit !== undefined) qs.set("limit", String(params.limit));
    if (params?.offset !== undefined) qs.set("offset", String(params.offset));
    const query = qs.toString() ? `?${qs}` : "";
    return request<LoanResponse[]>(`/loans${query}`);
  },

  get(loanId: string): Promise<LoanResponse> {
    return request<LoanResponse>(`/loans/${loanId}`);
  },

  submit(loanId: string): Promise<Record<string, unknown>> {
    return request(`/loans/${loanId}/submit`, { method: "POST" });
  },

  acceptOffer(loanId: string, offerId: string): Promise<Record<string, unknown>> {
    return request(`/loans/${loanId}/accept-offer/${offerId}`, { method: "POST" });
  },

  disburse(loanId: string): Promise<Record<string, unknown>> {
    return request(`/loans/${loanId}/disburse`, { method: "POST" });
  },
};

// ---------------------------------------------------------------------------
// Offers endpoints
// ---------------------------------------------------------------------------

export const offersApi = {
  list(loanId: string): Promise<OfferResponse[]> {
    return request<OfferResponse[]>(`/offers?loan_id=${encodeURIComponent(loanId)}`);
  },

  create(payload: {
    loan_id: string;
    interest_rate: number;
    offered_amount: number;
    tenure_months: number;
  }): Promise<{ offer_id: string }> {
    return request("/offers", { method: "POST", body: payload });
  },
};

// ---------------------------------------------------------------------------
// Repayment endpoints
// ---------------------------------------------------------------------------

export const repaymentApi = {
  schedule(loanId: string): Promise<RepaymentScheduleItem[]> {
    return request<RepaymentScheduleItem[]>(
      `/repayment/schedule?loan_id=${encodeURIComponent(loanId)}`,
    );
  },

  pay(payload: {
    loan_id: string;
    amount: number;
    mandate_id: string;
  }): Promise<{ transaction_id: string; status: string }> {
    return request("/repayment/pay", { method: "POST", body: payload });
  },
};

// ---------------------------------------------------------------------------
// Consent endpoints
// ---------------------------------------------------------------------------

export const consentApi = {
  grant(payload: ConsentGrantPayload): Promise<unknown[]> {
    return request("/consent/grant", { method: "POST", body: payload });
  },

  status(consentId: string): Promise<unknown> {
    return request(`/consent/${consentId}/status`);
  },
};

// ---------------------------------------------------------------------------
// Audit log endpoints
// ---------------------------------------------------------------------------

export const auditLogsApi = {
  list(params?: {
    loan_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<AuditLogEntry[]> {
    const qs = new URLSearchParams();
    if (params?.loan_id) qs.set("loan_id", params.loan_id);
    if (params?.limit !== undefined) qs.set("limit", String(params.limit));
    if (params?.offset !== undefined) qs.set("offset", String(params.offset));
    const query = qs.toString() ? `?${qs}` : "";
    return request<AuditLogEntry[]>(`/audit-logs${query}`);
  },

  get(logId: string): Promise<AuditLogEntry> {
    return request<AuditLogEntry>(`/audit-logs/${logId}`);
  },
};

// ---------------------------------------------------------------------------
// ESG endpoints
// ---------------------------------------------------------------------------

export const esgApi = {
  metrics(): Promise<ESGMetricsResponse> {
    return request<ESGMetricsResponse>("/esg/metrics");
  },
};

// ---------------------------------------------------------------------------
// Dashboard endpoints
// ---------------------------------------------------------------------------

export const dashboardApi = {
  borrower(): Promise<BorrowerDashboardResponse> {
    return request<BorrowerDashboardResponse>("/dashboard/borrower");
  },

  lender(): Promise<LenderDashboardResponse> {
    return request<LenderDashboardResponse>("/dashboard/lender");
  },
};

// ---------------------------------------------------------------------------
// Notifications endpoints
// ---------------------------------------------------------------------------

export const notificationsApi = {
  list(): Promise<NotificationItem[]> {
    return request<NotificationItem[]>("/notifications");
  },
};
