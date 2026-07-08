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

async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
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
};

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
