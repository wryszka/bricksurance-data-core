import { useEffect, useState } from 'react';
import { api, MetricsResponse, money } from '../api';
import PurposeCard from './PurposeCard';
import { DOCS } from '../docs';

const KPI_DEFS: { key: keyof MetricsResponse['kpis']; label: string; defKey: string; kind: 'money' | 'ratio' | 'count' }[] = [
  { key: 'gross_written_premium', label: 'Gross written premium', defKey: 'gross_written_premium', kind: 'money' },
  { key: 'claims_incurred', label: 'Claims incurred', defKey: 'claims_incurred', kind: 'money' },
  { key: 'outstanding_reserve', label: 'Outstanding reserve', defKey: 'outstanding_reserve', kind: 'money' },
  { key: 'loss_ratio', label: 'Loss ratio', defKey: 'loss_ratio', kind: 'ratio' },
  { key: 'policy_count', label: 'Policy count', defKey: 'policy_count', kind: 'count' },
  { key: 'claim_count', label: 'Claim count', defKey: 'claim_count', kind: 'count' },
];

export default function NumbersTab() {
  const [currency, setCurrency] = useState('GBP');
  const [year, setYear] = useState<number | null>(null);
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .metrics(currency, year)
      .then((d) => {
        setData(d);
        setErr(null);
      })
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [currency, year]);

  if (err) return <div className="result-note err">Failed to load metrics: {err}</div>;

  const maxVal = data
    ? Math.max(
        1,
        ...data.by_line_of_business.flatMap((l) => [l.gross_written_premium, l.claims_incurred]),
      )
    : 1;

  return (
    <>
      <PurposeCard
        seeing="KPIs served by Unity Catalog metric views — each figure carries its business definition."
        matters="One definition of every measure, for humans, dashboards and LLM agents alike."
        links={[DOCS.metrics, DOCS.genieCatalog, DOCS.agentPlaybook]}
      />
      <h2 className="section">Numbers — the semantic layer in action</h2>
      <p className="sub">
        Certified underwriting metrics. Amounts are per-currency; pick a currency before
        reading money.
      </p>

      <div className="controls">
        <div className="control">
          <label>Currency</label>
          <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
            {(data?.currencies ?? ['GBP']).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="control">
          <label>Underwriting year</label>
          <select
            value={year ?? ''}
            onChange={(e) => setYear(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">All years</option>
            {(data?.years ?? []).map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
        {data && (
          <a className="btn accent" href={data.genie_space_url} target="_blank" rel="noreferrer">
            Ask Genie ↗
          </a>
        )}
      </div>

      {loading || !data ? (
        <div className="loading">Computing measures…</div>
      ) : (
        <>
          <div className="kpis">
            {KPI_DEFS.map((k) => {
              const v = data.kpis[k.key];
              const display =
                k.kind === 'money'
                  ? money(v, currency)
                  : k.kind === 'ratio'
                    ? `${(v * 100).toFixed(1)}%`
                    : v.toLocaleString();
              return (
                <div key={k.key} className="card kpi">
                  <div className="k-label">
                    {k.label}
                    <span className="info" title={data.definitions[k.defKey] || ''}>
                      i
                    </span>
                  </div>
                  <div className="k-value">{display}</div>
                </div>
              );
            })}
          </div>

          <div className="card" style={{ padding: '16px 20px' }}>
            <h3 style={{ margin: '0 0 2px', fontSize: 15 }}>
              Premium and claims by line of business
            </h3>
            <div className="legend">
              <span>
                <span className="sw" style={{ background: 'var(--teal)' }} />
                Gross written premium
              </span>
              <span>
                <span className="sw" style={{ background: 'var(--accent)' }} />
                Claims incurred
              </span>
            </div>
            {data.by_line_of_business.map((l) => (
              <div className="chart-row" key={l.line_of_business}>
                <div className="chart-label">{l.line_of_business}</div>
                <div className="bars">
                  <div
                    className="bar gwp"
                    style={{ width: `${(l.gross_written_premium / maxVal) * 100}%` }}
                    title={`GWP ${money(l.gross_written_premium, currency)}`}
                  />
                  <div
                    className="bar inc"
                    style={{ width: `${(l.claims_incurred / maxVal) * 100}%` }}
                    title={`Incurred ${money(l.claims_incurred, currency)}`}
                  />
                </div>
                <div className="chart-val">
                  {money(l.gross_written_premium, currency)}
                </div>
              </div>
            ))}
            {data.by_line_of_business.length === 0 && (
              <div className="loading">No activity for this selection.</div>
            )}
          </div>
        </>
      )}
    </>
  );
}
