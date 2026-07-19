import { useState } from 'react';
import { AtlasKind, Certification } from '../api';

export function Loading({ label }: { label?: string }) {
  return <div className="loading">{label || 'Loading…'}</div>;
}

export function ErrorNote({ error }: { error: string }) {
  return <div className="result-note err">{error}</div>;
}

// Copy-to-clipboard button used on every SQL block and Genie question.
export function CopyButton({
  text,
  label = 'Copy',
}: {
  text: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Fallback for insecure contexts
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand('copy');
      } catch {
        /* noop */
      }
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };
  return (
    <button className="copy-btn" onClick={onCopy} type="button">
      {copied ? 'Copied' : label}
    </button>
  );
}

export function SqlBlock({ sql }: { sql: string }) {
  return (
    <div className="sql-block">
      <div className="sql-block-bar">
        <span className="sql-block-tag">SQL</span>
        <CopyButton text={sql} />
      </div>
      <pre className="sql-code">{sql}</pre>
    </div>
  );
}

export function ClassBadge({ c }: { c: string | null | undefined }) {
  if (!c) return null;
  return <span className={`badge ${c}`}>{c}</span>;
}

export function CertBadge({ c }: { c: Certification | undefined | null }) {
  if (!c) return null;
  const cls = c === 'certified' ? 'cert-certified' : 'cert-draft';
  return <span className={`badge cert ${cls}`}>{c}</span>;
}

export function KindPill({ kind }: { kind: AtlasKind | string }) {
  const label =
    kind === 'code_set' ? 'code set' : kind === 'metric_view' ? 'metric' : kind;
  return <span className={`kind-pill kind-${kind}`}>{label}</span>;
}
