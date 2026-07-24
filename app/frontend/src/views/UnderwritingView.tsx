import { useEffect, useState } from 'react';
import { api, UnderwritingResponse, AccountSummary, AccountDetail, money } from '../api';
import { ErrorNote, Loading } from '../components/ui';

type Scope = 'submission' | 'account' | 'team' | 'enterprise';
const SCOPES: { id: Scope; label: string; sub: string }[] = [
  { id: 'submission', label: '1 · Submission', sub: 'one agentic decision' },
  { id: 'account', label: '2 · Account', sub: 'the customer, whole' },
  { id: 'team', label: '3 · Team', sub: 'the portfolio, live' },
  { id: 'enterprise', label: '4 · Enterprise', sub: 'where the number flows' },
];

const DECISION_TONE: Record<string, string> = {
  ACCEPT: 'ok',
  DECLINE: 'bad',
  REFER: 'warn',
};

function fmtPremium(by: Record<string, number>): string {
  const parts = Object.entries(by).map(([c, v]) => money(v, c));
  return parts.length ? parts.join(' + ') : '—';
}

export default function UnderwritingView() {
  const [scope, setScope] = useState<Scope>('submission');
  const [data, setData] = useState<UnderwritingResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const ccy = 'GBP';

  // account scope (lazy)
  const [accounts, setAccounts] = useState<AccountSummary[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<AccountDetail | null>(null);

  useEffect(() => {
    setErr(null);
    api.underwriting(ccy).then(setData).catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    if (scope === 'account' && accounts === null) {
      api.accounts().then((d) => setAccounts(d.accounts)).catch(() => setAccounts([]));
    }
  }, [scope, accounts]);

  useEffect(() => {
    if (selected) {
      setDetail(null);
      api.account(selected).then(setDetail).catch(() => setDetail(null));
    }
  }, [selected]);

  if (err) return <ErrorNote error={`Failed to load underwriting: ${err}`} />;
  if (!data) return <Loading label="Loading the underwriting workbench…" />;

  return (
    <div className="view detail underwriting">
      <div className="detail-head">
        <div className="detail-kicker">Workbench · Underwriting</div>
        <h2 className="detail-title">Submission to bound — and everywhere it flows</h2>
        <p className="detail-desc">
          Start where Anthropic starts: one agentic underwriting decision. Then
          watch the scope open up — because it happened on the layer, not in a
          spreadsheet, the same decision becomes the customer's whole account, the
          team's portfolio, and then the enterprise's numbers. Automatically. Move
          the scope →
        </p>
      </div>

      {/* the scope slider — the spine of the story */}
      <div className="uw-scope">
        {SCOPES.map((s, i) => (
          <button
            key={s.id}
            className={`uw-scope-btn ${scope === s.id ? 'active' : ''}`}
            onClick={() => setScope(s.id)}
          >
            <span className="uw-scope-label">{s.label}</span>
            <span className="uw-scope-sub">{s.sub}</span>
            {i < SCOPES.length - 1 && <span className="uw-scope-arrow">→</span>}
          </button>
        ))}
      </div>

      {/* SCOPE 1 — SUBMISSION */}
      {scope === 'submission' && (
        <section className="detail-section">
          <p className="uw-note">{data.submission.note}</p>
          <div className="uw-cards">
            {data.submission.cases.map((c) => (
              <div key={c.quote_number} className={`uw-case ${DECISION_TONE[c.decision] || ''}`}>
                <div className="uw-case-top">
                  <span className="uw-case-num mono">{c.quote_number}</span>
                  <span className={`uw-badge ${DECISION_TONE[c.decision] || ''}`}>
                    {c.decision}
                  </span>
                </div>
                <div className="uw-case-lob">{c.line_of_business}</div>
                {c.quoted_premium != null && (
                  <div className="uw-case-prem">{money(c.quoted_premium, ccy)}</div>
                )}
                <div className="uw-case-by">
                  {c.by_agent ? '🤖 decided by agent' : '👤 ' + c.decided_by}
                </div>
                <div className="uw-case-why">{c.rationale}</div>
              </div>
            ))}
          </div>
          <p className="sub">
            A machine buyer submits, <span className="mono">fn_appetite_check</span>{' '}
            decides, and the decision is a governed{' '}
            <span className="mono">underwriting_decision</span> — not a cell in a
            file. Nothing to save or re-key; it's already a fact on the layer.
          </p>
        </section>
      )}

      {/* SCOPE 2 — ACCOUNT (multipolicy customer 360) */}
      {scope === 'account' && (
        <section className="detail-section">
          <p className="uw-note">
            Because a policyholder is a <em>role</em>, not a column, one customer's
            whole relationship assembles itself — every policy across every line,
            their claims and complaints. Nobody built a customer table.
          </p>
          {accounts === null ? (
            <Loading label="Finding the multipolicy customers…" />
          ) : (
            <div className="acc-layout">
              <div className="acc-list">
                {accounts.map((a) => (
                  <button
                    key={a.party_id}
                    className={`acc-pick ${selected === a.party_id ? 'active' : ''}`}
                    onClick={() => setSelected(a.party_id)}
                  >
                    <span className="acc-pick-name">{a.name}</span>
                    <span className="acc-pick-sub">{a.policies} policies · {a.lines} lines</span>
                  </button>
                ))}
              </div>
              <div className="acc-detail">
                {!selected ? (
                  <div className="acc-empty">← Pick a customer to see their whole account.</div>
                ) : !detail ? (
                  <Loading label="Assembling the 360…" />
                ) : (
                  <>
                    <div className="acc-head">
                      <h3 className="acc-name">{detail.name}</h3>
                      <span className="acc-country">{detail.country}</span>
                    </div>
                    <div className="acc-stats">
                      <div><b>{detail.policy_count}</b> policies</div>
                      <div><b>{detail.lines.length}</b> lines</div>
                      <div><b>{detail.claim_count}</b> claims</div>
                      <div><b>{detail.complaint_count}</b> complaints</div>
                      <div className="acc-prem"><b>{fmtPremium(detail.premium_by_currency)}</b> premium</div>
                    </div>
                    <div className="acc-lines">
                      {detail.lines.map((l) => <span key={l} className="acc-line-chip">{l}</span>)}
                    </div>
                    <div className="card scroll-x acc-policies">
                      <table>
                        <thead>
                          <tr><th>Policy</th><th>Line</th><th>UW year</th><th>Status</th><th>Premium</th></tr>
                        </thead>
                        <tbody>
                          {detail.policies.slice(0, 12).map((p) => (
                            <tr key={p.policy_number}>
                              <td className="mono">{p.policy_number}</td>
                              <td>{p.line_of_business}</td>
                              <td>{p.underwriting_year ?? ''}</td>
                              <td>{p.status}</td>
                              <td className="mono">{p.premium != null ? money(p.premium, p.currency) : '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {detail.policies.length > 12 && (
                        <div className="acc-more">+ {detail.policies.length - 12} more policies</div>
                      )}
                    </div>
                    {(detail.claims.length > 0 || detail.complaints.length > 0) && (
                      <div className="acc-conduct">
                        {detail.claims.length > 0 && (
                          <div>
                            <span className="acc-conduct-h">Claims</span>
                            {detail.claims.slice(0, 5).map((c) => (
                              <div key={c.claim_number} className="acc-conduct-row">
                                <span className="mono">{c.claim_number}</span> · {c.cause} · {c.status}
                              </div>
                            ))}
                          </div>
                        )}
                        {detail.complaints.length > 0 && (
                          <div>
                            <span className="acc-conduct-h">Complaints</span>
                            {detail.complaints.map((c) => (
                              <div key={c.reference} className="acc-conduct-row">
                                <span className="mono">{c.reference}</span> · {c.category} · {c.status}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    <p className="sub">{detail.note}</p>
                  </>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {/* SCOPE 3 — TEAM */}
      {scope === 'team' && (
        <section className="detail-section">
          <p className="uw-note">{data.team.note}</p>
          <div className="uw-stats">
            <div className="uw-stat">
              <span className="uw-stat-val">{data.team.total_decisions}</span>
              <span className="uw-stat-label">decisions on the book</span>
            </div>
            <div className="uw-stat">
              <span className="uw-stat-val">
                {data.team.agent_decisions}<span className="uw-stat-slash">/{data.team.total_decisions}</span>
              </span>
              <span className="uw-stat-label">made by an agent</span>
            </div>
            <div className="uw-stat">
              <span className="uw-stat-val">
                {data.team.conversion_rate != null
                  ? `${Math.round(data.team.conversion_rate * 100)}%`
                  : '—'}
              </span>
              <span className="uw-stat-label">quote → bind conversion</span>
            </div>
          </div>

          <h3 className="detail-h3">The book, forming in real time ({ccy})</h3>
          <div className="card scroll-x">
            <table>
              <thead>
                <tr><th>Line of business</th><th>Gross written premium</th><th>Policies</th></tr>
              </thead>
              <tbody>
                {data.team.portfolio.map((p) => (
                  <tr key={p.line_of_business}>
                    <td>{p.line_of_business}</td>
                    <td className="mono">{money(p.gwp ?? 0, ccy)}</td>
                    <td className="mono">{p.policy_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="sub">
            Every underwriter's and every agent's decision rolls up the instant
            it's made — the portfolio manager sees the book build without anyone
            collating a spreadsheet. One person's judgment is now the team's picture.
          </p>
        </section>
      )}

      {/* SCOPE 3 — ENTERPRISE */}
      {scope === 'enterprise' && (
        <section className="detail-section">
          <p className="uw-note">{data.enterprise.note}</p>

          <div className="uw-flow">
            <div className="uw-flow-source">
              <span className="uw-flow-label">Underwriting — gross written premium</span>
              <span className="uw-flow-val">{money(data.enterprise.underwriting_gwp ?? 0, ccy)}</span>
              <span className="uw-flow-sub">the number the team just bound</span>
            </div>
            <div className="uw-flow-fan">↓ flows, with no re-key, to ↓</div>
            <div className="uw-flow-targets">
              <div className={`uw-flow-target ${data.enterprise.finance_reconciles ? 'ok' : 'bad'}`}>
                <span className="uw-flow-t-label">Finance close</span>
                <span className="uw-flow-t-val">{money(data.enterprise.finance_premium_income ?? 0, ccy)}</span>
                <span className="uw-flow-t-sub">
                  {data.enterprise.finance_reconciles ? '✓ reconciles to GWP, to the penny' : 'premium income posted'}
                </span>
              </div>
              <div className="uw-flow-target">
                <span className="uw-flow-t-label">Reinsurance</span>
                <span className="uw-flow-t-val">{money(data.enterprise.reinsurance_ceded ?? 0, ccy)}</span>
                <span className="uw-flow-t-sub">ceded to treaty</span>
              </div>
              <div className="uw-flow-target">
                <span className="uw-flow-t-label">Reserving</span>
                <span className="uw-flow-t-val">{money(data.enterprise.reserving_ultimate ?? 0, ccy)}</span>
                <span className="uw-flow-t-sub">
                  projected ultimate · IBNR {money(data.enterprise.reserving_ibnr ?? 0, ccy)}
                </span>
              </div>
            </div>
          </div>
          <p className="sub">
            The same premium the underwriter bound this morning is already in the
            finance close, the reinsurance programme and the reserving triangle —
            one number, many consumers, meaning intact at every hop. The spreadsheet
            is where data goes to stop. The layer is where it keeps moving.
          </p>
        </section>
      )}

      {/* ask in genie */}
      <section className="detail-section">
        <div className="rsv-genie">
          <span className="rsv-genie-q">“{data.genie_question}”</span>
          <a className="btn primary" href={data.genie_url} target="_blank" rel="noreferrer">
            Ask in Genie →
          </a>
        </div>
      </section>

      <div className="provenance">Generated from {data.provenance}</div>
    </div>
  );
}
