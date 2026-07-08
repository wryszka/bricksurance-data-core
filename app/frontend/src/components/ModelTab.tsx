import { useEffect, useState } from 'react';
import { api, Domain, Entity, ModelResponse } from '../api';

function classBadge(c: string | null) {
  if (!c) return null;
  return <span className={`badge ${c}`}>{c}</span>;
}

export default function ModelTab() {
  const [data, setData] = useState<ModelResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [domainIdx, setDomainIdx] = useState(0);
  const [entity, setEntity] = useState<Entity | null>(null);

  useEffect(() => {
    api
      .model()
      .then((d) => {
        setData(d);
        const first = d.domains[0];
        if (first?.entities.length) setEntity(first.entities[0]);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div className="result-note err">Failed to load model: {err}</div>;
  if (!data) return <div className="loading">Loading the model…</div>;

  const domain: Domain = data.domains[domainIdx];

  return (
    <>
      <div className="banner">
        Everything on this page is generated from versioned YAML specs — the business owns
        the model, the platform is an output.
      </div>
      <h2 className="section">Model — governance browser</h2>
      <p className="sub">
        Domains, entities and every attribute definition, read live from the deployed data
        dictionary and Unity Catalog table comments.
      </p>

      <div className="grid-3col">
        {/* Domains */}
        <div className="card list">
          <div className="list-head">Domains</div>
          {data.domains.map((d, i) => (
            <div
              key={d.domain}
              className={`list-item ${i === domainIdx ? 'active' : ''}`}
              onClick={() => {
                setDomainIdx(i);
                setEntity(d.entities[0] ?? null);
              }}
            >
              {d.title}
              <span className="count-pill">{d.entities.length}</span>
              <div className="meta">{d.schema}</div>
            </div>
          ))}
        </div>

        {/* Entities */}
        <div className="card list">
          <div className="list-head">Entities in {domain.title}</div>
          {domain.entities.map((e) => (
            <div
              key={e.name}
              className={`list-item ${entity?.name === e.name ? 'active' : ''}`}
              onClick={() => setEntity(e)}
            >
              {e.name}
              <div className="meta">
                {e.type} · {e.attributes.length} attributes
              </div>
            </div>
          ))}
        </div>

        {/* Attributes */}
        <div className="card">
          {entity && (
            <>
              <div className="entity-head">
                <h3>{entity.name}</h3>
                <div className="cmt">{entity.comment}</div>
                <div style={{ marginTop: 10 }}>
                  <a href={data.model_repo_url} target="_blank" rel="noreferrer">
                    View the YAML spec ↗
                  </a>
                </div>
              </div>
              <div className="scroll-x">
                {entity.attributes.length === 0 ? (
                  <div className="loading">
                    No dictionary rows for this object (views inherit their definitions from
                    the underlying entities).
                  </div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Attribute</th>
                        <th>Type</th>
                        <th>Req</th>
                        <th>Definition</th>
                        <th>Class</th>
                        <th>ACORD</th>
                        <th>Lloyd's CDR</th>
                      </tr>
                    </thead>
                    <tbody>
                      {entity.attributes.map((a) => (
                        <tr key={a.attribute}>
                          <td className="mono">{a.attribute}</td>
                          <td className="mono">{a.type}</td>
                          <td>
                            {a.required ? (
                              <span className="req">●</span>
                            ) : (
                              <span className="opt">○</span>
                            )}
                          </td>
                          <td className="def">{a.definition}</td>
                          <td>{classBadge(a.classification)}</td>
                          <td className="ref">{a.acord_ref || '—'}</td>
                          <td className="ref">{a.lloyds_cdr_ref || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
