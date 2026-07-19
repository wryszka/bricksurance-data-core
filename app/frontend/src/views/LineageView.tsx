import { useCallback, useEffect, useState } from 'react';
import { api, LineageResponse } from '../api';
import { href, navigate } from '../useHashRoute';
import LineageGraph from '../components/LineageGraph';
import { ErrorNote, Loading } from '../components/ui';

function routeForNode(kind: string, name: string): string | null {
  if (kind === 'entity') return href(['entity', name]);
  if (kind === 'metric') return href(['metric', name]);
  if (kind === 'code_set') return href(['code_set', name]);
  if (kind === 'function') return href(['function', name]);
  return null;
}

export default function LineageView({
  kind,
  name,
}: {
  kind: string;
  name: string;
}) {
  const golden = kind === 'golden-thread';
  const [depth, setDepth] = useState(1);
  const [data, setData] = useState<LineageResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(() => {
    setData(null);
    setErr(null);
    const p = golden ? api.goldenThread() : api.lineage(kind, name, depth);
    p.then(setData).catch((e) => setErr(String(e)));
  }, [golden, kind, name, depth]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="view lineage-view">
      <div className="lineage-toolbar">
        <div>
          <h2 className="section">
            {golden ? 'Golden thread' : `Lineage — ${name}`}
          </h2>
          <p className="sub">
            {golden
              ? 'The saved end-to-end path through the model.'
              : 'The focused neighbourhood — only the edges around this node, never all 195.'}
          </p>
        </div>
        <div className="lineage-controls">
          {!golden && (
            <div className="depth-control">
              <span className="depth-label">Depth</span>
              <button
                className={`seg ${depth === 1 ? 'active' : ''}`}
                onClick={() => setDepth(1)}
              >
                1 hop
              </button>
              <button
                className={`seg ${depth === 2 ? 'active' : ''}`}
                onClick={() => setDepth(2)}
              >
                2 hops
              </button>
            </div>
          )}
          <button
            className="btn accent"
            onClick={() => navigate(href(['lineage', 'golden-thread', 'demo']))}
          >
            Golden thread
          </button>
        </div>
      </div>

      {golden && data?.narrative && (
        <div className="narrative-note">{data.narrative}</div>
      )}

      {err && <ErrorNote error={`Failed to load lineage: ${err}`} />}
      {!data && !err && <Loading label="Building the graph…" />}

      {data && (
        <div className="card lineage-full-wrap">
          <LineageGraph
            data={data}
            height={560}
            interactive
            onNodeClick={(n) => {
              const r = routeForNode(n.kind, n.name);
              if (r) navigate(r);
            }}
            onExpand={(n) => {
              if (n.kind === 'entity' || n.kind === 'metric' || n.kind === 'code_set') {
                navigate(href(['lineage', n.kind, n.name]));
              }
            }}
          />
          <div className="lineage-hint">
            Click a node to open its detail · double-click to re-centre the graph
            on it.
          </div>
        </div>
      )}
    </div>
  );
}
