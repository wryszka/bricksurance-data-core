import { useEffect, useRef, useState } from 'react';
import { api, MetaResponse } from '../api';
import { href } from '../useHashRoute';

const ROLES = [
  {
    id: 'cdo',
    label: 'CDO',
    line: 'Your governance policy becomes the system, not a PDF nobody follows.',
  },
  {
    id: 'cfo',
    label: 'CFO',
    line: 'One agreed definition of loss ratio, incurred, reserves — the number reconciles, and you can audit how it was built.',
  },
  {
    id: 'actuary',
    label: 'Chief Actuary',
    line: 'Your vocabulary, enforced everywhere, queryable in plain English — no fork of the truth.',
  },
] as const;

const EXAMPLES = [
  'loss ratio',
  'SCR',
  'ceded premium',
  'outstanding reserve',
  'where is personal data',
];

export default function HomeView({ meta }: { meta: MetaResponse | null }) {
  const [q, setQ] = useState('');
  const [role, setRole] = useState<(typeof ROLES)[number]['id']>('cdo');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const submit = (term: string) => {
    const t = term.trim();
    if (t) window.location.hash = href(['search', t]).slice(1);
  };

  const c = meta?.counts;
  const chips = c
    ? [
        `${c.entities} entities`,
        `${c.metric_views} governed metrics`,
        `${c.functions} functions`,
        `${c.domains} domains`,
        'ACORD & Lloyd’s aligned',
      ]
    : [];

  return (
    <div className="home">
      <div className="home-hero">
        <h1 className="home-headline">
          One agreed language for your insurance business — and the data, metrics
          and AI answers built from it.
        </h1>
        <p className="home-sub">
          Search any business term and see everything that makes it real: the
          governed definition, its owner, the exact SQL, the datasets feeding it,
          a focused lineage, and a one-click answer in Genie.
        </p>

        <form
          className="home-search"
          onSubmit={(e) => {
            e.preventDefault();
            submit(q);
          }}
        >
          <input
            ref={inputRef}
            className="home-search-input"
            placeholder="Search a business term — e.g. loss ratio, ceded premium, SCR"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button className="btn primary" type="submit">
            Search
          </button>
        </form>

        <div className="chip-row">
          {EXAMPLES.map((ex) => (
            <button key={ex} className="chip example" onClick={() => submit(ex)}>
              {ex}
            </button>
          ))}
        </div>

        {chips.length > 0 && (
          <div className="chip-row trust">
            {chips.map((t) => (
              <span key={t} className="chip trust">
                {t}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="role-toggle card">
        <div className="role-tabs">
          {ROLES.map((r) => (
            <button
              key={r.id}
              className={`role-tab ${role === r.id ? 'active' : ''}`}
              onClick={() => setRole(r.id)}
            >
              {r.label}
            </button>
          ))}
        </div>
        <p className="role-line">
          {ROLES.find((r) => r.id === role)?.line}
        </p>
      </div>

      <div className="ba-strip">
        <div className="ba-col ba-before">
          <div className="ba-tag">Ask an LLM over bare tables</div>
          <p>
            It guesses, hedges, and picks the wrong column. Every team gets a
            slightly different number — and no one can say which is right.
          </p>
        </div>
        <div className="ba-arrow">→</div>
        <div className="ba-col ba-after">
          <div className="ba-tag">Ask over the semantic layer</div>
          <p>
            The reconciling number, from the governed definition — with the exact
            formula and its owner attached. See it proven live on any metric page.
          </p>
        </div>
      </div>
    </div>
  );
}
