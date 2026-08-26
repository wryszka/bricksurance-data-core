import { useEffect, useState } from 'react';
import { api, EventPolicy, ClaimEventResult, money } from '../api';
import { ErrorNote, Loading } from '../components/ui';

export default function LiveEventView() {
  const [policies, setPolicies] = useState<EventPolicy[] | null>(null);
  const [policy, setPolicy] = useState<string>('');
  const [amount, setAmount] = useState<number>(5000000);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<ClaimEventResult | null>(null);

  useEffect(() => {
    api.eventPolicies().then((d) => {
      setPolicies(d.policies);
      const ceded = d.policies.find((p) => p.ceded);
      setPolicy((ceded || d.policies[0])?.policy_number || '');
    }).catch((e) => setErr(String(e)));
  }, []);

  const fire = () => {
    setBusy(true); setErr(null); setResult(null);
    api.recordClaim({
      policy_number: policy, reserve_amount: amount,
      cause_of_loss_code: 'FIRE', loss_date: '2026-08-01',
      description: 'Catastrophic loss recorded via the interactive spine.',
    }).then((r) => { setResult(r); setBusy(false); })
      .catch((e) => { setErr(String(e)); setBusy(false); });
  };

  const reset = () => {
    setBusy(true);
    api.resetEvents().then(() => { setResult(null); setBusy(false); })
      .catch((e) => { setErr(String(e)); setBusy(false); });
  };

  const cur = result?.currency || 'GBP';
  const sel = policies?.find((p) => p.policy_number === policy);

  return (
    <div className="view detail liveevent">
      <div className="detail-head">
        <div className="detail-kicker">Interactive spine · one event, whole estate</div>
        <h2 className="detail-title">Record a claim, watch it ripple</h2>
        <p className="detail-desc">
          The base data layer is live. Record a large claim against a real policy
          and it moves claims, reserving, finance and reinsurance <em>at once</em> —
          nothing updated per-domain. The reserving triangle, loss ratio, IBNR and
          the ledger all recompute as views over the one governed event.
        </p>
      </div>

      {err && <ErrorNote error={err} />}

      {/* controls */}
      <div className="le-controls card">
        <div className="le-field">
          <label>Policy</label>
          <select value={policy} onChange={(e) => setPolicy(e.target.value)} disabled={busy}>
            {(policies || []).map((p) => (
              <option key={p.policy_number} value={p.policy_number}>
                {p.policy_number} · {p.line_of_business}{p.ceded ? ' · ceded ✓' : ''}
              </option>
            ))}
          </select>
          {sel?.ceded && <span className="le-hint">ceded — reinsurance will respond too</span>}
        </div>
        <div className="le-field">
          <label>Reserve amount ({cur})</label>
          <input type="number" value={amount} step={500000}
                 onChange={(e) => setAmount(Number(e.target.value))} disabled={busy} />
        </div>
        <button className="btn primary le-fire" onClick={fire} disabled={busy || !policy}>
          {busy ? 'Recording…' : 'Record the claim →'}
        </button>
        {result && (
          <button className="btn ghost" onClick={reset} disabled={busy}>Reset</button>
        )}
      </div>

      {busy && !result && <Loading label="Recording the event and letting it ripple…" />}

      {result && (
        <>
          <div className="le-headline">
            Recorded <span className="mono">{result.claim_number}</span> —{' '}
            {money(result.reserve_amount, cur)} reserve on {result.policy_number}{' '}
            ({result.line_of_business}).
          </div>

          {/* the ripple across four domains */}
          <div className="le-ripple">
            <div className="le-domain">
              <div className="le-domain-h">Claims</div>
              <div className="le-metric">
                <span>Incurred</span>
                <span className="le-delta up">+{money(result.ripple.claims_incurred_delta, cur)}</span>
              </div>
              <div className="le-was">{money(result.before.claims_incurred, cur)} → {money(result.after.claims_incurred, cur)}</div>
            </div>
            <div className="le-domain">
              <div className="le-domain-h">Reserving</div>
              <div className="le-metric">
                <span>Outstanding</span>
                <span className="le-delta up">+{money(result.ripple.outstanding_reserve_delta, cur)}</span>
              </div>
              <div className="le-metric">
                <span>Loss ratio</span>
                <span className="le-delta up">{result.ripple.loss_ratio_before.toFixed(3)} → {result.ripple.loss_ratio_after.toFixed(3)}</span>
              </div>
              <div className="le-was">triangle &amp; IBNR recompute as views</div>
            </div>
            <div className="le-domain">
              <div className="le-domain-h">Finance</div>
              <div className="le-metric">
                <span>GL journal</span>
                <span className={`le-delta ${result.ripple.trial_balance_still_zero ? 'ok' : 'bad'}`}>
                  posted
                </span>
              </div>
              <div className="le-was">
                trial balance {result.ripple.trial_balance_still_zero ? '✓ still 0.00' : money(result.ripple.trial_balance_after, cur)}
              </div>
            </div>
            <div className={`le-domain ${result.ceded ? '' : 'muted'}`}>
              <div className="le-domain-h">Reinsurance</div>
              {result.ceded ? (
                <>
                  <div className="le-metric">
                    <span>Recovery</span>
                    <span className="le-delta ok">{money(result.reinsurance_recovery || 0, cur)}</span>
                  </div>
                  <div className="le-was">
                    {Math.round((result.ceded_share || 0) * 100)}% quota share · {result.treaty_reference}
                  </div>
                </>
              ) : (
                <div className="le-was">policy not ceded — no recovery</div>
              )}
            </div>
          </div>

          <p className="sub">{result.note}</p>
          <div className="provenance">
            Written to claim.claim / claim_transaction + finance.journal(_line); all
            metrics are views. Reset removes live events (source_system = LIVE_EVENT).
          </div>
        </>
      )}
    </div>
  );
}
