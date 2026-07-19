import { useEffect, useState } from 'react';
import { api, MetaResponse } from './api';
import { href, navigate, useHashRoute } from './useHashRoute';
import HomeView from './views/HomeView';
import SearchView from './views/SearchView';
import MetricView from './views/MetricView';
import EntityView from './views/EntityView';
import CodeSetView from './views/CodeSetView';
import FunctionView from './views/FunctionView';
import LineageView from './views/LineageView';
import GovernanceView from './views/GovernanceView';
import RegulatoryView from './views/RegulatoryView';
import EngineersView from './views/EngineersView';
import ExchangeTab from './components/ExchangeTab';
import NetworkTab from './components/NetworkTab';

const NAV = [
  { to: '#/', label: 'Home', match: (p: string) => p === '' || p.startsWith('search') || p.startsWith('metric') || p.startsWith('entity') || p.startsWith('code_set') || p.startsWith('function') || p.startsWith('lineage') },
  { to: '#/governance', label: 'Governance', match: (p: string) => p.startsWith('governance') || p.startsWith('regulatory') },
  { to: '#/exchange', label: 'Exchange', match: (p: string) => p.startsWith('exchange') },
  { to: '#/network', label: 'Network', match: (p: string) => p.startsWith('network') },
  { to: '#/engineers', label: 'For engineers', match: (p: string) => p.startsWith('engineers') },
];

function AboutPanel({ onClose }: { onClose: () => void }) {
  return (
    <div className="docs-overlay" onClick={onClose}>
      <div className="docs-panel about-panel" onClick={(e) => e.stopPropagation()}>
        <div className="docs-panel-head">
          <div>
            <h3>About this demo</h3>
            <div className="docs-panel-sub">
              A Databricks Field Engineering reference implementation.
            </div>
          </div>
          <button className="docs-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="about-body">
          <p>
            <strong>Bricksurance SE</strong> is a fictional insurance group. All
            data is synthetic.
          </p>
          <p>
            This is a Databricks Field Engineering reference implementation of a{' '}
            <strong>proposed ACORD / Lloyd’s-aligned insurance data model</strong>{' '}
            — a starting point you fork and own, not licensed standard content.
          </p>
        </div>
      </div>
    </div>
  );
}

function HeaderSearch({ initial }: { initial?: string }) {
  const [q, setQ] = useState(initial || '');
  useEffect(() => setQ(initial || ''), [initial]);
  return (
    <form
      className="header-search"
      onSubmit={(e) => {
        e.preventDefault();
        const t = q.trim();
        if (t) navigate(href(['search', t]));
      }}
    >
      <input
        className="header-search-input"
        placeholder="Search a term…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
    </form>
  );
}

export default function App() {
  const { route } = useHashRoute();
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [aboutOpen, setAboutOpen] = useState(false);

  useEffect(() => {
    api.meta().then(setMeta).catch(() => setMeta(null));
  }, []);

  const parts = route.parts;
  const head = parts[0] || '';
  const isHome = head === '';

  const renderView = () => {
    switch (head) {
      case '':
        return <HomeView meta={meta} />;
      case 'search':
        return <SearchView term={parts.slice(1).join('/') || ''} />;
      case 'metric':
        return <MetricView key={parts[1]} name={parts[1] || ''} />;
      case 'entity':
        return <EntityView key={parts[1]} name={parts[1] || ''} />;
      case 'code_set':
        return <CodeSetView key={parts[1]} name={parts[1] || ''} />;
      case 'function':
        return <FunctionView key={parts[1]} name={parts[1] || ''} />;
      case 'lineage':
        return (
          <LineageView
            key={`${parts[1]}/${parts[2]}`}
            kind={parts[1] || 'entity'}
            name={parts[2] || ''}
          />
        );
      case 'governance':
        return <GovernanceView />;
      case 'regulatory':
        return <RegulatoryView key={parts[1]} regime={parts[1] || 'solvency_ii'} />;
      case 'exchange':
        return <ExchangeTab />;
      case 'network':
        return <NetworkTab />;
      case 'engineers':
        return <EngineersView meta={meta} />;
      default:
        return (
          <div className="view">
            <div className="empty-note">
              Nothing here. <a href="#/">Back to the front door →</a>
            </div>
          </div>
        );
    }
  };

  const searchTerm = head === 'search' ? parts.slice(1).join('/') : '';
  const version = meta?.version || meta?.provenance?.version;

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <a
            className="brand brand-link"
            href="#/"
            onClick={(e) => {
              e.preventDefault();
              navigate('#/');
            }}
          >
            Bricksurance <span className="accent">Data Core</span> Atlas
          </a>
          {!isHome && <HeaderSearch initial={searchTerm} />}
          <button className="docs-btn" onClick={() => setAboutOpen(true)}>
            About this demo
          </button>
        </div>
        <nav className="tabs">
          {NAV.map((n) => (
            <a
              key={n.to}
              className={`tab ${n.match(head) ? 'active' : ''}`}
              href={n.to}
              onClick={(e) => {
                e.preventDefault();
                navigate(n.to);
              }}
            >
              {n.label}
            </a>
          ))}
        </nav>
      </header>

      <div className="framing">
        <strong>
          One agreed language for your insurance business — and the data, metrics
          and AI answers built from it.
        </strong>{' '}
        <span className="framing-sub">
          An ACORD &amp; Lloyd’s-aligned starting point you own — generated from one
          versioned ontology.
        </span>
      </div>

      <main className="main">{renderView()}</main>

      <footer className="footer">
        <div className="provenance">
          Generated from bricksurance-data-core v{version || '…'} · bundled ontology
        </div>
        <div>
          Bricksurance SE is a fictional insurance group. All data is synthetic. Demo
          by Databricks Field Engineering.
        </div>
      </footer>

      {aboutOpen && <AboutPanel onClose={() => setAboutOpen(false)} />}
    </div>
  );
}
