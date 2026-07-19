import { useEffect, useState } from 'react';
import { api, RegulatoryResponse } from '../api';
import { href, navigate } from '../useHashRoute';
import { CertBadge, ErrorNote, KindPill, Loading } from '../components/ui';

const REGIMES = [
  { id: 'solvency_ii', label: 'Solvency II' },
  { id: 'ifrs_17', label: 'IFRS 17' },
  { id: 'gdpr', label: 'GDPR' },
];

function cardHref(kind: string, name: string): string {
  if (kind === 'metric') return href(['metric', name]);
  if (kind === 'code_set') return href(['code_set', name]);
  if (kind === 'function') return href(['function', name]);
  return href(['entity', name]);
}

export default function RegulatoryView({ regime }: { regime: string }) {
  const [data, setData] = useState<RegulatoryResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setErr(null);
    api.regulatory(regime).then(setData).catch((e) => setErr(String(e)));
  }, [regime]);

  return (
    <div className="view">
      <div className="seg-control">
        {REGIMES.map((r) => (
          <button
            key={r.id}
            className={`seg ${r.id === regime ? 'active' : ''}`}
            onClick={() => navigate(href(['regulatory', r.id]))}
          >
            {r.label}
          </button>
        ))}
      </div>

      {err && <ErrorNote error={`Failed to load regulatory view: ${err}`} />}
      {!data && !err && <Loading label="Resolving the regime…" />}

      {data && (
        <>
          <h2 className="section">{data.title}</h2>
          <p className="sub">{data.blurb}</p>
          {data.consumed_by && (
            <div className="consumed-note">
              Consumed by <strong>{data.consumed_by}</strong>
            </div>
          )}

          <div className="result-list">
            {data.resolved.map((r) => (
              <a
                key={`${r.kind}:${r.name}`}
                className="result-tile card"
                href={cardHref(r.kind, r.name)}
                onClick={(e) => {
                  e.preventDefault();
                  navigate(cardHref(r.kind, r.name));
                }}
              >
                <div className="result-tile-top">
                  <KindPill kind={r.kind} />
                  <span className="result-domain">{r.domain}</span>
                </div>
                <div className="result-title">{r.title || r.name}</div>
                {(r.owner || r.certification) && (
                  <div className="result-meta">
                    {r.owner && <span className="result-owner">{r.owner}</span>}
                    <CertBadge c={r.certification} />
                  </div>
                )}
              </a>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
