import { DocLink } from '../docs';

interface Props {
  seeing: string;
  matters: string;
  links: DocLink[];
}

export default function PurposeCard({ seeing, matters, links }: Props) {
  return (
    <div className="card purpose">
      <div className="purpose-row">
        <span className="purpose-label">What you’re seeing</span>
        <span className="purpose-text">{seeing}</span>
      </div>
      <div className="purpose-row">
        <span className="purpose-label">Why it matters</span>
        <span className="purpose-text">{matters}</span>
      </div>
      <div className="purpose-links">
        <span className="purpose-label">Read more</span>
        <span className="purpose-linklist">
          {links.map((l) => (
            <a key={l.key} href={l.url} target="_blank" rel="noreferrer">
              {l.title} →
            </a>
          ))}
        </span>
      </div>
    </div>
  );
}
