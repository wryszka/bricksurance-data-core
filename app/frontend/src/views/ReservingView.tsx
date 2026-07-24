import { useEffect, useState } from 'react';
import { api, ReservingResponse, money } from '../api';
import { ErrorNote, Loading } from '../components/ui';

const LOB_LABELS: Record<string, string> = {
  COMMERCIAL_PROPERTY: 'Commercial Property',
  MOTOR: 'Motor',
  GENERAL_LIABILITY: 'General Liability',
  MARINE_CARGO: 'Marine Cargo',
};
const METHOD_LABELS: Record<string, string> = {
  CHAIN_LADDER: 'Chain-Ladder',
  BORNHUETTER_FERGUSON: 'Bornhuetter-Ferguson',
};

// Shade a triangle cell by how developed it is (paid / latest-diagonal paid),
// so the actual upper triangle reads warm-to-cool and empty (future) cells are
// visibly blank — the classic triangle, alive.
function cellShade(frac: number): string {
  // 0 -> pale, 1 -> full teal. Kept within the house palette.
  const a = 0.12 + 0.6 * Math.max(0, Math.min(1, frac));
  return `rgba(18, 86, 110, ${a.toFixed(2)})`;
}

export default function ReservingView() {
  const [lob, setLob] = useState('COMMERCIAL_PROPERTY');
  const [ccy] = useState('GBP');
  const [method, setMethod] = useState('CHAIN_LADDER');
  const [data, setData] = useState<ReservingResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setErr(null);
    api
      .reserving(lob, ccy, method)
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        setErr(String(e));
        setLoading(false);
      });
  }, [lob, ccy, method]);

  if (err) return <ErrorNote error={`Failed to load reserving: ${err}`} />;

  // triangle lookup
  const byCell = new Map<string, number | null>();
  let years: number[] = [];
  let maxLag = 0;
  const latestByAy: Record<number, number> = {};
  if (data) {
    years = data.accident_years;
    maxLag = data.max_lag;
    data.triangle.forEach((c) => {
      byCell.set(`${c.accident_year}:${c.development_lag}`, c.cumulative_paid);
    });
    years.forEach((ay) => {
      latestByAy[ay] = data.latest_lag[String(ay)] ?? -1;
    });
  }
  const estByAy = new Map(data?.estimates.map((e) => [e.accident_year, e]) ?? []);

  return (
    <div className="view detail reserving">
      <div className="detail-head">
        <div className="detail-kicker">Workbench · Reserving</div>
        <h2 className="detail-title">Loss-development triangle</h2>
        <div className="detail-owner">
          Owned by Chief Actuary · certified · derived live from{' '}
          <span className="mono">reserving.loss_development</span>
        </div>
        <p className="detail-desc">
          The reserving workflow actuaries run in a spreadsheet — but the triangle
          is a governed view over claim transactions, it re-projects when you
          switch method, and it reconciles to the claims ledger to the penny.
          Nothing here is pasted or stored.
        </p>
      </div>

      {/* controls */}
      <div className="rsv-controls">
        <div className="rsv-seg">
          <span className="rsv-seg-label">Line of business</span>
          <div className="seg">
            {(data?.lines_available ?? Object.keys(LOB_LABELS)).map((l) => (
              <button
                key={l}
                className={`seg-btn ${lob === l ? 'active' : ''}`}
                onClick={() => setLob(l)}
              >
                {LOB_LABELS[l] ?? l}
              </button>
            ))}
          </div>
        </div>
        <div className="rsv-seg">
          <span className="rsv-seg-label">Method</span>
          <div className="seg">
            {['CHAIN_LADDER', 'BORNHUETTER_FERGUSON'].map((m) => (
              <button
                key={m}
                className={`seg-btn ${method === m ? 'active' : ''}`}
                onClick={() => setMethod(m)}
                disabled={
                  data != null && !data.methods_available.includes(m)
                }
                title={
                  data != null && !data.methods_available.includes(m)
                    ? 'Not published for this line yet'
                    : ''
                }
              >
                {METHOD_LABELS[m]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading || !data ? (
        <Loading label="Building the triangle…" />
      ) : (
        <>
          {/* reconciliation — the money shot */}
          <div className={`rsv-recon ${data.reconciliation.reconciles ? 'ok' : 'bad'}`}>
            {data.reconciliation.reconciles ? '✓' : '✗'}{' '}
            <strong>
              Triangle paid reconciles to the claims ledger
            </strong>{' '}
            — {money(data.reconciliation.triangle_paid ?? 0, ccy)} paid on the
            triangle equals {money(data.reconciliation.ledger_paid ?? 0, ccy)} in{' '}
            <span className="mono">claim.claim_transaction</span>. Derived, not
            copied — it cannot drift.
          </div>

          {/* the triangle */}
          <section className="detail-section">
            <h3 className="detail-h3">
              Cumulative paid — {LOB_LABELS[lob] ?? lob} ({ccy})
            </h3>
            <div className="card scroll-x">
              <table className="triangle">
                <thead>
                  <tr>
                    <th className="tri-corner">Accident year</th>
                    {Array.from({ length: maxLag + 1 }, (_, i) => (
                      <th key={i}>dev {i}</th>
                    ))}
                    <th className="tri-ult">
                      Ultimate<br />
                      <span className="tri-ult-sub">{METHOD_LABELS[method]}</span>
                    </th>
                    <th className="tri-ult">IBNR</th>
                  </tr>
                </thead>
                <tbody>
                  {years.map((ay) => {
                    const latest = latestByAy[ay];
                    const est = estByAy.get(ay);
                    const diag = byCell.get(`${ay}:${latest}`) ?? 0;
                    return (
                      <tr key={ay}>
                        <th className="tri-ay">{ay}</th>
                        {Array.from({ length: maxLag + 1 }, (_, lag) => {
                          const v = byCell.get(`${ay}:${lag}`);
                          const isActual = v != null && lag <= latest;
                          const frac = diag ? (v ?? 0) / diag : 0;
                          return (
                            <td
                              key={lag}
                              className={`tri-cell ${isActual ? 'actual' : 'future'}`}
                              style={
                                isActual
                                  ? { background: cellShade(frac) }
                                  : undefined
                              }
                            >
                              {isActual ? Math.round(v as number).toLocaleString() : ''}
                            </td>
                          );
                        })}
                        <td className="tri-ult mono">
                          {est ? Math.round(est.ultimate_loss ?? 0).toLocaleString() : ''}
                        </td>
                        <td className="tri-ult mono ibnr">
                          {est ? Math.round(est.ibnr ?? 0).toLocaleString() : ''}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="tri-legend">
              <span className="swatch actual" /> observed (upper triangle){'  '}
              <span className="swatch future" /> not yet developed{'  '}· ultimate
              and IBNR projected by <strong>{METHOD_LABELS[method]}</strong> — switch
              method above and watch the projection change.
            </p>
          </section>

          {/* reserve walk */}
          <section className="detail-section">
            <h3 className="detail-h3">Reserve walk ({METHOD_LABELS[method]})</h3>
            <div className="rsv-walk">
              {[
                ['Paid to date', data.reserve_walk.paid_to_date],
                ['+ Case reserves', data.reserve_walk.case_reserves],
                ['+ IBNR', data.reserve_walk.ibnr],
                ['= Ultimate loss', data.reserve_walk.ultimate_loss],
              ].map(([label, val], i) => (
                <div key={i} className={`rsv-step ${i === 3 ? 'total' : ''}`}>
                  <span className="rsv-step-label">{label as string}</span>
                  <span className="rsv-step-val mono">
                    {money(val as number, ccy)}
                  </span>
                </div>
              ))}
            </div>
            <p className="sub">
              Total outstanding (case + IBNR):{' '}
              <strong>{money(data.reserve_walk.outstanding, ccy)}</strong>. Every
              figure derives from the triangle and ties back to source; the method
              choice is recorded as a dated attestation.
            </p>
          </section>

          {/* ask in genie */}
          <section className="detail-section">
            <h3 className="detail-h3">Ask it in plain English</h3>
            <p className="sub">
              The same governed figures answer in the Reserving Genie space — no
              SQL, no spreadsheet.
            </p>
            <div className="rsv-genie">
              <span className="rsv-genie-q">“{data.genie_question}”</span>
              <a
                className="btn primary"
                href={data.genie_url}
                target="_blank"
                rel="noreferrer"
              >
                Ask in Genie →
              </a>
            </div>
          </section>

          <div className="provenance">Generated from {data.provenance}</div>
        </>
      )}
    </div>
  );
}
