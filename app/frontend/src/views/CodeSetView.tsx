import { useEffect, useState } from 'react';
import { api, CodeSetResponse } from '../api';
import { href, navigate } from '../useHashRoute';
import { ErrorNote, Loading } from '../components/ui';

export default function CodeSetView({ name }: { name: string }) {
  const [data, setData] = useState<CodeSetResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setErr(null);
    api.codeSet(name).then(setData).catch((e) => setErr(String(e)));
  }, [name]);

  if (err) return <ErrorNote error={`Failed to load code set: ${err}`} />;
  if (!data) return <Loading label="Loading the code set…" />;

  return (
    <div className="view detail">
      <div className="detail-head">
        <div className="detail-kicker">Code set</div>
        <h2 className="detail-title">{data.title || data.name}</h2>
        <p className="detail-desc">{data.description}</p>
        <div className="detail-note">
          <a
            href={href(['lineage', 'code_set', name])}
            onClick={(e) => {
              e.preventDefault();
              navigate(href(['lineage', 'code_set', name]));
            }}
          >
            See where this code set is used →
          </a>
        </div>
      </div>

      <section className="detail-section">
        <h3 className="detail-h3">Codes ({data.codes.length})</h3>
        <div className="card scroll-x">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Label</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {data.codes.map((c) => (
                <tr key={c.code}>
                  <td className="mono">{c.code}</td>
                  <td>{c.label}</td>
                  <td className="def">{c.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
