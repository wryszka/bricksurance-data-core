import { useCallback, useEffect, useState } from 'react';
import { href, navigate } from '../useHashRoute';
import '../one-number.css';

// "One Number" — the governed loss-ratio demo for executives and actuaries.
// One question, one number, one screen per beat. Technical detail lives
// behind "Explore" only.

interface Definition {
  version: number;
  status: string;
  name: string;
  include_case_reserves: boolean;
  include_ibnr: boolean;
  include_claims_handling_costs: boolean;
  net_of_recoveries: boolean;
  premium_basis: 'EARNED' | 'WRITTEN';
  definition_text: string;
  rationale: string | null;
  proposed_by: string | null;
  approved_by: string | null;
  proposed_at: string | null;
  approved_at: string | null;
}
interface Book {
  loss_ratio: number;
  written_premium: number;
  earned_premium: number;
  claims_paid: number;
  case_reserves: number;
  ibnr: number;
  claims_handling_costs: number;
  recoveries: number;
  claim_count: number;
}
interface Team { team: string; who: string; counts: string; over: string; value: number; why: string }
interface BridgeStep { label: string; value: number; kind: 'start' | 'step' | 'end' }
interface Group { loss_ratio: number; earned_premium: number; clients: string }
interface Firm {
  client_name: string;
  global_company_id: string;
  industry_sector: string;
  annual_revenue_gbp: string;
  employee_count: string;
  financial_stress_score: string;
  financial_stress_band: string;
}
interface State {
  question: string;
  stress_question: string;
  approved: Definition;
  pending: Definition | null;
  pending_value?: number;
  history: Definition[];
  book: Book;
  teams: Team[];
  bridge: BridgeStep[];
  stress: { stressed?: Group; other?: Group };
  firmographics: Firm[];
  spaces: { raw: string; governed: string };
  host: string;
}
interface Answer { question: string; text: string[]; sql: string | null; columns: string[]; rows: (string | null)[][]; seconds: number }
interface AskResult { answers: Answer[]; explain: string[]; live: boolean; note?: string }
type Rule = Pick<Definition, 'include_case_reserves' | 'include_ibnr' | 'include_claims_handling_costs' | 'net_of_recoveries' | 'premium_basis'>;

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

const pct = (v: number | null | undefined, d = 1) =>
  v === null || v === undefined || Number.isNaN(v) ? '—' : `${(v * 100).toFixed(d)}%`;
const gbp = (v: number) => (v >= 1e6 ? `£${(v / 1e6).toFixed(1)}m` : `£${Math.round(v / 1e3)}k`);
const day = (s: string | null) => (s ? new Date(s.replace(' ', 'T')).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '');

// The number an assistant answered: last numeric column of the first row.
// Values above 1.5 are already percentages.
function answerValue(a: Answer): number | null {
  const row = a.rows?.[0];
  if (!row) return null;
  for (let i = row.length - 1; i >= 0; i--) {
    const v = row[i];
    if (v !== null && v !== '' && !Number.isNaN(Number(v))) {
      const n = Number(v);
      if (n === 0) return null;
      return n > 1.5 ? n / 100 : n;
    }
  }
  return null;
}
const stripMd = (s: string) => s.replace(/\*\*/g, '');

function ruleValue(b: Book, r: Rule) {
  let cost = b.claims_paid;
  if (r.include_case_reserves) cost += b.case_reserves;
  if (r.include_ibnr) cost += b.ibnr;
  if (r.include_claims_handling_costs) cost += b.claims_handling_costs;
  if (r.net_of_recoveries) cost -= b.recoveries;
  return cost / (r.premium_basis === 'EARNED' ? b.earned_premium : b.written_premium);
}

const BEATS = [
  { key: 'question', title: 'The question' },
  { key: 'today', title: 'Today: three answers' },
  { key: 'no-context', title: 'AI without context' },
  { key: 'rulebook', title: 'Give it the rulebook' },
  { key: 'ask-again', title: 'Ask again' },
  { key: 'change', title: 'Change the rule' },
  { key: 'path', title: 'How you get here' },
];

