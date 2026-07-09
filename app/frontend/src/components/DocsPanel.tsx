import { DOC_ORDER, REPO } from '../docs';

export default function DocsPanel({ onClose }: { onClose: () => void }) {
  return (
    <div className="docs-overlay" onClick={onClose}>
      <div className="docs-panel" onClick={(e) => e.stopPropagation()}>
        <div className="docs-panel-head">
          <div>
            <h3>Documents</h3>
            <div className="docs-panel-sub">
              The full write-up behind Data Core — what it is, how to run it, and how it grows.
            </div>
          </div>
          <button className="docs-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="docs-list">
          {DOC_ORDER.map((d) => (
            <a key={d.key} className="docs-item" href={d.url} target="_blank" rel="noreferrer">
              <span className="docs-item-title">{d.title} →</span>
              <span className="docs-item-desc">{d.description}</span>
            </a>
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
