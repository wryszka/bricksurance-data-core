// Thin typed client over the FastAPI backend.

export interface Attribute {
  attribute: string;
  type: string;
  required: boolean;
  definition: string;
  classification: string | null;
  acord_ref: string | null;
  lloyds_cdr_ref: string | null;
}
export interface Entity {
  name: string;
  type: string;
  comment: string;
  attributes: Attribute[];
}
export interface Domain {
  domain: string;
  title: string;
  schema: string;
  entities: Entity[];
}
export interface ModelResponse {
  domains: Domain[];
  model_repo_url: string;
}

export interface MetricsResponse {
  currency: string;
  underwriting_year: number | null;
  currencies: string[];
  years: number[];
  kpis: {
    gross_written_premium: number;
    claims_incurred: number;
    outstanding_reserve: number;
    loss_ratio: number;
    policy_count: number;
    claim_count: number;
  };
  definitions: Record<string, string>;
  by_line_of_business: {
    line_of_business: string;
    gross_written_premium: number;
    claims_incurred: number;
  }[];
  genie_space_url: string;
}

export interface OutboundResponse {
  columns: string[];
  rows: Record<string, string | null>[];
  travels: { attribute: string; type: string; definition: string; classification: string | null }[];
  share_objects: { schema: string; name: string; type: string }[];
  share_name: string;
}

export interface MapResponse {
  mapping_notes: Record<string, string>;
  records: Record<string, any>[];
  errors: string[];
  valid: boolean;
  contract: { attribute: string; type: string; required: boolean; definition: string }[];
}

export interface LoadResponse {
  row_count: number;
  gross_premium_total: number;
}

export interface NetworkNode {
  id: string;
  label: string;
  sub: string;
  platform: string;
  status: 'live' | 'pending' | 'planned';
}
export interface NetworkResponse {
  share_name: string;
  share_live: boolean;
  share_detail: string;
  nodes: NetworkNode[];
}

// ---------------------------------------------------------------------------
// Atlas types (frozen contract — app/API_CONTRACT.md)
// ---------------------------------------------------------------------------

export type AtlasKind = 'metric' | 'entity' | 'code_set' | 'function' | 'view';
export type Certification = 'certified' | 'draft' | string;

export interface MetaResponse {
  name: string;
  title: string;
  version: string;
  standards_basis: string;
  counts: {
    domains: number;
    entities: number;
    code_sets: number;
    metric_views: number;
    functions: number;
    relationships: number;
  };
  domains: { name: string; description: string }[];
  provenance: { version: string; source: string };
}

export interface SearchResult {
  kind: AtlasKind;
  name: string;
  title: string;
  domain: string;
  score: number;
  summary: string;
  owner?: string;
  certification?: Certification;
  measure_names?: string[];
}
export interface SearchResponse {
  query: string;
  roadmap: null | { term: string; note: string };
  results: SearchResult[];
}

export interface MetricJoin {
  name: string;
  source: string;
  condition: string;
}
export interface MetricMember {
  name: string;
  expr: string;
  description: string;
}
export interface FeedsFrom {
  ref: string;
  role: string;
  entity: string;
  exists: boolean;
  join_name?: string;
}
export interface MetricResponse {
  name: string;
  title: string;
  domain: string;
  description: string;
  owner: string;
  certification: Certification;
  source: string;
  joins: MetricJoin[];
  dimensions: MetricMember[];
  measures: MetricMember[];
  feeds_from: FeedsFrom[];
  genie_question: string;
  genie_space_url: string;
}

export interface EntityAttribute {
  name: string;
  type: string;
  required: boolean;
  description: string;
  classification: string | null;
  standards?: Record<string, string> | null;
}
export interface EntityReference {
  attribute: string;
  to: string;
  to_kind: string;
}
export interface EntityQuality {
  name: string;
  rule: string;
  description: string;
}
export interface EntityResponse {
  name: string;
  title: string;
  domain: string;
  description: string;
  grain: string;
  owner: string;
  standards?: Record<string, string> | null;
  tags: { maturity?: string } | null;
  attributes: EntityAttribute[];
  keys: { primary: string[]; natural?: string[] | null };
  quality?: EntityQuality[] | null;
  references: EntityReference[];
  referenced_by: { from: string; attribute: string }[];
}

export interface CodeSetResponse {
  name: string;
  title: string;
  description: string;
  codes: { code: string; label: string; description: string }[];
}