function Explain({ seeing, matters }: { seeing: string; matters: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="on-explain">
      <button className="on-link" onClick={() => setOpen(!open)}>
        {open ? '▾' : '▸'} What am I seeing?
      </button>
      {open && (
        <div className="on-explain-body">
          <p><strong>What you’re seeing.</strong> {seeing}</p>
          <p><strong>Why it matters.</strong> {matters}</p>
        </div>
      )}
    </div>
  );
}

function Explore({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="on-explore">
      <button className="on-link" onClick={() => setOpen(!open)}>
        {open ? '▾' : '⚙'} Explore — how it works
      </button>
      {open && <div className="on-explore-body">{children}</div>}
    </div>
  );
}

function AnswerCard({ a, i, governed }: { a: Answer; i: number; governed: boolean }) {
  const v = answerValue(a);
  const said = stripMd(a.text[0] || '');
  const dollars = !governed && /\$/.test(a.text.join(' '));
  return (
    <div className={`on-answer ${governed ? 'good' : v === null ? 'none' : 'bad'}`}>
      <div className="on-answer-head">Attempt {i + 1}</div>
      <div className="on-answer-num">{v === null ? 'No answer' : pct(v)}</div>
      <div className="on-answer-said">“{said.length > 220 ? said.slice(0, 220) + '…' : said}”</div>
      {dollars && <div className="on-flag">Reported in dollars — our book is in pounds</div>}
    </div>
  );
}

