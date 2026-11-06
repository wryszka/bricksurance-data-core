import { useCallback, useEffect, useState } from 'react';
import { href, navigate } from '../useHashRoute';
import '../one-number.css';

// "Motor" — the second context-demo chapter. One executive question, three
// disconnected systems, an AI with and without the mapped governed layer, the
// evidence behind each driver, and two competing definitions. Same house style
// and components as One Number; depth only behind "Explore".

interface Definition { version: number; status: string; name: string; definition_text: string; approved_by: string | null; approved_at: string | null }
interface Measures {
  earned_premium: number; written_premium: number; incurred_claims: number; loss_ratio: number; claims_paid: number;
  case_reserves: number; ibnr: number; recoveries: number; claims_handling_costs: number; claim_count: number;
  vehicle_years: number; claims_operations_ratio: number; per_100_vy?: number; severity?: number;
}
interface Headline { q2: Measures; q3: Measures; delta_points: number; incurred_growth: number; earned_growth: number }
interface Segment { code: string; label: string; q2: Measures; q3: Measures; contribution: number; share: number; delta_points: number }
interface Col { source: string | null; attribute: string; note: string }
interface Ext { name: string; source: string | null; definition: string }
interface Table { source: string; concept: string | null; conformed_view: string | null; grain: string; description: string; columns: Col[]; extensions: Ext[] }
interface System { system: string; title: string; schema: string; owner: string | null; certification: string | null; description: string; tables: Table[] }
interface CrossRow { concept: string; attribute: string; systems: Record<string, { source: string; note: string }> }
interface Legacy { name: string; formula: string; where: string; answers: string; not: string; q2: number; q3: number }
interface SecondRow { accident_quarter: string; motor_segment: string; earned_premium: number; incurred_claims: number; loss_ratio: number; claim_count: number }
interface Second {
  name: string; loaded: boolean; error?: string; mappings: string[]; systems?: string[]; mapped_columns?: number;
  segments?: SecondRow[]; totals?: Record<string, { earned_premium: number; incurred_claims: number; loss_ratio: number }>;
}
interface State {
  question: string; follow_ups: { key: string; question: string }[]; valuation_date: string; approved: Definition;
  headline: Headline; segments: Segment[]; definitions: { approved: { q2: number; q3: number }; legacy: Legacy };
  systems: System[]; crosswalk: CrossRow[]; second_insurer: Second | null; spaces: { raw: string; governed: string }; host: string;
}
interface Pivot extends Record<string, unknown> { q2: Partial<Measures>; q3: Partial<Measures> }
interface Evidence {
  regions: (Pivot & { region_name: string; delta_points: number; extra_incurred: number })[];
  theft: (Pivot & { motor_segment_code: string })[];
  repair: (Pivot & { motor_segment_code: string })[];
  large: (Pivot & { large_loss_flag: string | boolean })[];
  freq_sev: (Pivot & { motor_segment_code: string; motor_segment: string })[];
  perils: (Pivot & { peril_code: string })[];
}
interface Answer { question: string; text: string[] | string; sql: string | null; columns: string[]; rows: (string | null)[][]; seconds: number; citations?: { title?: string; asset_type?: string; identifier?: string }[] }
interface AskResult { answers: Answer[]; explain: string[]; live: boolean; note?: string }

async function call<T>(url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, body === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  if (!r.ok) {
    let msg = await r.text();
    try { msg = JSON.parse(msg).detail || msg; } catch { /* plain text */ }
    throw new Error(msg);
  }
  return r.json();
}