export interface FunctionResponse {
  name: string;
  title: string;
  domain: string;
  description: string;
  inputs: { name: string; type: string }[] | string[] | string;
  returns: string;
  sql: string;
}

export interface LineageNode {
  id: string;
  kind: string;
  name: string;
  label: string;
  domain: string;
  certification?: Certification;
  owner?: string;
}
export interface LineageEdge {
  source: string;
  target: string;
  label: string;
}
export interface LineageResponse {
  center: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
  narrative?: string;
}

export interface GovernanceResponse {
  entities: {
    total: number;
    certified: number;
    draft: number;
    with_owner: number;
    with_standards: number;
    with_quality: number;
  };
  metrics: { total: number; certified: number; draft: number; with_owner: number };
  attributes: {
    total: number;
    classification: {
      internal?: number;
      confidential?: number;
      pii?: number;
      unassessed?: number;
    };
    unassessed: number;
  };
  ownership_board: {
    owner: string;
    count: number;
    elements: { name: string; domain: string; certification: Certification }[];
  }[];
  attestations: {
    element: string;
    element_kind: string;
    certification: Certification;
    owner: string;
    attested_by: string;
    attested_on: string;
    evidence: string;
  }[];
}

export interface RegulatoryResponse {
  regime: string;
  title: string;
  blurb: string;
  consumed_by: string;
  resolved: {
    kind: AtlasKind;
    name: string;
    title: string;
    domain: string;
    owner?: string;
    certification?: Certification;
  }[];
}

export interface ProveResponse {
  metric: string;
  ok: boolean;
  error: string | null;
  sql: string;
  measures: { name: string; value: number | null; formula: string }[];
  genie_question: string;
  genie_space_url: string;
}

export interface GenieHealthResponse {
  warehouse: 'warm' | 'cold';
  genie_space_url: string;
  ready: boolean;
  detail?: string;
}

export interface GovernanceAction {
  action_id: string;
  action_type: 'proposal' | 'issue';
  element: string;
  element_kind: string;
  field?: string;
  current_value?: string;
  proposed_value?: string;
  rationale: string;
  raised_by: string;
  raised_on: string;
  status: string;
  spec_diff?: string;
}
export interface GovernanceActionsResponse {
  actions: GovernanceAction[];
  error?: string;
}
export interface ProposeBody {
  element: string;
  element_kind: 'entity' | 'metric' | 'attribute';
  field: string;
  proposed_value: string;
  rationale: string;
  raised_by: string;
  current_value: string;
}
export interface ProposeResponse {
  action_id: string;
  status: string;
  spec_diff: string;
  note: string;
}
export interface IssueBody {
  element: string;
  element_kind: string;
  rationale: string;
  raised_by: string;
}
export interface IssueResponse {
  action_id: string;
  status: string;
}

async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export interface TriangleCell {
  accident_year: number;
  development_lag: number;
  cumulative_paid: number | null;
  cumulative_incurred: number | null;
}
export interface ReserveEstimate {
  accident_year: number;
  paid_to_date: number | null;
  case_reserves: number | null;
  ultimate_loss: number | null;
  ibnr: number | null;
  outstanding: number | null;
}
export interface ReservingResponse {
  line_of_business: string;
  currency: string;
  method: string;
  methods_available: string[];
  lines_available: string[];
  accident_years: number[];
  max_lag: number;
  latest_lag: Record<string, number>;
  triangle: TriangleCell[];
  estimates: ReserveEstimate[];
  reserve_walk: {
    paid_to_date: number;
    case_reserves: number;
    ibnr: number;
    ultimate_loss: number;
    outstanding: number;
  };
  reconciliation: {
    triangle_paid: number | null;
    ledger_paid: number | null;
    reconciles: boolean;
  };
  genie_url: string;
  genie_question: string;
  provenance: string;
}

export interface UnderwritingResponse {
  currency: string;
  submission: {
    cases: {
      quote_number: string;
      line_of_business: string;
      quoted_premium: number | null;
      quote_status: string;
      decision: string;
      by_agent: boolean;
      decided_by: string;
      rationale: string;
    }[];
    note: string;
  };
  team: {
    total_decisions: number;
    agent_decisions: number;
    human_decisions: number;
    decisions: { decision: string; by_agent: boolean; count: number }[];
    converted: number;
    total_quotes: number;
    conversion_rate: number | null;
    portfolio: { line_of_business: string; gwp: number | null; policy_count: number }[];
    note: string;
  };
  enterprise: {
    underwriting_gwp: number | null;
    finance_premium_income: number | null;
    finance_reconciles: boolean;
    reinsurance_ceded: number | null;
    reserving_ultimate: number | null;
    reserving_ibnr: number | null;
    note: string;
  };
  genie_url: string;
  genie_question: string;
  provenance: string;
}

