import { useEffect, useState } from 'react';
import { api, FunctionResponse } from '../api';
import { ErrorNote, Loading, SqlBlock } from '../components/ui';

function renderInputs(inputs: FunctionResponse['inputs']): string {
  if (!inputs) return '—';
  if (typeof inputs === 'string') return inputs;
  if (Array.isArray(inputs)) {
    return inputs
      .map((i) =>
        typeof i === 'string' ? i : `${i.name}${i.type ? `: ${i.type}` : ''}`,
      )
      .join(', ');
  }
  return String(inputs);
}

export default function FunctionView({ name }: { name: string }) {
  const [data, setData] = useState<FunctionResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setErr(null);
    api.atlasFunction(name).then(setData).catch((e) => setErr(String(e)));
  }, [name]);

  if (err) return <ErrorNote error={`Failed to load function: ${err}`} />;
  if (!data) return <Loading label="Loading the function…" />;

  return (
    <div className="view detail">
      <div className="detail-head">
        <div className="detail-kicker">Function · {data.domain}</div>
        <h2 className="detail-title">{data.title || data.name}</h2>
        <p className="detail-desc">{data.description}</p>
      </div>

      <section className="detail-section">
        <div className="kv-row">
          <span className="kv-label">Inputs</span>
          <span className="kv-val mono">{renderInputs(data.inputs)}</span>
        </div>
        <div className="kv-row">
          <span className="kv-label">Returns</span>
          <span className="kv-val mono">{data.returns || '—'}</span>
        </div>
      </section>

      <section className="detail-section">
        <h3 className="detail-h3">Definition</h3>
        <SqlBlock sql={data.sql} />
      </section>
    </div>
  );
}