const pct = (v: number | null | undefined, d = 1) => (v === null || v === undefined || Number.isNaN(v) ? '—' : `${(v * 100).toFixed(d)}%`);
const pts = (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(1)} pts`;
const m = (v: number | undefined) => (v === undefined ? '—' : `£${(v / 1e6).toFixed(1)}m`);
const gbp = (v: number | undefined) => (v === undefined ? '—' : v >= 1e6 ? `£${(v / 1e6).toFixed(2)}m` : `£${Math.round(v).toLocaleString('en-GB')}`);
const n0 = (v: number | undefined) => (v === undefined ? '—' : Math.round(v).toLocaleString('en-GB'));
const stripMd = (s: string) => s.replace(/\*\*/g, '').replace(/#+\s/g, '');
const textOf = (a: Answer) => (Array.isArray(a.text) ? a.text.join('\n\n') : a.text || '');

const BEATS = [
  { key: 'question', title: 'The question' },
  { key: 'no-context', title: 'AI without context' },
  { key: 'answer', title: 'The answer' },
  { key: 'drilldown', title: 'Drill down' },
  { key: 'two-numbers', title: 'Two numbers, two questions' },
  { key: 'how', title: 'How it got there' },
];

const SYSTEM_WORDS: Record<string, string> = { PAS_MOTOR: 'Policy administration', CLM_MOTOR: 'Claims management', ACT_DW: 'Actuarial warehouse' };

function Explain({ seeing, matters }: { seeing: string; matters: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="on-explain">
      <button className="on-link" onClick={() => setOpen(!open)}>{open ? '▾' : '▸'} What am I seeing?</button>
      {open && (
        <div className="on-explain-body">
          <p><strong>What you’re seeing.</strong> {seeing}</p>
          <p><strong>Why it matters.</strong> {matters}</p>
        </div>
      )}
    </div>
  );
}

function Explore({ children, label = 'Explore — how it works' }: { children: React.ReactNode; label?: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="on-explore">
      <button className="on-link" onClick={() => setOpen(!open)}>{open ? '▾' : '⚙'} {label}</button>
      {open && <div className="on-explore-body">{children}</div>}
    </div>
  );
}

function AnswerCard({ a, i, governed }: { a: Answer; i: number; governed: boolean }) {
  const said = stripMd(textOf(a));
  const answered = Boolean(said.trim()) && !/cannot|can't|unable|no data|not available/i.test(said.slice(0, 160));
  return (
    <div className={`on-answer ${governed ? 'good' : answered ? 'bad' : 'none'}`}>
      <div className="on-answer-head">Attempt {i + 1} · {a.seconds}s</div>
      <div className="on-answer-num" style={{ fontSize: '1.1rem' }}>{answered ? (governed ? 'Answered from the governed layer' : 'Answered, confidently') : 'No answer'}</div>
      <div className="on-answer-said">“{said.length > 260 ? said.slice(0, 260) + '…' : said}”</div>
    </div>
  );
}

function Asker({ space, question, label, times = 1, compact = false }: {
  space: 'raw' | 'governed' | 'one'; question: string; label: string; times?: number; compact?: boolean;
}) {
  const [res, setRes] = useState<AskResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const go = async (live: boolean) => {
    setBusy(true); setErr(null); setRes(null); setElapsed(0);
    const t0 = Date.now();
    const timer = setInterval(() => setElapsed(Math.round((Date.now() - t0) / 1000)), 500);
    try {
      setRes(await call<AskResult>('/api/motor/ask', { space, question, times, live }));
    } catch (e) {
      setErr(String((e as Error).message));
    } finally {
      clearInterval(timer); setBusy(false);
    }
  };
  const governed = space !== 'raw';
  return (
    <div className="on-asker">
      <div className="on-q">“{question}”</div>
      <div className="btn-row">
        <button className={`btn primary ${compact ? '' : 'on-big'}`} disabled={busy} onClick={() => go(true)}>
          {busy ? `Asking… ${elapsed}s` : label}
        </button>
        <button className="btn ghost" disabled={busy} onClick={() => go(false)}>Show saved answer</button>
      </div>
      {err && <div className="result-note err">{err}</div>}
      {res && (
        <>
          {!res.live && <div className="on-note">{res.note || 'Saved answer from a verified earlier run.'}</div>}
          {times > 1 ? (
            <div className="on-answers">{res.answers.map((a, i) => <AnswerCard key={i} a={a} i={i} governed={governed} />)}</div>
          ) : (
            <div className={`on-did ${governed ? 'good' : 'bad'}`}>
              <div className="on-did-head">{space === 'one' ? 'Genie One, workspace-wide' : governed ? 'The assistant’s answer' : 'What it said'} · {res.answers[0]?.seconds}s</div>
              <div style={{ whiteSpace: 'pre-wrap' }}>{stripMd(textOf(res.answers[0]))}</div>
              {res.answers[0]?.citations && res.answers[0].citations!.length > 0 && (
                <div className="on-small">Cited: {res.answers[0].citations!.map((c) => `${c.asset_type || ''} ${c.title || c.identifier || ''}`.trim()).join(' · ')}</div>
              )}
            </div>
          )}
          {res.explain?.length > 0 && (
            <div className={`on-did ${governed ? 'good' : 'bad'}`}>
              <div className="on-did-head">{governed ? 'What it did' : 'What it actually added up'}</div>
              <ul>{res.explain.map((x, i) => <li key={i}>{x}</li>)}</ul>
            </div>
          )}
          <Explore>
            {res.answers.map((a, i) => (
              <div key={i} className="on-tech">
                <div className="on-tech-head">Attempt {i + 1} · {a.seconds}s · the query the assistant wrote</div>
                <pre className="sql-code">{a.sql || '(no query)'}</pre>
                {a.rows?.length > 0 && (
                  <table className="on-table"><thead><tr>{a.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                    <tbody>{a.rows.slice(0, 8).map((r, j) => <tr key={j}>{r.map((v, k) => <td key={k}>{v}</td>)}</tr>)}</tbody></table>
                )}
              </div>
            ))}
          </Explore>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- beats

function sameThing(s: State) {
  const want = ['policy.policy_id', 'claim.policy_id', 'premium_earning.policy_id'];
  const names: Record<string, string> = {};
  for (const r of s.crosswalk) {
    const key = `${r.concept}.${r.attribute}`;
    if (want.includes(key)) for (const [sys, v] of Object.entries(r.systems)) names[sys] = v.source;
  }
  return names;
}

function BeatQuestion({ s }: { s: State }) {
  const same = sameThing(s);
  return (
    <div className="on-hero">
      <div className="on-kicker">Monday, 9:10am. The Chief Underwriting Officer’s quarterly review is at 11.</div>
      <div className="on-hero-q">“{s.question}”</div>
      <p className="on-lede">
        The answer lives in three systems that have never agreed on a word. The policy system has a <em>contract</em>;
        the claims system has a <em>policy no</em>; the actuaries have a <em>pol ref</em>. Same thing, three names, and
        nothing that says so.
      </p>
      <div className="on-three">
        {s.systems.map((sys) => (
          <div key={sys.system} className="on-card">
            <div className="on-card-tag">{SYSTEM_WORDS[sys.system] || sys.system}</div>
            <div className="on-card-title">{sys.tables.length} tables · schema {sys.schema}</div>
            <ul className="on-small">
              {sys.tables.map((t) => <li key={t.source}><code>{t.source}</code> — {t.grain}</li>)}
            </ul>
            <div className="on-card-foot">says <strong>{same[sys.system] ? same[sys.system].split('.')[1] : '…'}</strong> for the policy</div>
          </div>
        ))}
      </div>
      <Explain
        seeing="Three real-shaped extracts: a policy administration system, a claims management system and an actuarial warehouse. Ten tables, three vocabularies, no shared definitions."
        matters="The problem is not missing data. Every number the CUO needs is in there. The problem is meaning: nothing tells a person, or an AI, that contract_reference, policy_no and pol_ref are the same policy, or which loss ratio is the company’s."
      />
    </div>
  );
}

function BeatNoContext({ s }: { s: State }) {
  return (
    <div>
      <h2 className="on-h2">Point an AI at the ten tables. Ask it three times.</h2>
      <p className="on-lede">No definitions, no mappings, no instructions. Just the data.</p>
      <Asker space="raw" question={s.question} label="Ask it three times" times={3} />
      <Explain
        seeing="The same question asked three times of an assistant that sees only the raw source tables. Under each attempt, what it actually added up, in plain English, checked against the query it wrote."
        matters="Without the business layer it has to guess what a loss ratio is, which premium to divide by, how claims join to policies and which quarter is ‘this quarter’. A confident guess is worse than no answer in a board pack."
      />
    </div>
  );
}

function Bar({ share, label, value }: { share: number; label: string; value: string }) {
  return (
    <div className="on-bridge-row">
      <div className="on-bridge-label">{label}</div>
      <div className="on-bridge-track"><div className="on-bridge-bar" style={{ width: `${Math.max(2, Math.round(share * 100))}%` }} /></div>
      <div className="on-bridge-val">{value}</div>
    </div>
  );
}

function BeatAnswer({ s }: { s: State }) {
  const h = s.headline;
  return (
    <div>
      <h2 className="on-h2">Same question. Now the AI has the mapped, governed layer.</h2>
      <div className="on-split">
        <div className="on-split-col"><div className="on-split-label">Last quarter (Q2 2026)</div><div className="on-split-num">{pct(h.q2.loss_ratio)}</div><div className="on-split-sub">{m(h.q2.incurred_claims)} incurred on {m(h.q2.earned_premium)} earned</div></div>
        <div className="on-arrow">→</div>
        <div className="on-split-col"><div className="on-split-label">This quarter (Q3 2026)</div><div className="on-split-num">{pct(h.q3.loss_ratio)}</div><div className="on-split-sub">{m(h.q3.incurred_claims)} incurred on {m(h.q3.earned_premium)} earned</div></div>
      </div>
      <p className="on-punch">
        <strong>{pts(h.delta_points)}.</strong> Incurred claims up {pct(h.incurred_growth)}; earned premium up only {pct(h.earned_growth)}.
      </p>
      <table className="on-table">
        <thead><tr><th>Segment</th><th>Q2 loss ratio</th><th>Q3 loss ratio</th><th>Change</th><th>Extra claims at Q2 rate</th><th>Share of deterioration</th></tr></thead>
        <tbody>
          {s.segments.map((g) => (
            <tr key={g.code}>
              <td><strong>{g.label}</strong></td><td>{pct(g.q2.loss_ratio)}</td><td>{pct(g.q3.loss_ratio)}</td>
              <td>{pts(g.delta_points)}</td><td>{m(g.contribution)}</td><td>{pct(g.share, 0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="on-bridge">
        {s.segments.map((g) => <Bar key={g.code} share={g.share} label={g.label} value={`${pct(g.share, 0)} · ${m(g.contribution)}`} />)}
      </div>
      <Asker space="governed" question={s.question} label="Ask the assistant" />
      <Explain
        seeing="The headline, the segment table and the attribution are computed live from the governed motor metric view. The assistant’s narrative comes from the same metric, so the words and the numbers cannot drift apart."
        matters="Attribution holds each segment’s Q3 earned premium constant and asks how many more claims it produced than its own Q2 loss ratio would predict. That separates a segment getting worse from a change in business mix, which is the question the CUO is really asking."
      />
      <Explore>
        <p className="on-small">Definition in force: version {s.approved.version} “{s.approved.name}”, approved by {s.approved.approved_by}. {s.approved.definition_text}</p>
        <p className="on-small">Metric view <code>bricksurance_semantics.motor_performance_metrics</code>, measure <code>loss_ratio</code>; valuation date {s.valuation_date}; accident-quarter basis; GBP.</p>
      </Explore>
    </div>
  );
}

function Delta({ a, b, fmt }: { a?: number; b?: number; fmt: (v: number | undefined) => string }) {
  const up = (b ?? 0) > (a ?? 0);
  return <span>{fmt(a)} → <strong className={up ? 'on-flag' : ''}>{fmt(b)}</strong></span>;
}

function BeatDrilldown({ s, ev }: { s: State; ev: Evidence | null }) {
  const q = (k: string) => s.follow_ups.find((f) => f.key === k)!.question;
  const pmuTheft = ev?.theft.find((r) => r.motor_segment_code === 'PMU');
  const largeTrue = ev?.large.find((r) => String(r.large_loss_flag) === 'true');
  const largeFalse = ev?.large.find((r) => String(r.large_loss_flag) === 'false');
  const per100 = (v?: number) => (v === undefined ? '—' : v.toFixed(2));
  return (
    <div>
      <h2 className="on-h2">Every driver is a follow-up question, answered from data.</h2>
      <p className="on-lede">Three questions the CUO asks next. Each has the evidence beside it, computed live, and the assistant answering from the same metric.</p>

      <h3 className="on-h3">1 · Where is the urban deterioration?</h3>
      {ev && (
        <table className="on-table">
          <thead><tr><th>Region (urban private motor)</th><th>Q2 loss ratio</th><th>Q3 loss ratio</th><th>Change</th><th>Extra claims at Q2 rate</th></tr></thead>
          <tbody>{ev.regions.slice(0, 6).map((r) => (
            <tr key={r.region_name}><td>{r.region_name}</td><td>{pct(r.q2.loss_ratio)}</td><td>{pct(r.q3.loss_ratio)}</td><td>{pts(r.delta_points)}</td><td>{m(r.extra_incurred)}</td></tr>
          ))}</tbody>
        </table>
      )}
      {ev && pmuTheft && (
        <div className="on-three">
          <div className="on-card"><div className="on-card-tag">Urban theft frequency</div><div className="on-card-title"><Delta a={pmuTheft.q2.per_100_vy} b={pmuTheft.q3.per_100_vy} fmt={(v) => per100(v)} /></div><div className="on-card-foot">theft claims per 100 vehicle-years</div></div>
          <div className="on-card"><div className="on-card-tag">Urban theft severity</div><div className="on-card-title"><Delta a={pmuTheft.q2.severity} b={pmuTheft.q3.severity} fmt={gbp} /></div><div className="on-card-foot">average net cost per theft claim</div></div>
          <div className="on-card"><div className="on-card-tag">Vehicle repair cost</div>
            <div className="on-card-title">{ev.repair.map((r) => <div key={r.motor_segment_code} className="on-small">{r.motor_segment_code}: <Delta a={r.q2.severity} b={r.q3.severity} fmt={gbp} /></div>)}</div>
            <div className="on-card-foot">average repair claim, by segment</div></div>
        </div>
      )}
      <Asker space="governed" question={q('areas')} label="Ask the assistant" compact />

      <h3 className="on-h3">2 · Frequency or severity?</h3>
      {ev && (
        <table className="on-table">
          <thead><tr><th>Segment</th><th>Claims per 100 vehicle-years</th><th>Average cost per claim</th><th>Claims</th></tr></thead>
          <tbody>{ev.freq_sev.map((r) => (
            <tr key={r.motor_segment_code}><td>{r.motor_segment}</td>
              <td><Delta a={r.q2.per_100_vy} b={r.q3.per_100_vy} fmt={(v) => per100(v)} /></td>
              <td><Delta a={r.q2.severity} b={r.q3.severity} fmt={gbp} /></td>
              <td>{n0(r.q2.claim_count)} → {n0(r.q3.claim_count)}</td></tr>
          ))}</tbody>
        </table>
      )}
      <Asker space="governed" question={q('freq_sev')} label="Ask the assistant" compact />

      <h3 className="on-h3">3 · How much of commercial is large losses?</h3>
      {ev && largeTrue && largeFalse && (
        <table className="on-table">
          <thead><tr><th>Commercial motor claims</th><th>Q2 incurred</th><th>Q3 incurred</th><th>Change</th><th>Claims</th></tr></thead>
          <tbody>
            <tr><td>Large losses (≥ £500k, bodily injury)</td><td>{m(largeTrue.q2.incurred_claims)}</td><td>{m(largeTrue.q3.incurred_claims)}</td><td>{m((largeTrue.q3.incurred_claims ?? 0) - (largeTrue.q2.incurred_claims ?? 0))}</td><td>{n0(largeTrue.q2.claim_count)} → {n0(largeTrue.q3.claim_count)}</td></tr>
            <tr><td>All other claims</td><td>{m(largeFalse.q2.incurred_claims)}</td><td>{m(largeFalse.q3.incurred_claims)}</td><td>{m((largeFalse.q3.incurred_claims ?? 0) - (largeFalse.q2.incurred_claims ?? 0))}</td><td>{n0(largeFalse.q2.claim_count)} → {n0(largeFalse.q3.claim_count)}</td></tr>
          </tbody>
        </table>
      )}
      <Asker space="governed" question={q('large')} label="Ask the assistant" compact />
      <Explain
        seeing="Each follow-up is answered twice: by a live table from the governed metric view, and by the assistant. Theft frequency and severity, repair cost, region and large-loss splits are all measures or dimensions of the same metric."
        matters="The executive can keep asking. Nothing here is a prepared paragraph: if the data changed tomorrow, every number and every answer would change with it. The analysis shows where to look; it does not by itself prove cause."
      />
    </div>
  );
}

function BeatTwoNumbers({ s }: { s: State }) {
  const d = s.definitions;
  return (
    <div>
      <h2 className="on-h2">Two numbers. Both right. Only one is the loss ratio.</h2>
      <div className="on-teams">
        <div className="on-team">
          <div className="on-team-name">Approved loss ratio <span className="on-pill">version {s.approved.version} · {s.approved.approved_by}</span></div>
          <div className="on-team-num">{pct(d.approved.q2)} → {pct(d.approved.q3)}</div>
          <div className="on-team-who">Incurred claims (paid + outstanding + not yet reported, net of recoveries) ÷ <strong>earned</strong> premium.</div>
          <div className="on-team-why">Answers: how profitable was the cover we actually provided this quarter. Lives in the certified metric view and the rulebook, with an owner and an approval date.</div>
        </div>
        <div className="on-team">
          <div className="on-team-name">{d.legacy.name} <span className="on-pill">legacy</span></div>
          <div className="on-team-num">{pct(d.legacy.q2)} → {pct(d.legacy.q3)}</div>
          <div className="on-team-who">{d.legacy.formula}.</div>
          <div className="on-team-why">{d.legacy.answers} {d.legacy.not} Where it comes from: {d.legacy.where}</div>
        </div>
      </div>
      <p className="on-punch">The popular query is not the authoritative definition. An AI that learns from what people run most will learn the second number. The business has to say which one is the loss ratio, and sign it.</p>
      <Explain
        seeing="The approved definition (from the company rulebook, compiled into the metric view) beside the legacy claims-operations ratio that the weekly dashboard has carried for years. Same data, two formulas, two different quarters-over-quarter stories."
        matters="Both are legitimate. Only one belongs in a board pack as ‘the loss ratio’. Automatic context layers learn from usage, so the most-used pattern has authority by default; certification and a named owner are how the business overrides popularity with judgement."
      />
      <Explore label="Explore — what the automatic layer picked up">
        <p className="on-small">The workspace’s automatic context layer (Genie Ontology) extracts snippets from dashboards, saved queries, metric views and Genie agents and ranks them by authority. Both the certified motor dashboard and the legacy claims-ops query exist in this workspace. Use the Genie One arm below to see which sources it cites; we report what we observe, not what we hope.</p>
        <Asker space="one" question="What is our motor loss ratio this quarter compared with last quarter?" label="Ask Genie One (workspace-wide)" compact />
      </Explore>
    </div>
  );
}

function BeatHow({ s, refresh }: { s: State; refresh: () => void }) {
  const [showAll, setShowAll] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const systems = s.systems.map((x) => x.system);
  const rows = showAll ? s.crosswalk : s.crosswalk.slice(0, 10);
  const reset = async () => {
    setBusy(true); setMsg(null);
    try { await call('/api/motor/reset', {}); setMsg('Republished the metric view and the governed assistant from the approved rulebook.'); refresh(); }
    catch (e) { setMsg(String((e as Error).message)); } finally { setBusy(false); }
  };
  return (
    <div>
      <h2 className="on-h2">Nobody taught the AI insurance from scratch. Three layers did.</h2>
      <div className="on-three">
        <div className="on-card">
          <div className="on-card-tag">1 · Industry knowledge</div>
          <div className="on-card-title">An open, ACORD-aligned base</div>
          <p className="on-small">What a policy, a coverage, an insured vehicle, a claim, a claim transaction and earned premium <em>are</em>, with definitions and relationships. Written once, as code, shared across insurers. The standard’s terms are cited, never reproduced.</p>
          <div className="on-card-foot">Ours. Open source. Portable as one file.</div>
        </div>
        <div className="on-card">
          <div className="on-card-tag">2 · Enterprise knowledge</div>
          <div className="on-card-title">This insurer’s mapping and definitions</div>
          <p className="on-small">Three mapping files say which column in which system is which concept, keep what is insurer-specific (segments, use classes) as extensions, and compile into comments, tags, conformed views, a certified metric and the assistant’s instructions. The rulebook says which loss ratio is the company’s, and who approved it.</p>
          <div className="on-card-foot">Theirs. Governed in the catalog. Certified becomes portable.</div>
        </div>
        <div className="on-card">
          <div className="on-card-tag">3 · Discovered knowledge</div>
          <div className="on-card-title">What the platform learns from use</div>
          <p className="on-small">The workspace’s automatic context layer harvests dashboards, saved queries, metric views and agents, scores them by authority and freshness, and cites them in answers. It finds the certified metric and the legacy query alike; certification is how the business tells it which wins.</p>
          <div className="on-card-foot">Native, automatic. Inferred stays with the data.</div>
        </div>
      </div>

      <h3 className="on-h3">The crosswalk: one concept, every system’s word for it</h3>
      <table className="on-table">
        <thead><tr><th>Core concept</th>{systems.map((x) => <th key={x}>{SYSTEM_WORDS[x] || x}</th>)}</tr></thead>
        <tbody>{rows.map((r) => (
          <tr key={`${r.concept}.${r.attribute}`}><td><code>{r.concept}.{r.attribute}</code></td>
            {systems.map((x) => <td key={x}>{r.systems[x] ? <><code>{r.systems[x].source}</code>{r.systems[x].note && <div className="on-small">{r.systems[x].note}</div>}</> : ''}</td>)}</tr>
        ))}</tbody>
      </table>
      <button className="on-link" onClick={() => setShowAll(!showAll)}>{showAll ? 'Show fewer' : `Show all ${s.crosswalk.length} mapped attributes`}</button>

      {s.second_insurer && (
        <>
          <h3 className="on-h3">A second insurer, the same question, two mapping files</h3>
          <div className="on-card">
            <div className="on-card-tag">{s.second_insurer.name} · {s.second_insurer.mappings.length} mapping files · {s.second_insurer.mapped_columns ?? '—'} mapped columns</div>
            {s.second_insurer.loaded && s.second_insurer.totals ? (
              <>
                <div className="on-card-title">
                  Motor loss ratio {pct(s.second_insurer.totals['2026Q2']?.loss_ratio)} → {pct(s.second_insurer.totals['2026Q3']?.loss_ratio)}
                </div>
                <table className="on-table">
                  <thead><tr><th>Segment</th><th>Quarter</th><th>Earned</th><th>Incurred</th><th>Loss ratio</th><th>Claims</th></tr></thead>
                  <tbody>{s.second_insurer.segments!.map((r, i) => (
                    <tr key={i}><td>{r.motor_segment}</td><td>{r.accident_quarter}</td><td>{m(r.earned_premium)}</td><td>{m(r.incurred_claims)}</td><td>{pct(r.loss_ratio)}</td><td>{n0(r.claim_count)}</td></tr>
                  ))}</tbody>
                </table>
                <div className="on-card-foot">Policy-centre and claim-centre shapes (PublicID, PolicyNumber, LossCause, TransactionType), different words again. Same concepts, same metric definition, same assistant rules. Harbour has no IBNR feed and no region dimension in this extract, and the view says so.</div>
              </>
            ) : (
              <div className="on-card-foot">Mapped ({s.second_insurer.mappings.join('; ')}) but not loaded in this workspace yet.</div>
            )}
          </div>
        </>
      )}

      <h3 className="on-h3">What is native, what is ours, what is simulated</h3>
      <table className="on-table">
        <tbody>
          <tr><td>Metric views, column comments, tags, certification, Genie agents and their API, dashboards</td><td><span className="on-pill">native</span></td></tr>
          <tr><td>Automatic context snippets and citations (Genie Ontology)</td><td><span className="on-pill">native, automatic — we seed sources and observe</span></td></tr>
          <tr><td>Pages and Domains (governed glossary entries)</td><td><span className="on-pill">native, account-level preview — the crosswalk above is the ready content</span></td></tr>
          <tr><td>The open base model, the mapping files, the generator, the rulebook with maker/checker, republish-on-approval</td><td><span className="on-pill">ours, open source</span></td></tr>
          <tr><td>The motor book itself: three systems, {s.systems.reduce((a, x) => a + x.tables.length, 0)} tables, two quarters</td><td><span className="on-pill">synthetic, deterministic, labelled — not posted to the group ledger</span></td></tr>
        </tbody>
      </table>
      <Explain
        seeing="The architecture behind the previous four screens, in business terms, and the honest split between what Databricks does natively, what this open project adds, and what is simulated."
        matters="An insurer should leave knowing three things: industry knowledge already exists and is a starting point, not a project; their own definitions and mappings are what make it theirs; and what the platform infers from use complements certified meaning but never replaces a signed definition."
      />
      <Explore label="Explore — run controls">
        <div className="btn-row">
          <button className="btn ghost" disabled={busy} onClick={reset}>{busy ? 'Resetting…' : 'Reset the demo (republish from the approved rulebook)'}</button>
        </div>
        {msg && <div className="on-note">{msg}</div>}
        <p className="on-small">Raw agent {s.spaces.raw || '(not configured)'} · governed agent {s.spaces.governed || '(not configured)'} · workspace {s.host}</p>
      </Explore>
    </div>
  );
}

export default function MotorView({ beat }: { beat?: string }) {
  const [s, setS] = useState<State | null>(null);
  const [ev, setEv] = useState<Evidence | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const idx = Math.max(0, BEATS.findIndex((b) => b.key === beat));
  const load = useCallback(() => {
    call<State>('/api/motor/state').then(setS).catch((e) => setErr(String(e.message)));
    call<Evidence>('/api/motor/evidence').then(setEv).catch(() => setEv(null));
  }, []);
  useEffect(load, [load]);
  const goto = (i: number) => navigate(href(['motor', BEATS[Math.min(Math.max(i, 0), BEATS.length - 1)].key]));
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'TEXTAREA' || tag === 'INPUT' || tag === 'SELECT') return;
      if (e.key === 'ArrowRight') goto(idx + 1);
      if (e.key === 'ArrowLeft') goto(idx - 1);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  return (
    <div className="view on-view">
      <div className="on-steps">
        {BEATS.map((b, i) => (
          <button key={b.key} className={`on-step ${i === idx ? 'active' : ''} ${i < idx ? 'done' : ''}`} onClick={() => goto(i)}>
            <span className="on-step-n">{i + 1}</span>{b.title}
          </button>
        ))}
      </div>
      {err && <div className="result-note err">Could not load the demo: {err}</div>}
      {!s && !err && <div className="loading">Loading the motor book…</div>}
      {s && (
        <div className="on-stage">
          {idx === 0 && <BeatQuestion s={s} />}
          {idx === 1 && <BeatNoContext s={s} />}
          {idx === 2 && <BeatAnswer s={s} />}
          {idx === 3 && <BeatDrilldown s={s} ev={ev} />}
          {idx === 4 && <BeatTwoNumbers s={s} />}
          {idx === 5 && <BeatHow s={s} refresh={load} />}
        </div>
      )}
      <div className="on-nav">
        <button className="btn ghost" disabled={idx === 0} onClick={() => goto(idx - 1)}>← Back</button>
        <span className="on-nav-hint">Use ← → keys to move between steps</span>
        <button className="btn primary" disabled={idx === BEATS.length - 1} onClick={() => goto(idx + 1)}>
          {idx === BEATS.length - 1 ? 'End' : `Next: ${BEATS[idx + 1].title} →`}
        </button>
      </div>
      <div className="on-disclaimer">
        About this demo: Bricksurance SE is a fictional insurer and all data is synthetic. The motor experience book is a
        separate, labelled dataset and is not posted to the group ledger. Numbers are calculated live from the governed
        metric view; AI answers are live, with saved, verified answers as a fallback.
      </div>
    </div>
  );
}
