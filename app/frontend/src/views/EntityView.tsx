import { useEffect, useState } from 'react';
import { api, EntityResponse, LineageResponse } from '../api';
import { href, navigate } from '../useHashRoute';
import LineageGraph from '../components/LineageGraph';
import { CertBadge, ClassBadge, ErrorNote, Loading } from '../components/ui';

function standardsPairs(s?: Record<string, string> | null): [string, string][] {
  if (!s) return [];
  return Object.entries(s);
}

export default function EntityView({ name }: { name: string }) {
  const [data, setData] = useState<EntityResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [lineage, setLineage] = useState<LineageResponse | null>(null);

  useEffect(() => {
    setData(null);
    setErr(null);
    setLineage(null);
    api.entity(name).then(setData).catch((e) => setErr(String(e)));
    api
      .lineage('entity', name, 1)
      .then(setLineage)
      .catch(() => setLineage(null));
  }, [name]);

  if (err) return <ErrorNote error={`Failed to load entity: ${err}`} />;
  if (!data) return <Loading label="Loading the entity…" />;

  const maturity = data.tags?.maturity;
  const crosswalk = standardsPairs(data.standards);

  return (
    <div className="view detail">
      <div className="detail-head">
        <div className="detail-kicker">Entity · {data.domain}</div>
        <h2 className="detail-title">
          {data.title || data.name}{' '}
          <CertBadge c={(maturity as string) === 'certified' ? 'certified' : maturity} />
        </h2>
        <div className="detail-owner">
          Owned by {data.owner}
          {data.grain && <span className="grain"> · grain: {data.grain}</span>}
        </div>
        <p className="detail-desc">{data.description}</p>
        {crosswalk.length > 0 && (
          <div className="crosswalk">
            <span className="crosswalk-label">Standards crosswalk:</span>
            {crosswalk.map(([k, v]) => (
              <span key={k} className="chip trust">
                {k}: {v}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Keys */}
      <section className="detail-section">
        <h3 className="detail-h3">Keys</h3>
        <div className="kv-row">
          <span className="kv-label">Primary</span>
          <span className="kv-val mono">
            {data.keys.primary?.length ? data.keys.primary.join(', ') : '—'}
          </span>
        </div>
        {data.keys.natural && data.keys.natural.length > 0 && (
          <div className="kv-row">
            <span className="kv-label">Natural</span>
            <span className="kv-val mono">{data.keys.natural.join(', ')}</span>
          </div>
        )}
      </section>

      {/* Attributes */}
      <section className="detail-section">
        <h3 className="detail-h3">Attributes</h3>
        <div className="card scroll-x">
          <table>
            <thead>
              <tr>
                <th>Attribute</th>
                <th>Type</th>
                <th>Req</th>
                <th>Definition</th>
                <th>Class</th>
                <th>Standards</th>
              </tr>
            </thead>
            <tbody>
              {data.attributes.map((a) => (
                <tr key={a.name}>
                  <td className="mono">{a.name}</td>
                  <td className="mono">{a.type}</td>
                  <td>
                    {a.required ? (
                      <span className="req">●</span>
                    ) : (
                      <span className="opt">○</span>
                    )}
                  </td>
                  <td className="def">{a.description}</td>
                  <td>
                    <ClassBadge c={a.classification} />
                  </td>
                  <td className="ref">
                    {standardsPairs(a.standards).length
                      ? standardsPairs(a.standards)
                          .map(([k, v]) => `${k}: ${v}`)
                          .join('  ')
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Quality */}
      {(data.quality?.length ?? 0) > 0 && (
        <section className="detail-section">
          <h3 className="detail-h3">Quality rules</h3>
          <div className="card scroll-x">
            <table>
              <thead>
                <tr>
                  <th>Rule</th>
                  <th>Expression</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {data.quality!.map((q) => (
                  <tr key={q.name}>
                    <td className="mono">{q.name}</td>
                    <td className="mono">{q.rule}</td>
                    <td className="def">{q.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* References */}
      {(data.references.length > 0 || data.referenced_by.length > 0) && (
        <section className="detail-section rel-grid">
          {data.references.length > 0 && (
            <div>
              <h3 className="detail-h3">References (this entity’s foreign keys)</h3>
              <div className="chip-row">
                {data.references.map((r, i) => (
                  <a
                    key={`${r.to}-${i}`}
                    className="chip link"
                    href={href(['entity', r.to])}
                    onClick={(e) => {
                      e.preventDefault();
                      navigate(href(['entity', r.to]));
                    }}
                  >
                    {r.attribute} → {r.to}
                  </a>
                ))}
              </div>
            </div>
          )}
          {data.referenced_by.length > 0 && (
            <div>
              <h3 className="detail-h3">Referenced by</h3>
              <div className="chip-row">
                {data.referenced_by.map((r, i) => (
                  <a
                    key={`${r.from}-${i}`}
                    className="chip link"
                    href={href(['entity', r.from])}
                    onClick={(e) => {
                      e.preventDefault();
                      navigate(href(['entity', r.from]));
                    }}
                  >
                    {r.from} · {r.attribute}
                  </a>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* Focused lineage */}
      <section className="detail-section">
        <h3 className="detail-h3">Lineage</h3>
        <p className="detail-note">
          The focused neighbourhood around this entity.{' '}
          <a
            href={href(['lineage', 'entity', name])}
            onClick={(e) => {
              e.preventDefault();
              navigate(href(['lineage', 'entity', name]));
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