export interface NarrationModel {
  id: string;
  label: string;
  tier: string;
  note: string;
}
export interface ModelSwapResponse {
  model: string;
  model_label: string;
  fact: {
    quote_number: string;
    line_of_business: string;
    quoted_premium: number | null;
    decision: string;
    decided_by: string;
    by_agent: boolean;
    rationale: string;
    decided_by_engine: string;
  };
  decision_source: string;
  narration: string | null;
  narration_error: string | null;
  narration_note?: string;
  contract: string;
}

export interface AccountSummary {
  party_id: string;
  name: string;
  policies: number;
  lines: number;
}
export interface AccountDetail {
  party_id: string;
  name: string;
  country: string;
  lines: string[];
  policy_count: number;
  claim_count: number;
  complaint_count: number;
  premium_by_currency: Record<string, number>;
  policies: {
    policy_number: string; line_of_business: string; status: string;
    underwriting_year: number | null; currency: string; premium: number | null;
  }[];
  claims: { claim_number: string; status: string; cause: string; loss_date: string | null }[];
  complaints: { reference: string; category: string; status: string }[];
  note: string;
  provenance: string;
}

export interface ReinsuranceResponse {
  programme: {
    treaties: { reference: string; type: string; line_of_business: string; cession_rate: number | null; currency: string }[];
    layers: { treaty: string; layer: number; limit: number | null; attachment: number | null }[];
    submissions: { status: string; count: number }[];
    note: string;
  };
  accumulation: {
    events: { event: string; peril: string; date: string | null; gross_loss: number | null; ceded_recovery: number | null; net_retained: number; loss_rows: number }[];
    note: string;
  };
  exchange: {
    outbound_rows: number; outbound_gross: number | null; outbound_ceded: number | null;
    received_rows: number | null; received_ceded: number | null;
    exchange_live: boolean; reconciles: boolean; note: string;
  };
  genie_url: string;
  genie_question: string;
  provenance: string;
}

export interface EventPolicy {
  policy_number: string;
  line_of_business: string;
  currency: string;
  ceded: boolean;
}
export interface ClaimEventResult {
  claim_number: string;
  policy_number: string;
  line_of_business: string;
  currency: string;
  reserve_amount: number;
  ceded: boolean;
  ceded_share: number | null;
  treaty_reference: string | null;
  reinsurance_recovery: number | null;
  before: Record<string, number>;
  after: Record<string, number>;
  ripple: {
    claims_incurred_delta: number;
    outstanding_reserve_delta: number;
    loss_ratio_before: number;
    loss_ratio_after: number;
    trial_balance_after: number;
    trial_balance_still_zero: boolean;
  };
  note: string;
}

