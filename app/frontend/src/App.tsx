import { useState } from 'react';
import ModelTab from './components/ModelTab';
import NumbersTab from './components/NumbersTab';
import ExchangeTab from './components/ExchangeTab';
import NetworkTab from './components/NetworkTab';

const TABS = [
  { id: 'model', label: 'Model' },
  { id: 'numbers', label: 'Numbers' },
  { id: 'exchange', label: 'Exchange' },
  { id: 'network', label: 'Network' },
] as const;

type TabId = (typeof TABS)[number]['id'];

export default function App() {
  const [tab, setTab] = useState<TabId>('model');
  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <span className="brand">
            Bricksurance <span className="accent">Data Core</span> Console
          </span>
          <span className="tagline">One business-first semantic model for insurance</span>
        </div>
        <nav className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="main">
        {tab === 'model' && <ModelTab />}
        {tab === 'numbers' && <NumbersTab />}
        {tab === 'exchange' && <ExchangeTab />}
        {tab === 'network' && <NetworkTab />}
      </main>

      <footer className="footer">
        Bricksurance SE is a fictional insurance group. All data is synthetic. Demo by
        Databricks Field Engineering.
      </footer>
    </div>
  );
}
