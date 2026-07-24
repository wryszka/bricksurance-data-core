import { DEMO_ORDER, DOC_ORDER, REPO, DocLink } from '../docs';

function DocItem({ d }: { d: DocLink }) {
  return (
    <a className="docs-item" href={d.url} target="_blank" rel="noreferrer">
      <span className="docs-item-title">{d.title} →</span>
      <span className="docs-item-desc">{d.description}</span>
    </a>
  );
}

export default function DocsPanel({ onClose }: { onClose: () => void }) {
  return (
    <div className="docs-overlay" onClick={onClose}>
      <div className="docs-panel" onClick={(e) => e.stopPropagation()}>
        <div className="docs-panel-head">
          <div>
            <h3>Documents</h3>
            <div className="docs-panel-sub">
              Demo run-throughs to present with, and the full write-up behind Data Core.
            </div>
          </div>
          <button className="docs-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="docs-list">
          <div className="docs-group-head">Demo run-throughs</div>
          {DEMO_ORDER.map((d) => (
            <DocItem key={d.key} d={d} />
          ))}
          <div className="docs-group-head">Reference documentation</div>
          {DOC_ORDER.map((d) => (
            <DocItem key={d.key} d={d} />
          ))}
          <a className="docs-item repo" href={REPO.url} target="_blank" rel="noreferrer">
            <span className="docs-item-title">{REPO.title} →</span>
            <span className="docs-item-desc">{REPO.description}</span>
          </a>
        </div>
      </div>
    </div>
  );
}
