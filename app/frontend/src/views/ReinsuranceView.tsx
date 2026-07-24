import { useEffect, useState } from 'react';
import { api, ReinsuranceResponse, money } from '../api';
import { ErrorNote, Loading } from '../components/ui';

type Lens = 'programme' | 'accumulation' | 'exchange';
const LENSES: { id: Lens; label: string; sub: string }[] = [
  { id: 'programme', label: 'Programme', sub: 'what we bought' },
  { id: 'accumulation', label: 'Accumulation & recovery', sub: 'when a cat hits' },
  { id: 'exchange', label: 'Exchange', sub: 'the bordereau, killed' },
];

export default function ReinsuranceView() {
  const [lens, setLens] = useState<Lens>('programme');
  const [data, setData] = useState<ReinsuranceResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.reinsurance().then(setData).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <ErrorNote error={`Failed to load reinsurance: ${err}`} />;
  if (!data) return <Loading label="Loading the reinsurance workbench…" />;

  const ex = data.exchange;

  return (
    <div className="view detail reinsurance-wb">
      <div className="detail-head">
        <div className="detail-kicker">Workbench · Reinsurance</div>
        <h2 className="detail-title">The programme, the recovery, and the bordereau — governed</h2>
        <p className="detail-desc">
          The protection we bought, what it pays when a catastrophe hits, and the
          cession bordereau that reaches our reinsurer — as a governed view that
          reconciles to the penny, not a spreadsheet emailed and re-keyed.
        </p>
      </div>

      <div className="uw-scope">
        {LENSES.map((l, i) => (
          <button key={l.id} className={`uw-scope-btn ${lens === l.id ? 'active' : ''}`} onClick={() => setLens(l.id)}>
            <span className="uw-scope-label">{l.label}</span>
            <span className="uw-scope-sub">{l.sub}</span>
            {i < LENSES.length - 1 && <span className="uw-scope-arrow">→</span>}
          </button>
        ))}
      </div>

      {/* PROGRAMME */}
      {lens === 'programme' && (
        <section className="detail-section">
          <p className="uw-note">{data.programme.note}</p>
          <div className="card scroll-x">
            <table>
              <thead><tr><th>Treaty</th><th>Type</th><th>Line</th><th>Cession / layers</th></tr></thead>
              <tbody>
                {data.programme.treaties.map((t) => {
                  const layers = data.programme.layers.filter((l) => l.treaty === t.reference);
                  return (
                    <tr key={t.reference}>
                      <td className="mono">{t.reference}</td>
                      <td>{t.type}</td>
                      <td>{t.line_of_business}</td>
                      <td>
                        {t.cession_rate != null
                          ? `${Math.round(t.cession_rate * 100)}% quota share`
                          : layers.map((l) => `L${l.layer}: ${money(l.limit ?? 0, t.currency)} xs ${money(l.attachment ?? 0, t.currency)}`).join('  ·  ')}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <h3 className="detail-h3">Inward submission funnel</h3>
          <div className="ri-funnel">
            {data.programme.submissions.map((s) => (
              <div key={s.status} className="ri-funnel-step">
                <span className="ri-funnel-n">{s.count}</span>
                <span className="ri-funnel-l">{s.status.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ACCUMULATION & RECOVERY */}
      {lens === 'accumulation' && (
        <section className="detail-section">
          <p className="uw-note">{data.accumulation.note}</p>
          <div className="ri-events">
            {data.accumulation.events.map((e) => {
              const pierced = (e.ceded_recovery ?? 0) > 0;
              return (
                <div key={e.event} className={`ri-event ${pierced ? 'pierced' : ''}`}>
                  <div className="ri-event-top">
                    <span className="ri-event-name">{e.event}</span>
                    <span className="ri-event-peril">{e.peril} · {e.date}</span>
                  </div>
                  <div className="ri-event-bar">
                    <div className="ri-bar-ceded"
                         style={{ width: `${Math.round(100 * (e.ceded_recovery ?? 0) / (e.gross_loss || 1))}%` }} />
                  </div>
                  <div className="ri-event-nums">
                    <span>Gross <b>{money(e.gross_loss ?? 0, 'GBP')}</b></span>
                    <span className="ceded">Reinsurance recovery <b>{money(e.ceded_recovery ?? 0, 'GBP')}</b></span>
                    <span>Net retained <b>{money(e.net_retained, 'GBP')}</b></span>
                  </div>
                </div>
              );
            })}
          </div>
          <p className="sub">
            The recovery is derived from the same event losses that build the gross
            — where the loss pierces the excess-of-loss attachment, the layer pays.
            No separate recoverables spreadsheet to reconcile.
          </p>
        </section>
      )}

      {/* EXCHANGE — the punchline */}
      {lens === 'exchange' && (
        <section className="detail-section">
          <p className="uw-note">{ex.note}</p>
          <div className="ri-exchange">
            <div className="ri-ex-side">
              <div className="ri-ex-who">Bricksurance SE — cedant</div>
              <div className="ri-ex-label">Outbound cession bordereau</div>
              <div className="ri-ex-val">{ex.outbound_ceded != null ? money(ex.outbound_ceded, 'GBP') : '—'}</div>
              <div className="ri-ex-sub">{ex.outbound_rows} lines · a governed view, derived live</div>
            </div>
            <div className={`ri-ex-link ${ex.reconciles ? 'ok' : ''}`}>
              {ex.exchange_live ? (ex.reconciles ? '= reconciles =' : '≠') : '→ shares to →'}
            </div>
            <div className="ri-ex-side">
              <div className="ri-ex-who">Bricksurance Re — reinsurer</div>
              <div className="ri-ex-label">Received bordereau</div>
              <div className="ri-ex-val">
                {ex.received_ceded != null ? money(ex.received_ceded, 'GBP') : '(pending share)'}
              </div>
              <div className="ri-ex-sub">
                {ex.exchange_live ? `${ex.received_rows} lines · with the data dictionary attached` : 'run the local exchange or Delta Share'}
              </div>
            </div>
          </div>
          {ex.reconciles && (
            <div className="rsv-recon ok">
              ✓ <strong>Penny-identical, no reconciliation step.</strong> The cedant and
              the reinsurer read one governed definition — no bordereau spreadsheet,
              no middleware, no “which number?” call. The meaning travels with the data.
            </div>
          )}
        </section>
      )}

      <section className="detail-section">
        <div className="rsv-genie">
          <span className="rsv-genie-q">“{data.genie_question}”</span>
          <a className="btn primary" href={data.genie_url} target="_blank" rel="noreferrer">Ask in Genie →</a>
        </div>
      </section>

      <div className="provenance">Generated from {data.provenance}</div>
    </div>
  );
}
