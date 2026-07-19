import { useEffect, useState } from 'react';
import {
  api,
  GovernanceActionsResponse,
  GovernanceResponse,
  ProposeBody,
  ProposeResponse,
} from '../api';
import { href, navigate } from '../useHashRoute';
import { CertBadge, CopyButton, ErrorNote, Loading, SqlBlock } from '../components/ui';

function Gauge({
  label,
  done,
  total,
  tone = 'teal',
}: {
  label: string;
  done: number;
  total: number;
  tone?: string;
}) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return (
    <div className="gauge">
      <div className="gauge-top">
        <span className="gauge-label">{label}</span>
        <span className="gauge-count">
          {done}/{total}
        </span>
      </div>
      <div className="gauge-track">
        <div
          className={`gauge-fill tone-${tone}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="gauge-pct">{pct}% certified</div>
    </div>
  );
}

const CLASS_TONES: Record<string, string> = {
  internal: 'internal',
  confidential: 'conf',
  pii: 'pii',
  unassessed: 'risk',
};

function ClassMap({ gov }: { gov: GovernanceResponse }) {
  const cls = gov.attributes.classification;
  const entries: [string, number][] = [
    ['pii', cls.pii || 0],
    ['confidential', cls.confidential || 0],
    ['internal', cls.internal || 0],
    ['unassessed', gov.attributes.unassessed || cls.unassessed || 0],
  ];
  const total = gov.attributes.total || entries.reduce((s, [, v]) => s + v, 0) || 1;
  return (
    <div className="classmap">
      <div className="classmap-bar">
        {entries.map(([k, v]) =>
          v > 0 ? (
            <div
              key={k}
              className={`classmap-seg seg-${CLASS_TONES[k]}`}
              style={{ width: `${(v / total) * 100}%` }}
              title={`${k}: ${v}`}
            />
          ) : null,
        )}
      </div>
      <div className="classmap-legend">
        {entries.map(([k, v]) => (
          <span key={k} className={`classmap-key ${k === 'unassessed' && v > 0 ? 'risk' : ''}`}>
            <span className={`sw seg-${CLASS_TONES[k]}`} /> {k} · {v}
          </span>
        ))}
      </div>
      {(gov.attributes.unassessed || 0) === 0 && (
        <div className="classmap-note">
          No unassessed attributes — every attribute carries a classification.
        </div>
      )}
    </div>
  );
}

function OwnershipBoard({ gov }: { gov: GovernanceResponse }) {
  const [open, setOpen] = useState<string | null>(null);
  return (
    <div className="ownership-board">
      {gov.ownership_board.map((o) => (
        <div key={o.owner} className="owner-group card">
          <button
            className="owner-head"
            onClick={() => setOpen(open === o.owner ? null : o.owner)}
          >
            <span className="owner-name">{o.owner}</span>
            <span className="owner-count">{o.count}</span>
            <span className="owner-chev">{open === o.owner ? '▾' : '▸'}</span>
          </button>
          {open === o.owner && (
            <div className="owner-elements">
              {o.elements.map((el) => (
                <a
                  key={el.name}
                  className="owner-el"
                  href={href(['entity', el.name])}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(href(['entity', el.name]));
                  }}
                >
                  <span className="owner-el-name">{el.name}</span>
                  <span className="owner-el-domain">{el.domain}</span>
                  <CertBadge c={el.certification} />
                </a>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

const EMPTY_FORM: ProposeBody = {
  element: '',
  element_kind: 'entity',
  field: '',
  proposed_value: '',
  rationale: '',
  raised_by: '',
  current_value: '',
};

function ProposeForm({ onSubmitted }: { onSubmitted: () => void }) {
  const [form, setForm] = useState<ProposeBody>(EMPTY_FORM);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<ProposeResponse | null>(null);

  const set = (k: keyof ProposeBody, v: string) =>
    setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      const r = await api.propose(form);
      setResult(r);
      onSubmitted();
    } catch (ex) {
      setErr(String(ex));
    } finally {
      setBusy(false);
    }
  };

  const valid =
    form.element && form.field && form.proposed_value && form.rationale && form.raised_by;

  return (
    <div className="card propose-card">
      <div className="propose-head">
        <h3 className="detail-h3">Propose a change</h3>
        <p className="detail-note">
          Capture-only. The model truth stays in the versioned YAML specs —
          nothing here is auto-applied. A proposal generates a diff stub to take
          through the evolution contract.
        </p>
      </div>
      <form className="propose-form" onSubmit={submit}>
        <div className="pf-grid">
          <label className="pf-field">
            <span>Element</span>
            <input
              value={form.element}
              onChange={(e) => set('element', e.target.value)}
              placeholder="e.g. claim"
            />
          </label>
          <label className="pf-field">
            <span>Kind</span>
            <select
              value={form.element_kind}
              onChange={(e) => set('element_kind', e.target.value)}
            >
              <option value="entity">entity</option>
              <option value="metric">metric</option>
              <option value="attribute">attribute</option>
            </select>
          </label>
          <label className="pf-field">
            <span>Field</span>
            <input
              value={form.field}
              onChange={(e) => set('field', e.target.value)}
              placeholder="e.g. description"
            />
          </label>
          <label className="pf-field">
            <span>Current value (optional)</span>
            <input
              value={form.current_value}
              onChange={(e) => set('current_value', e.target.value)}
              placeholder="current…"
            />
          </label>
          <label className="pf-field pf-wide">
            <span>Proposed value</span>
            <input
              value={form.proposed_value}
              onChange={(e) => set('proposed_value', e.target.value)}
              placeholder="proposed…"
            />
          </label>
          <label className="pf-field pf-wide">
            <span>Rationale</span>
            <textarea
              value={form.rationale}
              onChange={(e) => set('rationale', e.target.value)}
              rows={2}
              placeholder="why the change is needed"
            />
          </label>
          <label className="pf-field">
            <span>Raised by</span>
            <input
              value={form.raised_by}
              onChange={(e) => set('raised_by', e.target.value)}
              placeholder="you@bricksurance.example"
            />
          </label>
        </div>
        <div className="btn-row">
          <button className="btn primary" type="submit" disabled={!valid || busy}>
            {busy ? 'Capturing…' : 'Capture proposal'}
          </button>
        </div>
      </form>

      {err && <ErrorNote error={err} />}

      {result && (
        <div className="propose-result">
          <div className="result-note ok">
            Captured as <span className="mono">{result.action_id}</span> · status{' '}
            {result.status}. {result.note}
          </div>
          {result.spec_diff && (
            <>
              <div className="detail-note">
                The generated diff stub for the source YAML (not applied):
              </div>
              <div className="sql-block">
                <div className="sql-block-bar">
                  <span className="sql-block-tag">spec diff</span>
                  <CopyButton text={result.spec_diff} />
                </div>
                <pre className="sql-code">{result.spec_diff}</pre>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function ActionsTable({ data }: { data: GovernanceActionsResponse | null }) {
  if (!data) return <Loading label="Loading captured actions…" />;
  if (data.error) {
    return (
      <div className="soft-note">
        The action log is unavailable right now ({data.error}). You can still
        capture proposals above — they’re recorded when the store is warm.
      </div>
    );
  }
  if (data.actions.length === 0) {
    return <div className="empty-note">No proposals or issues captured yet.</div>;
  }
  return (
    <div className="card scroll-x">
      <table>
        <thead>
          <tr>
            <th>Raised</th>
            <th>Type</th>
            <th>Element</th>
            <th>Field</th>
            <th>Proposed</th>
            <th>Rationale</th>
            <th>By</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.actions.map((a) => (
            <tr key={a.action_id}>
              <td>{a.raised_on}</td>
              <td>{a.action_type}</td>
              <td className="mono">
                {a.element}
                <span className="muted-sub"> · {a.element_kind}</span>
              </td>
              <td className="mono">{a.field || '—'}</td>
              <td className="def">{a.proposed_value || '—'}</td>
              <td className="def">{a.rationale}</td>
              <td>{a.raised_by}</td>
              <td>{a.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const REGIMES = [
  { id: 'solvency_ii', label: 'Solvency II' },
  { id: 'ifrs_17', label: 'IFRS 17' },
  { id: 'gdpr', label: 'GDPR' },
];

export default function GovernanceView() {
  const [gov, setGov] = useState<GovernanceResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [actions, setActions] = useState<GovernanceActionsResponse | null>(null);

  const loadActions = () => {
    api
      .governanceActions()
      .then(setActions)
      .catch((e) => setActions({ actions: [], error: String(e) }));
  };

  useEffect(() => {
    api.governance().then(setGov).catch((e) => setErr(String(e)));
    loadActions();
  }, []);

  if (err) return <ErrorNote error={`Failed to load governance: ${err}`} />;
  if (!gov) return <Loading label="Loading governance…" />;

  return (
    <div className="view">
      <h2 className="section">Governance — the control, not the glossary</h2>
      <p className="sub">
        Honest completeness, classification coverage, ownership and the
        attestation record behind every certified badge.
      </p>

      {/* Certification board */}
      <section className="detail-section">
        <h3 className="detail-h3">Certification board</h3>
        <div className="gauge-row">
          <Gauge
            label="Entities certified"
            done={gov.entities.certified}
            total={gov.entities.total}
          />
          <Gauge
            label="Metrics certified"
            done={gov.metrics.certified}
            total={gov.metrics.total}
            tone="accent"
          />
        </div>
        <div className="detail-note">
          {gov.entities.draft} entities and {gov.metrics.draft} metrics remain
          draft — the model does not claim more than it has attested.
        </div>
      </section>

      {/* Classification map */}
      <section className="detail-section">
        <h3 className="detail-h3">Classification map</h3>
        <p className="detail-note">
          Every attribute across the model, by data classification.
        </p>
        <ClassMap gov={gov} />
      </section>

      {/* Ownership board */}
      <section className="detail-section">
        <h3 className="detail-h3">Ownership board</h3>
        <p className="detail-note">Grouped by owning role. Expand to see elements.</p>
        <OwnershipBoard gov={gov} />
      </section>

      {/* Attestation record */}
      <section className="detail-section">
        <h3 className="detail-h3">Attestation record</h3>
        <p className="detail-note">
          The dated audit evidence behind every certified badge.
        </p>
        <div className="card scroll-x">
          <table>
            <thead>
              <tr>
                <th>Element</th>
                <th>Kind</th>
                <th>Cert</th>
                <th>Owner</th>
                <th>Attested by</th>
                <th>Attested on</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {gov.attestations.map((a) => (
                <tr key={`${a.element}-${a.element_kind}`}>
                  <td className="mono">{a.element}</td>
                  <td>{a.element_kind}</td>
                  <td>
                    <CertBadge c={a.certification} />
                  </td>
                  <td>{a.owner}</td>
                  <td>{a.attested_by}</td>
                  <td>{a.attested_on}</td>
                  <td className="def">{a.evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Regulatory links */}
      <section className="detail-section">
        <h3 className="detail-h3">Regulatory lineage</h3>
        <div className="chip-row">
          {REGIMES.map((r) => (
            <a
              key={r.id}
              className="chip link"
              href={href(['regulatory', r.id])}
              onClick={(e) => {
                e.preventDefault();
                navigate(href(['regulatory', r.id]));
              }}
            >
              {r.label} →
            </a>
          ))}
        </div>
      </section>

      {/* Propose a change / capture loop */}
      <section className="detail-section">
        <ProposeForm onSubmitted={loadActions} />
      </section>

      <section className="detail-section">
        <h3 className="detail-h3">Captured proposals & issues</h3>
        <p className="detail-note">
          Capture-only log. Each entry is a request to change the model — the
          truth stays in the specs until taken through the evolution contract.
        </p>
        <ActionsTable data={actions} />
      </section>
    </div>
  );
}
