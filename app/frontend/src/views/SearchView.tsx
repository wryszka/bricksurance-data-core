import { useEffect, useState } from 'react';
import { api, SearchResponse, SearchResult } from '../api';
import { href, navigate } from '../useHashRoute';
import { CertBadge, ErrorNote, KindPill, Loading } from '../components/ui';

function resultHref(r: SearchResult): string {
  switch (r.kind) {
    case 'metric':
      return href(['metric', r.name]);
    case 'entity':
      return href(['entity', r.name]);
    case 'code_set':
      return href(['code_set', r.name]);
    case 'function':
      return href(['function', r.name]);
    case 'view':
      return href(['entity', r.name]);
    default:
      return href(['search', r.name]);
  }
}

export default function SearchView({ term }: { term: string }) {
  const [data, setData] = useState<SearchResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setErr(null);
    api.search(term).then(setData).catch((e) => setErr(String(e)));
  }, [term]);

  return (
    <div className="view">
      <h2 className="section">
        Results for “{term}”
        {data && <span className="result-count"> · {data.results.length}</span>}
      </h2>
      <p className="sub">
        Every hit is a business object — a governed metric, entity, code set or
        function — with a plain-English summary, its owner and certification.
      </p>

      {err && <ErrorNote error={err} />}
      {!data && !err && <Loading label="Searching the ontology…" />}

      {data?.roadmap && (
        <div className="roadmap-note">
          <strong>On the roadmap.</strong> “{data.roadmap.term}” isn’t in the
          model yet. {data.roadmap.note}
        </div>
      )}

      {data && data.results.length === 0 && !data.roadmap && (
        <div className="empty-note">
          No matches. Try a business term like “loss ratio”, “ceded premium” or
          “outstanding reserve”.
        </div>
      )}

      <div className="result-list">
        {data?.results.map((r) => (
          <a
            key={`${r.kind}:${r.name}`}
            className="result-tile card"
            href={resultHref(r)}
            onClick={(e) => {
              e.preventDefault();
              navigate(resultHref(r));
            }}
          >
            <div className="result-tile-top">
              <KindPill kind={r.kind} />
              <span className="result-domain">{r.domain}</span>
            </div>
            <div className="result-title">{r.title || r.name}</div>
            <div className="result-summary">{r.summary}</div>
            {(r.owner || r.certification) && (
              <div className="result-meta">
                {r.owner && <span className="result-owner">{r.owner}</span>}
                <CertBadge c={r.certification} />
              </div>
            )}
          </a>
        ))}
      </div>
    </div>
  );
}
