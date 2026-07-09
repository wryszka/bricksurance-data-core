import { useEffect, useState } from 'react';
import { api, NetworkNode, NetworkResponse } from '../api';
import PurposeCard from './PurposeCard';
import { DOCS } from '../docs';

function Node({ n, variant }: { n: NetworkNode; variant?: string }) {
  return (
    <div className={`node ${variant || ''}`}>
      <div className="n-label">{n.label}</div>
      <div className="n-sub">{n.sub}</div>
      <div className="n-plat">
        {n.platform} · <span className={`badge ${n.status}`}>{n.status}</span>
      </div>
    </div>
  );
}

export default function NetworkTab() {
  const [data, setData] = useState<NetworkResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    api.network().then(setData).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div className="result-note err">{err}</div>;
  if (!data) return <div className="loading">Checking the federation…</div>;

  const byId = Object.fromEntries(data.nodes.map((n) => [n.id, n]));

  return (
    <>
      <PurposeCard
        seeing="The federated estate and live exchange status — shares checked against the real API."
        matters="Two entities that adopt the same ontology exchange data with meaning intact."
        links={[DOCS.gettingStarted, DOCS.assets]}
      />
      <h2 className="section">Network — the federated estate</h2>
      <p className="sub">
        Live status is checked against Unity Catalog Delta Sharing. Planned units show the
        target topology.
      </p>

      <div className="card">
        <div className="net">
          <Node n={byId['centre']} />
          <div className="connector" />
          <div className="net-row">
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <Node n={byId['se']} variant="primary" />
              <div className="connector" />
              <Node n={byId['share']} variant="share" />
              <div className="connector" />
              <Node n={byId['re']} variant="primary" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <Node n={byId['specialty']} />
            </div>
          </div>
          <div className="net-caption">
            {data.share_live
              ? `The Delta Share “${data.share_name}” is live: Bricksurance SE shares the cession bordereau, its data dictionary and code sets directly to Bricksurance Re.`
              : `The Delta Share “${data.share_name}” is provisioned in code (tools/create_share.py) and pending activation to the Bricksurance Re dev workspace. Snowflake and BigQuery units are on the roadmap.`}
          </div>
        </div>
      </div>
    </>
  );
}