export const api = {
  model: () => getJSON<ModelResponse>('/api/model'),
  metrics: (currency: string, year?: number | null) =>
    getJSON<MetricsResponse>(
      `/api/metrics?currency=${encodeURIComponent(currency)}` +
        (year ? `&underwriting_year=${year}` : ''),
    ),
  outbound: () => getJSON<OutboundResponse>('/api/exchange/outbound'),
  sample: () => getJSON<{ filename: string; content: string }>('/api/exchange/sample'),
  network: () => getJSON<NetworkResponse>('/api/network'),
  mapContent: async (content: string): Promise<MapResponse> => {
    const fd = new FormData();
    fd.append('content', content);
    const r = await fetch('/api/exchange/map', { method: 'POST', body: fd });
    if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
    return r.json();
  },
  mapFile: async (file: File): Promise<MapResponse> => {
    const fd = new FormData();
    fd.append('file', file);
    const r = await fetch('/api/exchange/map', { method: 'POST', body: fd });
    if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
    return r.json();
  },
  load: async (records: Record<string, any>[]): Promise<LoadResponse> => {
    const r = await fetch('/api/exchange/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ records }),
    });
    if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
    return r.json();
  },

  // ---- Atlas -----------------------------------------------------------
  meta: () => getJSON<MetaResponse>('/api/atlas/meta'),
  search: (q: string, limit = 30) =>
    getJSON<SearchResponse>(
      `/api/atlas/search?q=${encodeURIComponent(q)}&limit=${limit}`,
    ),
  metric: (name: string) =>
    getJSON<MetricResponse>(`/api/atlas/metric/${encodeURIComponent(name)}`),
  entity: (name: string) =>
    getJSON<EntityResponse>(`/api/atlas/entity/${encodeURIComponent(name)}`),
  codeSet: (name: string) =>
    getJSON<CodeSetResponse>(`/api/atlas/code_set/${encodeURIComponent(name)}`),
  atlasFunction: (name: string) =>
    getJSON<FunctionResponse>(`/api/atlas/function/${encodeURIComponent(name)}`),
  lineage: (kind: string, name: string, depth = 1) =>
    getJSON<LineageResponse>(
      `/api/atlas/lineage/${encodeURIComponent(kind)}/${encodeURIComponent(
        name,
      )}?depth=${depth}`,
    ),
  goldenThread: () => getJSON<LineageResponse>('/api/atlas/golden-thread'),
  governance: () => getJSON<GovernanceResponse>('/api/atlas/governance'),
  regulatory: (regime: string) =>
    getJSON<RegulatoryResponse>(
      `/api/atlas/regulatory/${encodeURIComponent(regime)}`,
    ),
  prove: (name: string) =>
    getJSON<ProveResponse>(`/api/atlas/prove/${encodeURIComponent(name)}`),
  genieHealth: () => getJSON<GenieHealthResponse>('/api/atlas/genie-health'),
  reserving: (lob: string, currency: string, method: string) =>
    getJSON<ReservingResponse>(
      `/api/atlas/reserving?line_of_business=${encodeURIComponent(lob)}` +
        `&currency=${encodeURIComponent(currency)}&method=${encodeURIComponent(method)}`,
    ),
  underwriting: (currency: string) =>
    getJSON<UnderwritingResponse>(
      `/api/atlas/underwriting?currency=${encodeURIComponent(currency)}`,
    ),
  modelSwapConfig: () =>
    getJSON<{ models: NarrationModel[] }>('/api/atlas/model-swap/config'),
  modelSwap: (model: string) =>
    getJSON<ModelSwapResponse>(
      `/api/atlas/model-swap?model=${encodeURIComponent(model)}`,
    ),
  accounts: () => getJSON<{ accounts: AccountSummary[] }>('/api/atlas/accounts'),
  account: (partyId: string) =>
    getJSON<AccountDetail>(`/api/atlas/account/${encodeURIComponent(partyId)}`),
  reinsurance: () => getJSON<ReinsuranceResponse>('/api/atlas/reinsurance'),
  eventPolicies: () => getJSON<{ policies: EventPolicy[] }>('/api/atlas/event/policies'),
  recordClaim: async (body: {
    policy_number: string; reserve_amount: number;
    cause_of_loss_code?: string; loss_date?: string; description?: string;
  }): Promise<ClaimEventResult> => {
    const r = await fetch('/api/atlas/event/record-claim', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
    return r.json();
  },
  resetEvents: async (): Promise<{ reset: boolean }> => {
    const r = await fetch('/api/atlas/event/reset', { method: 'POST' });
    if (!r.ok) throw new Error(r.statusText);
    return r.json();
  },
  governanceActions: () =>
    getJSON<GovernanceActionsResponse>('/api/atlas/governance/actions'),
  propose: async (body: ProposeBody): Promise<ProposeResponse> => {
    const r = await fetch('/api/atlas/governance/propose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
    return r.json();
  },
  raiseIssue: async (body: IssueBody): Promise<IssueResponse> => {
    const r = await fetch('/api/atlas/governance/issue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
    return r.json();
  },
};

export function num(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  const abs = Math.abs(n);
  const opts: Intl.NumberFormatOptions =
    abs > 0 && abs < 10 && !Number.isInteger(n)
      ? { maximumFractionDigits: 4 }
      : { maximumFractionDigits: 0 };
  return new Intl.NumberFormat('en-GB', opts).format(n);
}

export function money(n: number, currency: string): string {
  try {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(n);
  } catch {
    return `${currency} ${n.toLocaleString()}`;
  }
}