function Asker({ space, question, label, onDone }: {
  space: 'raw' | 'governed'; question: string; label: string; onDone?: (r: AskResult) => void;
}) {
  const [res, setRes] = useState<AskResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const go = async (live: boolean, times: number) => {
    setBusy(true); setErr(null); setRes(null); setElapsed(0);
    const t0 = Date.now();
    const timer = setInterval(() => setElapsed(Math.round((Date.now() - t0) / 1000)), 500);
    try {
      const r = await call<AskResult>('/api/one-number/ask', { space, question, times, live });
      setRes(r); onDone?.(r);
    } catch (e) {
      setErr(String((e as Error).message));
    } finally {
      clearInterval(timer); setBusy(false);
    }
  };
  const governed = space === 'governed';
  const times = question.includes('financial stress') ? 1 : 3;
  return (
    <div className="on-asker">
      <div className="on-q">“{question}”</div>
      <div className="btn-row">
        <button className="btn primary on-big" disabled={busy} onClick={() => go(true, times)}>
          {busy ? `Asking… ${elapsed}s` : label}
        </button>
        <button className="btn ghost" disabled={busy} onClick={() => go(false, times)}>
          Show saved answer
        </button>
      </div>
      {err && <div className="result-note err">{err}</div>}
      {res && (
        <>
          {!res.live && <div className="on-note">{res.note || 'Saved answer from a verified earlier run.'}</div>}
          {times === 3 && (
            <div className="on-answers">
              {res.answers.map((a, i) => <AnswerCard key={i} a={a} i={i} governed={governed} />)}
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
                <pre className="sql-code">{a.sql}</pre>
              </div>
            ))}
          </Explore>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- beats

function BeatQuestion({ s }: { s: State }) {
  return (
    <div className="on-hero">
      <div className="on-kicker">Thursday, 8:40am. The board meets at 10.</div>
      <h1 className="on-hero-q">“{s.question}”</h1>
      <p className="on-lede">
        The simplest question an insurer can be asked. Watch how many answers it has today, and what
        it takes to give one, every time, from people and from AI.
      </p>
      <Explain
        seeing="The question a CEO asks before every board meeting."
        matters="Every insurer has this problem. The loss ratio is the headline number of the business, yet different teams calculate it differently. Get one number agreed, and AI can be trusted with the rest."
      />
    </div>
  );
}

function BeatToday({ s }: { s: State }) {
  return (
    <div>
      <h2 className="on-h2">Three teams. Three answers. All of them “right”.</h2>
      <div className="on-teams">
        {s.teams.map((t) => (
          <div className="on-team" key={t.team}>
            <div className="on-team-name">{t.team}</div>
            <div className="on-team-who">{t.who}</div>
            <div className="on-team-num">{pct(t.value, 0)}</div>
            <div className="on-team-row"><span>Counts</span>{t.counts}</div>
            <div className="on-team-row"><span>Divided by</span>{t.over}</div>
            <div className="on-team-why">{t.why}</div>
          </div>
        ))}
      </div>
      <div className="on-punch">
        Nobody is wrong. They each answer a slightly different question. The board pack waits for a
        reconciliation meeting, and nobody trusts the AI pilot.
      </div>
      <Explain
        seeing="The same Commercial Property book, measured by three teams. Each number is calculated live from the same underlying claims and premium; only the definition differs."
        matters="This gap is where time, trust and money go: reconciliation meetings, restated board packs and AI pilots that never make it to production because nobody can say which number is right."
      />
      <Explore>
        <BuildingBlocks b={s.book} />
      </Explore>
    </div>
  );
}

function BuildingBlocks({ b }: { b: Book }) {
  const rows: [string, number][] = [
    ['Premium written (everything sold)', b.written_premium],
    ['Premium earned (cover already given)', b.earned_premium],
    ['Claims paid', b.claims_paid],
    ['Claims reported, not yet paid (case reserves)', b.case_reserves],
    ['Claims happened, not yet reported (IBNR)', b.ibnr],
    ['Claims-handling costs (ALAE)', b.claims_handling_costs],
    ['Recoveries (salvage, third parties)', b.recoveries],
  ];
  return (
    <div>
      <div className="on-tech-head">The building blocks every definition uses (Commercial Property, GBP, whole book)</div>
      <table className="on-table">
        <tbody>{rows.map(([k, v]) => <tr key={k}><td>{k}</td><td className="num">{gbp(v)}</td></tr>)}</tbody>
      </table>
      <p className="on-small">Source: the published metric <code>bricksurance_semantics.loss_ratio_metrics</code> over
        <code> loss_ratio_components</code>, built from policy, premium and claim transactions in the Data Core.</p>
    </div>
  );
}

function BeatNoContext({ s }: { s: State }) {
  return (
    <div>
      <h2 className="on-h2">Ask an AI assistant. It has the data, but not your definitions.</h2>
      <p className="on-lede">
        This is what most AI pilots look like: an assistant pointed straight at the claims and policy
        systems. We ask it the same question three times.
      </p>
      <Asker space="raw" question={s.question} label="Ask it three times" />
      <Explain
        seeing="A live AI assistant (Databricks Genie) connected to the raw policy, premium and claims tables, with no business definitions and no instructions. Each attempt is a separate, live conversation."
        matters="Without context, AI is a confident guesser. It may add currencies together, count reserve movements as claims, or give up. The same question gets different answers, and none match any team's number."
      />
    </div>
  );
}

function BeatRulebook({ s }: { s: State }) {
  const d = s.approved;
  const max = Math.max(...s.bridge.map((b) => b.value)) * 1.08;
  return (
    <div>
      <h2 className="on-h2">Give it the rulebook: three things every insurer already has.</h2>
      <div className="on-three">
        <div className="on-card">
          <div className="on-card-tag">1 · The industry dictionary</div>
          <div className="on-card-title">The words everyone in insurance already agrees on</div>
          <dl className="on-dl">
            <dt>Written premium</dt><dd>The premium for all the cover we have sold.</dd>
            <dt>Earned premium</dt><dd>The part of that premium for cover already given.</dd>
            <dt>Case reserve</dt><dd>Our estimate of what we still owe on claims we know about.</dd>
            <dt>IBNR</dt><dd>Claims that have happened but have not been reported yet.</dd>
          </dl>
          <div className="on-card-foot">Aligned to ACORD, the industry’s standard insurance vocabulary.</div>
        </div>
        <div className="on-card accent">
          <div className="on-card-tag">2 · Our definition, signed off</div>
          <div className="on-card-title">{d.name}</div>
          <p className="on-def">{d.definition_text}</p>
          <div className="on-card-foot">
            Version {d.version} · proposed by the {d.proposed_by} · approved by the <strong>{d.approved_by}</strong> on {day(d.approved_at)}
          </div>
        </div>
        <div className="on-card">
          <div className="on-card-tag">3 · One outside source</div>
          <div className="on-card-title">Who our clients really are</div>
          <table className="on-table compact">
            <thead><tr><th>Client</th><th>Industry</th><th>Revenue</th><th>Financial stress</th></tr></thead>
            <tbody>
              {s.firmographics.map((f) => (
                <tr key={f.client_name}>
                  <td>{f.client_name}</td><td>{f.industry_sector}</td>
                  <td>{gbp(Number(f.annual_revenue_gbp))}</td>
                  <td><span className={`on-band ${f.financial_stress_band.toLowerCase()}`}>{f.financial_stress_band}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="on-card-foot">Company data (Dun &amp; Bradstreet-style, synthetic) matched to our clients by company ID.</div>
        </div>
      </div>

      <h3 className="on-h3">And the reason the three teams differ, in one picture</h3>
      <div className="on-bridge">
        {s.bridge.map((b, i) => {
          const prev = i === 0 ? 0 : s.bridge[i - 1].value;
          const lo = b.kind === 'step' ? Math.min(prev, b.value) : 0;
          const hi = b.kind === 'step' ? Math.max(prev, b.value) : b.value;
          const delta = b.value - prev;
          return (
            <div className="on-bridge-row" key={i}>
              <div className="on-bridge-label">{b.label}</div>
              <div className="on-bridge-track">
                <div className={`on-bridge-bar ${b.kind} ${delta < 0 ? 'down' : ''}`}
                  style={{ left: `${(lo / max) * 100}%`, width: `${Math.max(((hi - lo) / max) * 100, 0.6)}%` }} />
              </div>
              <div className="on-bridge-val">
                {b.kind === 'step' ? `${delta >= 0 ? '+' : '−'}${Math.abs(delta * 100).toFixed(1)} pts` : pct(b.value)}
              </div>
            </div>
          );
        })}
      </div>
      <Explain
        seeing="The three pieces of context we give the assistant: the industry vocabulary, the company's own approved definition, and outside data about each client. Below them is a walk from the Finance number to the company number, one ingredient at a time, all from the same data."
        matters="None of this is new. Insurers already have a reserving manual, a glossary and data suppliers. The difference is putting them next to the data, in a form both people and AI use, so the reconciliation meeting becomes a one-page picture."
      />
      <Explore>
        <p className="on-small">
          The definition is a governed, versioned row in <code>bricksurance_semantics.loss_ratio_definition</code>
          (maker/checker). The approved version is published as a Unity Catalog metric view
          (<code>loss_ratio_metrics</code>) and written into the AI assistant’s instructions. Industry terms come from the
          Data Core’s ACORD-aligned model, where every column carries its definition. Outside data lives in
          <code> bricksurance_enrichment.business_firmographics</code>, joined by <code>global_company_id</code>.
        </p>
      </Explore>
    </div>
  );
}

function BeatAskAgain({ s }: { s: State }) {
  const st = s.stress;
  const [asked, setAsked] = useState(false);
  return (
    <div>
      <h2 className="on-h2">Same question, same assistant, now with the rulebook.</h2>
      <Asker space="governed" question={s.question} label="Ask it three times" />
      <h3 className="on-h3">And a question you couldn’t ask before</h3>
      <Asker space="governed" question={s.stress_question} label="Ask the follow-up" onDone={() => setAsked(true)} />
      {asked && st.stressed && st.other && (
        <div className="on-split">
          <div className="on-split-col bad">
            <div className="on-split-label">Clients under financial stress</div>
            <div className="on-split-num">{pct(st.stressed.loss_ratio)}</div>
            <div className="on-split-sub">{st.stressed.clients} · {gbp(st.stressed.earned_premium)} earned</div>
          </div>
          <div className="on-split-col good">
            <div className="on-split-label">All other clients</div>
            <div className="on-split-num">{pct(st.other.loss_ratio)}</div>
            <div className="on-split-sub">{st.other.clients} · {gbp(st.other.earned_premium)} earned</div>
          </div>
        </div>
      )}
      <div className="on-punch">
        One answer, every time, and it says what it counted and who approved it. The outside data turns
        a number into a renewal conversation.
      </div>
      <Explain
        seeing="The same AI assistant, now pointed at the approved definition, the published metric and the outside company data. Asked three times live, then a follow-up that combines our book with outside data."
        matters="Consistency is what makes AI usable in a regulated business. The answer matches the board pack because both come from one definition. The follow-up shows the payoff: the largest client is under financial stress, and its loss ratio is almost double the rest of the book."
      />
    </div>
  );
}

const RULES: { key: keyof Rule; label: string; hint: string }[] = [
  { key: 'include_case_reserves', label: 'Claims reported but not yet paid', hint: 'case reserves' },
  { key: 'include_ibnr', label: 'Claims that have happened but are not yet reported', hint: 'IBNR' },
  { key: 'include_claims_handling_costs', label: 'Costs of settling claims: legal fees, surveyors', hint: 'ALAE' },
  { key: 'net_of_recoveries', label: 'Deduct what we recover from salvage and third parties', hint: 'recoveries' },
];

function BeatChange({ s, refresh, setS }: { s: State; refresh: () => void; setS: (x: State) => void }) {
  const a = s.approved;
  const [rule, setRule] = useState<Rule>({
    include_case_reserves: a.include_case_reserves, include_ibnr: a.include_ibnr,
    include_claims_handling_costs: !a.include_claims_handling_costs ? true : a.include_claims_handling_costs,
    net_of_recoveries: a.net_of_recoveries, premium_basis: a.premium_basis,
  });
  const [reason, setReason] = useState('Align with the reserving view: the cost of settling a claim is part of the cost of the claim.');
  const [approver, setApprover] = useState('Chief Actuary');
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [published, setPublished] = useState(false);
  const now = s.book.loss_ratio;
  const next = ruleValue(s.book, rule);
  const same = (Object.keys(rule) as (keyof Rule)[]).every((k) => rule[k] === a[k]);

  const act = async (what: string, url: string, body: unknown) => {
    setBusy(what); setErr(null);
    try {
      const r = await call<State>(url, body);
      setS(r);
      if (what === 'approve') setPublished(true);
    } catch (e) { setErr((e as Error).message); } finally { setBusy(null); }
  };

  return (
    <div>
      <h2 className="on-h2">The business owns the meaning. Change it once, and it changes everywhere.</h2>
      <div className="on-change">
        <div className="on-card">
          <div className="on-card-tag">Proposed by the Reserving Manager</div>
          <div className="on-card-title">What should the company loss ratio count?</div>
          <div className="on-rules">
            <label className="on-rule fixed"><input type="checkbox" checked readOnly disabled /> Claims paid <span>always</span></label>
            {RULES.map((r) => (
              <label key={r.key} className={`on-rule ${rule[r.key] !== a[r.key] ? 'changed' : ''}`}>
                <input type="checkbox" checked={Boolean(rule[r.key])} disabled={!!s.pending}
                  onChange={(e) => setRule({ ...rule, [r.key]: e.target.checked })} />
                {r.label} <span>{r.hint}</span>
              </label>
            ))}
            <div className="on-basis">
              Divide by
              <button className={`on-pill ${rule.premium_basis === 'EARNED' ? 'on' : ''}`} disabled={!!s.pending}
                onClick={() => setRule({ ...rule, premium_basis: 'EARNED' })}>premium earned</button>
              <button className={`on-pill ${rule.premium_basis === 'WRITTEN' ? 'on' : ''}`} disabled={!!s.pending}
                onClick={() => setRule({ ...rule, premium_basis: 'WRITTEN' })}>premium written</button>
            </div>
          </div>
          <textarea className="on-reason" value={reason} disabled={!!s.pending} onChange={(e) => setReason(e.target.value)} />
          <div className="on-preview">
            <div><div className="on-preview-label">In force today (v{a.version})</div><div className="on-preview-num">{pct(now)}</div></div>
            <div className="on-arrow">→</div>
            <div><div className="on-preview-label">With this change</div><div className="on-preview-num accent">{pct(s.pending_value ?? next)}</div></div>
            <div className="on-preview-delta">{same ? 'no change' : `${next >= now ? '+' : '−'}${Math.abs((next - now) * 100).toFixed(1)} pts`}</div>
          </div>
          {!s.pending && (
            <button className="btn primary on-big" disabled={same || !!busy}
              onClick={() => act('propose', '/api/one-number/propose', { ...rule, rationale: reason, proposed_by: 'Reserving Manager' })}>
              {busy === 'propose' ? 'Submitting…' : 'Submit for approval'}
            </button>
          )}
        </div>

        <div className={`on-card ${s.pending ? 'accent' : 'muted'}`}>
          <div className="on-card-tag">Approval · four eyes</div>
          {s.pending ? (
            <>
              <div className="on-card-title">Version {s.pending.version} is waiting for approval</div>
              <p className="on-def">{s.pending.definition_text}</p>
              <p className="on-small"><strong>Why:</strong> {s.pending.rationale}</p>
              <div className="on-approve">
                Approve as
                <select value={approver} onChange={(e) => setApprover(e.target.value)}>
                  <option>Chief Actuary</option>
                  <option>Reserving Manager</option>
                </select>
                <button className="btn accent on-big" disabled={!!busy}
                  onClick={() => act('approve', '/api/one-number/approve', { approved_by: approver })}>
                  {busy === 'approve' ? 'Publishing…' : 'Approve & publish'}
                </button>
                <button className="btn ghost" disabled={!!busy} onClick={() => act('reject', '/api/one-number/reject', {})}>Send back</button>
              </div>
              {err && <div className="result-note err">{err}</div>}
            </>
          ) : published ? (
            <>
              <div className="on-card-title">Version {a.version} is now the company loss ratio: {pct(now)}</div>
              <ul className="on-checks">
                <li>✓ The published metric every report reads from</li>
                <li>✓ The AI assistant’s instructions</li>
                <li>✓ The board pack and dashboards built on the metric</li>
                <li>✓ The audit trail: who proposed, who approved, when and why</li>
              </ul>
              <Asker space="governed" question={s.question} label="Ask the assistant again" />
            </>
          ) : (
            <div className="on-card-title muted">Nothing waiting. Propose a change on the left.</div>
          )}
        </div>
      </div>

      <h3 className="on-h3">The rulebook’s history</h3>
      <table className="on-table">
        <thead><tr><th>Version</th><th>Status</th><th>Definition</th><th>Proposed by</th><th>Approved by</th><th>When</th></tr></thead>
        <tbody>
          {s.history.map((d) => (
            <tr key={d.version} className={d.status === 'APPROVED' ? 'on-current' : ''}>
              <td>v{d.version}</td><td>{d.status.toLowerCase()}</td><td>{d.name}</td>
              <td>{d.proposed_by}</td><td>{d.approved_by || '—'}</td><td>{day(d.approved_at || d.proposed_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <Explain
        seeing="The Reserving Manager proposes adding claims-handling costs to the definition. The impact is shown before anyone approves. The Chief Actuary approves it, because the person who proposes a change cannot approve it, and the new version is published."
        matters="Today a definition change means emails, spreadsheets and weeks of drift between reports. Here the business owns the meaning, the impact is visible up front, and one approval updates the metric, the assistant and every report at once, with a full audit trail."
      />
      <Explore>
        <p className="on-small">
          Approval writes the new version to <code>loss_ratio_definition</code>, re-creates the Unity Catalog metric
          view <code>loss_ratio_metrics</code> from it, and rewrites the Genie space instructions through the Genie API.
          “Reset the demo” restores version 1.
        </p>
        <button className="btn ghost" disabled={!!busy} onClick={() => { setPublished(false); act('reset', '/api/one-number/reset', {}).then(refresh); }}>
          {busy === 'reset' ? 'Resetting…' : 'Reset the demo to version 1'}
        </button>
      </Explore>
    </div>
  );
}

const LADDER = [
  { step: 'Write down what you already mean', who: 'Chief Actuary, Finance', time: '2–4 weeks',
    get: 'One signed-off page per headline number. Most insurers already have it in a reserving manual or an Excel glossary.' },
  { step: 'Put the definitions next to the data', who: 'Data team', time: '4–6 weeks',
    get: 'Every report and dashboard calculates the number the same way, from the same building blocks.' },
  { step: 'Point your AI assistant at them', who: 'Data team and one business owner', time: '2 weeks',
    get: 'Answers that state their basis and match the board pack.' },
  { step: 'Add one outside source', who: 'Underwriting and data team', time: '2–4 weeks per source',
    get: 'Questions you could not ask before, such as which clients are under financial stress.' },
  { step: 'Govern changes', who: 'Owner of each number, plus an approver', time: 'Ongoing',
    get: 'Change once, updated everywhere, with an audit trail the regulator can follow.' },
];

function BeatPath() {
  return (
    <div>
      <h2 className="on-h2">Not a five-year programme. Five steps, starting with one number.</h2>
      <div className="on-ladder">
        {LADDER.map((l, i) => (
          <div className="on-rung" key={l.step}>
            <div className="on-rung-n">{i + 1}</div>
            <div className="on-rung-body">
              <div className="on-rung-step">{l.step}</div>
              <div className="on-rung-get">{l.get}</div>
            </div>
            <div className="on-rung-meta"><div>{l.who}</div><div className="on-rung-time">{l.time}</div></div>
          </div>
        ))}
      </div>
      <div className="on-punch">
        Start with one line of business and one number, the loss ratio. Everything you have just seen
        runs on that.
      </div>
      <Explain
        seeing="The path from where most insurers are today (definitions in documents and spreadsheets) to what you have just seen. Timings are indicative for one line of business and one headline number."
        matters="You don't need a new core system, a data-model programme or an AI platform project to start. The first step is writing down what you already mean, and every step delivers something on its own."
      />
    </div>
  );
}

// ---------------------------------------------------------------- shell

export default function OneNumberView({ beat }: { beat?: string }) {
  const [s, setS] = useState<State | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const idx = Math.max(0, BEATS.findIndex((b) => b.key === beat));
  const load = useCallback(() => {
    call<State>('/api/one-number/state').then(setS).catch((e) => setErr(String(e.message)));
  }, []);
  useEffect(load, [load]);
  const goto = (i: number) => navigate(href(['one-number', BEATS[Math.min(Math.max(i, 0), BEATS.length - 1)].key]));
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
      {!s && !err && <div className="loading">Loading the book…</div>}
      {s && (
        <div className="on-stage">
          {idx === 0 && <BeatQuestion s={s} />}
          {idx === 1 && <BeatToday s={s} />}
          {idx === 2 && <BeatNoContext s={s} />}
          {idx === 3 && <BeatRulebook s={s} />}
          {idx === 4 && <BeatAskAgain s={s} />}
          {idx === 5 && <BeatChange s={s} refresh={load} setS={setS} />}
          {idx === 6 && <BeatPath />}
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
        About this demo: Bricksurance SE is a fictional insurer and all data is synthetic, including the outside
        company data. Numbers are calculated live from the Bricksurance Data Core; AI answers are live, with saved,
        verified answers as a fallback.
      </div>
    </div>
  );
}
