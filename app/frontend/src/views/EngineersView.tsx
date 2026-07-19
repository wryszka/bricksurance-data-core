import { MetaResponse } from '../api';
import { DOCS, REPO } from '../docs';

export default function EngineersView({ meta }: { meta: MetaResponse | null }) {
  const version = meta?.version || meta?.provenance?.version || '—';
  const c = meta?.counts;
  return (
    <div className="view">
      <h2 className="section">For engineers — the machinery</h2>
      <p className="sub">
        The technical backing behind everything on the exec path. This is model-as-code:
        the ontology is versioned YAML; the Databricks and Snowflake artifacts are
        generated from it, so the model can never drift from what’s deployed.
      </p>

      <div className="eng-grid">
        <div className="card eng-card">
          <h3 className="detail-h3">Ontology & version</h3>
          <div className="kv-row">
            <span className="kv-label">Version</span>
            <span className="kv-val mono">{version}</span>
          </div>
          <div className="kv-row">
            <span className="kv-label">Standards basis</span>
            <span className="kv-val">{meta?.standards_basis || 'ACORD / Lloyd’s aligned'}</span>
          </div>
          <p className="detail-note">
            An aligned starting point you fork and own — not licensed standard content.
          </p>
          <div className="btn-row">
            <a className="btn ghost" href={REPO.url} target="_blank" rel="noreferrer">
              Ontology export / install ↗
            </a>
          </div>
        </div>

        {c && (
          <div className="card eng-card">
            <h3 className="detail-h3">Counts</h3>
            <div className="eng-counts">
              <div><b>{c.domains}</b> domains</div>
              <div><b>{c.entities}</b> entities</div>
              <div><b>{c.code_sets}</b> code sets</div>
              <div><b>{c.metric_views}</b> metric views</div>
              <div><b>{c.functions}</b> functions</div>
              <div><b>{c.relationships}</b> relationships</div>
            </div>
          </div>
        )}

        <div className="card eng-card">
          <h3 className="detail-h3">Model-as-code & evolution</h3>
          <p className="detail-note">
            YAML specs are the single source of truth; a generator emits Databricks
            (Unity Catalog, metric views, functions) and Snowflake artifacts. Changes
            move through a semver’d evolution contract — proposals captured on the
            Governance page become diff stubs against the specs.
          </p>
          <div className="docs-list eng-docs">
            {[DOCS.design, DOCS.evolution, DOCS.tagging, DOCS.metrics, DOCS.gettingStarted].map(
              (d) => (
                <a key={d.key} className="docs-item" href={d.url} target="_blank" rel="noreferrer">
                  <span className="docs-item-title">{d.title} →</span>
                  <span className="docs-item-desc">{d.description}</span>
                </a>
              ),
            )}
            <a className="docs-item repo" href={REPO.url} target="_blank" rel="noreferrer">
              <span className="docs-item-title">{REPO.title} →</span>
              <span className="docs-item-desc">{REPO.description}</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
