import { useEffect, useState } from 'react';
import { api, NarrationModel, ModelSwapResponse, money } from '../api';
import { ErrorNote, Loading } from '../components/ui';

const TIER_LABEL: Record<string, string> = {
  frontier: 'Frontier',
  open: 'Open weights',
  cheap: 'Small / cheap',
  none: 'No model',
};

export default function ModelSwapView() {
  const [models, setModels] = useState<NarrationModel[]>([]);
  const [model, setModel] = useState('databricks-claude-sonnet-5');
  const [data, setData] = useState<ModelSwapResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [narrating, setNarrating] = useState(false);

  useEffect(() => {
    api.modelSwapConfig().then((c) => setModels(c.models)).catch(() => {});
  }, []);

  useEffect(() => {
    setNarrating(true);
    setErr(null);
    api
      .modelSwap(model)
      .then((d) => {
        setData(d);
        setNarrating(false);
      })
      .catch((e) => {
        setErr(String(e));
        setNarrating(false);
      });
  }, [model]);

  if (err) return <ErrorNote error={`Failed: ${err}`} />;

  const fact = data?.fact;

  return (
    <div className="view detail modelswap">
      <div className="detail-head">
        <div className="detail-kicker">Platform · Context is the moat</div>
        <h2 className="detail-title">The model is a dial, not the foundation</h2>
        <p className="detail-desc">
          The decision below was made by a governed rules function — not by an
          LLM. Change the model that <em>explains</em> it, or switch the model
          off entirely: the decision and the number never move. The intelligence
          isn't in the model. It's in the governed context underneath.
        </p>
      </div>

      {/* the dial */}
      <div className="ms-dial">
        <span className="ms-dial-label">Narration model</span>
        <div className="seg-wrap">
          {models.map((m) => (
            <button
              key={m.id}
              className={`ms-model ${model === m.id ? 'active' : ''} tier-${m.tier}`}
              onClick={() => setModel(m.id)}
              title={m.note}
            >
              <span className="ms-model-label">{m.label}</span>
              <span className="ms-model-tier">{TIER_LABEL[m.tier] || m.tier}</span>
            </button>
          ))}
        </div>
      </div>

      {!fact ? (
        <Loading label="Loading the governed decision…" />
      ) : (
        <div className="ms-grid">
          {/* the fixed governed fact */}
          <div className="ms-fact">
            <div className="ms-fact-tag">Governed decision — never changes</div>
            <div className="ms-fact-row">
              <span>Quote</span>
              <span className="mono">{fact.quote_number}</span>
            </div>
            <div className="ms-fact-row">
              <span>Line of business</span>
              <span>{fact.line_of_business}</span>
            </div>
            <div className="ms-fact-row">
              <span>Premium</span>
              <span className="mono">
                {fact.quoted_premium != null ? money(fact.quoted_premium, 'GBP') : '—'}
              </span>
            </div>
            <div className="ms-fact-decision">
              <span className="ms-decision-badge">{fact.decision}</span>
              <span className="ms-decision-by">by {fact.decided_by_engine}</span>
            </div>
            <div className="ms-fact-note">
              Deterministic · recorded · auditable — the same regardless of which
              model (or no model) is selected.
            </div>
          </div>

          {/* the swappable narration */}
          <div className="ms-narration">
            <div className="ms-narration-tag">
              Narration — {data?.model_label}
              {narrating && <span className="ms-spin"> · thinking…</span>}
            </div>
            {model === 'none' ? (
              <div className="ms-none">
                <div className="ms-none-icon">⛉</div>
                <p>{data?.narration_note}</p>
              </div>
            ) : data?.narration_error ? (
              <div className="ms-narration-body err">
                Model unavailable: {data.narration_error}
                <br />
                <strong>The decision above still stands.</strong>
              </div>
            ) : (
              <div className="ms-narration-body">{data?.narration || '…'}</div>
            )}
          </div>
        </div>
      )}

      <div className="ms-contract">
        <strong>Why this matters.</strong> {data?.contract}
        <div className="ms-contract-points">
          <div>
            <span className="ms-cp-h">Regulator</span>
            The number and the decision are deterministic and logged — not a black
            box. The model explains; it doesn't adjudicate.
          </div>
          <div>
            <span className="ms-cp-h">No lock-in</span>
            Every option is a Foundation Model API endpoint. Swap Anthropic for an
            open-weight model in your own VPC, or drop the LLM from the path — the
            governed answer is unchanged.
          </div>
          <div>
            <span className="ms-cp-h">The moat</span>
            The durable asset is the governed context — Unity Catalog, metric
            views, lineage — on the platform. The model is a commodity you dial.
          </div>
        </div>
      </div>

      <div className="provenance">
        Decision: policy.underwriting_decision (fn_appetite_check) · narration via
        Foundation Model API — model-agnostic
      </div>
    </div>
  );
}
