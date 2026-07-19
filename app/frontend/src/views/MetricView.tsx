import { useEffect, useState } from 'react';
import {
  api,
  GenieHealthResponse,
  LineageResponse,
  MetricResponse,
  num,
  ProveResponse,
} from '../api';
import { href, navigate } from '../useHashRoute';
import LineageGraph from '../components/LineageGraph';
import {
  CertBadge,
  CopyButton,
  ErrorNote,
  Loading,
  SqlBlock,
} from '../components/ui';

export default function MetricView({ name }: { name: string }) {
  const [data, setData] = useState<MetricResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [lineage, setLineage] = useState<LineageResponse | null>(null);

  const [prove, setProve] = useState<ProveResponse | null>(null);
  const [proving, setProving] = useState(false);
  const [genie, setGenie] = useState<GenieHealthResponse | null>(null);
  const [genieBusy, setGenieBusy] = useState(false);
  const [genieChecked, setGenieChecked] = useState(false);

  useEffect(() => {
    setData(null);
    setErr(null);
    setLineage(null);
    setProve(null);
    setGenie(null);
    setGenieChecked(false);
    api.metric(name).then(setData).catch((e) => setErr(String(e)));
    api
      .lineage('metric', name, 1)
      .then(setLineage)
      .catch(() => setLineage(null));
  }, [name]);

  const runProve = async () => {
    setProving(true);
    try {
      setProve(await api.prove(name));
    } catch (e) {
      setProve({
        metric: name,
        ok: false,
        error: String(e),
        sql: '',
        measures: [],
        genie_question: data?.genie_question || '',
        genie_space_url: data?.genie_space_url || '',
      });
    } finally {
      setProving(false);
    }
  };

  const checkGenie = async () => {
    setGenieBusy(true);
    try {
      const h = await api.genieHealth();
      setGenie(h);
      setGenieChecked(true);
      if (h.ready && h.genie_space_url) {
        window.open(h.genie_space_url, '_blank', 'noopener');
      }
    } catch (e) {
      setGenie({
        warehouse: 'cold',
        genie_space_url: data?.genie_space_url || '',
        ready: false,
        detail: String(e),
      });
      setGenieChecked(true);
    } finally {
      setGenieBusy(false);
    }
  };

  if (err) return <ErrorNote error={`Failed to load metric: ${err}`} />;
  if (!data) return <Loading label="Loading the metric…" />;

  const draft = data.certification !== 'certified';

  return (
    <div className="view detail">
      <div className="detail-head">
        <div className="detail-kicker">Governed metric · {data.domain}</div>
        <h2 className="detail-title">
          {data.title || data.name} <CertBadge c={data.certification} />
        </h2>
        <div className="detail-owner">Owned by {data.owner}</div>
        <p className={`detail-desc ${draft ? 'has-caveat' : ''}`}>
          {data.description}
        </p>
        {draft && (
          <div className="caveat-note">
            This metric is <strong>draft</strong> — not yet attested. Treat the
            number as indicative until certified.
          </div>
        )}
      </div>

      {/* Measures — the exact SQL */}
      <section className="detail-section">
        <h3 className="detail-h3">Measures</h3>
        <p className="detail-note">
          Each measure is defined once, here, as the single source of truth.
        </p>
        <div className="measure-list">
          {data.measures.map((m) => (
            <div key={m.name} className="measure-card card">
              <div className="measure-head">
                <span className="measure-name mono">{m.name}</span>
              </div>
              {m.description && (
                <div className="measure-desc">{m.description}</div>
              )}
              <div className="sql-block inline">
                <div className="sql-block-bar">
                  <span className="sql-block-tag">formula</span>
                  <CopyButton text={m.expr} />
                </div>
                <pre className="sql-code">{m.expr}</pre>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Feeds from */}
      {data.feeds_from.length > 0 && (
        <section className="detail-section">
          <h3 className="detail-h3">Feeds from</h3>
          <p className="detail-note">
            The source and join tables this metric is built on.
          </p>
          <div className="chip-row">
            {data.feeds_from.map((f, i) => {
              const label = `${f.entity}${f.role ? ` · ${f.role}` : ''}`;
              if (f.exists) {
                return (
                  <a
                    key={`${f.entity}-${i}`}
                    className="chip link"
                    href={href(['entity', f.entity])}
                    onClick={(e) => {
                      e.preventDefault();
                      navigate(href(['entity', f.entity]));
                    }}
                  >
                    {label}
                  </a>
                );
              }
              return (
                <span key={`${f.entity}-${i}`} className="chip disabled" title="not a resolvable entity">
                  {label}
                </span>
              );
            })}
          </div>
        </section>
      )}

      {/* Prove it live */}
      <section className="detail-section">
        <h3 className="detail-h3">Prove it live</h3>
        <p className="detail-note">
          Run the governed definition against the warehouse and see the number.
        </p>
        <div className="btn-row">
          <button className="btn accent" onClick={runProve} disabled={proving}>
            {proving ? 'Proving…' : 'Prove it live'}
          </button>
        </div>

        {prove && prove.ok && (
          <div className="prove-grid">
            {prove.measures.map((m) => (
              <div key={m.name} className="prove-card card">
                <div className="prove-value">{num(m.value)}</div>
                <div className="prove-name mono">{m.name}</div>
                <div className="prove-formula mono">{m.formula}</div>
              </div>
            ))}
          </div>
        )}

        {prove && !prove.ok && (
          <div className="cold-card card">
            <div className="cold-head">
              Warehouse is cold — here’s the query that proves it
            </div>
            {prove.error && <div className="cold-err">{prove.error}</div>}
            {prove.sql && <SqlBlock sql={prove.sql} />}
          </div>
        )}
      </section>

      {/* Ask in Genie */}
      <section className="detail-section">
        <h3 className="detail-h3">Ask in Genie</h3>
        <p className="detail-note">
          Ask this in plain English over the governed model.
        </p>
        <div className="genie-question">
          <span className="genie-q-text">{data.genie_question}</span>
          <CopyButton text={data.genie_question} label="Copy question" />
        </div>
        <div className="btn-row">
          <button className="btn primary" onClick={checkGenie} disabled={genieBusy}>
            {genieBusy ? 'Checking Genie…' : 'Ask in Genie'}
          </button>
        </div>
        {genieChecked && genie && !genie.ready && (
          <div className="cold-card card">
            <div className="cold-head">
              Genie space isn’t warm right now — ask it directly in SQL instead
            </div>
            {genie.detail && <div className="cold-err">{genie.detail}</div>}
            {data.measures[0] && <SqlBlock sql={data.measures[0].expr} />}
          </div>
        )}
        {genieChecked && genie && genie.ready && (
          <div className="result-note ok">
            Opened the Genie space in a new tab — type the question above.
          </div>
        )}
      </section>

      {/* Focused lineage */}
      <section className="detail-section">
        <h3 className="detail-h3">Lineage</h3>
        <p className="detail-note">
          The focused neighbourhood around this metric.{' '}
          <a
            href={href(['lineage', 'metric', name])}
            onClick={(e) => {
              e.preventDefault();
              navigate(href(['lineage', 'metric', name]));
            }}
          >
            Open the full lineage →
          </a>
        </p>
        {lineage ? (
          <LineageGraph
            data={lineage}
            height={320}
            onNodeClick={(n) => {
              if (n.kind === 'entity') navigate(href(['entity', n.name]));
              else if (n.kind === 'metric') navigate(href(['metric', n.name]));
              else if (n.kind === 'code_set') navigate(href(['code_set', n.name]));
            }}
          />
        ) : (
          <Loading label="Loading lineage…" />
        )}
      </section>
    </div>
  );
}
