import { useEffect, useRef, useState } from 'react';
import { api, LoadResponse, MapResponse, OutboundResponse } from '../api';

function OutboundPane() {
  const [data, setData] = useState<OutboundResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    api.outbound().then(setData).catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="card">
      <div className="pane-head">
        <h3>Outbound — the bordereau is a governed view</h3>
        <div className="p-sub">
          Derived live from the canonical model and shared as a table, never exported to a
          spreadsheet.
        </div>
      </div>
      <div className="pane-body">
        {err && <div className="result-note err">{err}</div>}
        {!data ? (
          <div className="loading">Loading the outbound bordereau…</div>
        ) : (
          <>
            <div className="scroll-x">
              <table>
                <thead>
                  <tr>
                    <th>Treaty</th>
                    <th>Policy</th>
                    <th>Insured</th>
                    <th>Ccy</th>
                    <th>Gross prem</th>
                    <th>Share</th>
                    <th>Ceded prem</th>
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((r, i) => (
                    <tr key={i}>
                      <td className="mono">{r.treaty_reference}</td>
                      <td className="mono">{r.policy_number}</td>
                      <td>{r.insured_name}</td>
                      <td>{r.currency_code}</td>
                      <td>{Number(r.gross_premium).toLocaleString()}</td>
                      <td>{r.ceded_share}</td>
                      <td>{Number(r.ceded_premium).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <details open>
              <summary>What travels with this share</summary>
              <div className="scroll-x" style={{ marginTop: 10 }}>
                <table>
                  <thead>
                    <tr>
                      <th>Attribute</th>
                      <th>Type</th>
                      <th>Definition</th>
                      <th>Class</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.travels.map((t) => (
                      <tr key={t.attribute}>
                        <td className="mono">{t.attribute}</td>
                        <td className="mono">{t.type || '—'}</td>
                        <td className="def">{t.definition}</td>
                        <td>
                          {t.classification ? (
                            <span className={`badge ${t.classification}`}>
                              {t.classification}
                            </span>
                          ) : (
                            '—'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="callout">
                The Delta Share <span className="mono">{data.share_name}</span> carries the
                data dictionary and the code sets alongside the rows —{' '}
                {data.share_objects.map((o) => o.name).join(', ')} — so the receiver gets the
                semantics, not just numbers.
              </div>
            </details>
          </>
        )}
      </div>
    </div>
  );
}

function InboundPane() {
  const [content, setContent] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [mapping, setMapping] = useState<MapResponse | null>(null);
  const [loaded, setLoaded] = useState<LoadResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setMapping(null);
    setLoaded(null);
    setErr(null);
  };

  const useSample = async () => {
    reset();
    const s = await api.sample();
    setContent(s.content);
    setFilename(s.filename);
  };

  const onFile = async (f: File) => {
    reset();
    setFilename(f.name);
    setContent(await f.text());
  };

  const runMap = async () => {
    if (!content) return;
    reset();
    setBusy(true);
    try {
      setMapping(await api.mapContent(content));
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  const runLoad = async () => {
    if (!mapping?.records) return;
    setBusy(true);
    setErr(null);
    try {
      setLoaded(await api.load(mapping.records));
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  const cols = mapping?.records?.length ? Object.keys(mapping.records[0]) : [];

  return (
    <div className="card">
      <div className="pane-head">
        <h3>Inbound — map a messy bordereau with the dictionary as the contract</h3>
        <div className="p-sub">
          A coverholder's spreadsheet, mapped to the canonical model by Claude, validated
          against the data dictionary before a single row loads. No middleware.
        </div>
      </div>
      <div className="pane-body">
        <div className="btn-row">
          <button className="btn ghost" onClick={() => fileRef.current?.click()}>
            Upload a CSV…
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,text/csv"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
          />
          <button className="btn ghost" onClick={useSample}>
            Use sample file
          </button>
          {filename && <span className="p-sub">Loaded: {filename}</span>}
        </div>

        <div className="btn-row">
          <button className="btn primary" onClick={runMap} disabled={!content || busy}>
            {busy && !loaded ? 'Mapping with Claude…' : 'Map with Claude'}
          </button>
          <button
            className="btn accent"
            onClick={runLoad}
            disabled={!mapping?.valid || busy}
          >
            Load into canonical model
          </button>
        </div>

        {err && <div className="result-note err">{err}</div>}

        {mapping && (
          <>
            <div className={`result-note ${mapping.valid ? 'ok' : 'err'}`}>
              {mapping.valid
                ? `Validation passed — ${mapping.records.length} records conform to the dictionary contract.`
                : `Validation failed: ${mapping.errors.join('; ')}`}
            </div>

            <details open>
              <summary>Mapping report — file column → canonical attribute</summary>
              <div className="scroll-x" style={{ marginTop: 10 }}>
                <table>
                  <thead>
                    <tr>
                      <th>File column</th>
                      <th>Canonical mapping</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(mapping.mapping_notes).map(([k, v]) => (
                      <tr key={k}>
                        <td className="mono">{k}</td>
                        <td className="def">{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>

            <details open>
              <summary>Conforming records ({mapping.records.length})</summary>
              <div className="scroll-x" style={{ marginTop: 10 }}>
                <table>
                  <thead>
                    <tr>
                      {cols.map((c) => (
                        <th key={c}>{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {mapping.records.map((r, i) => (
                      <tr key={i}>
                        {cols.map((c) => (
                          <td key={c} className="mono">
                            {r[c] === null || r[c] === undefined ? '—' : String(r[c])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </>
        )}

        {loaded && (
          <div className="result-note ok">
            Loaded into <span className="mono">exchange.premium_bordereau_line</span>:{' '}
            {loaded.row_count} lines, gross premium{' '}
            {loaded.gross_premium_total.toLocaleString()}.
          </div>
        )}
      </div>
    </div>
  );
}

export default function ExchangeTab() {
  return (
    <>
      <div className="banner">
        Killing the bordereau: the outbound share is a governed view, and inbound messy files
        are mapped to the canonical model with the dictionary as the contract.
      </div>
      <h2 className="section">Exchange — semantics that travel</h2>
      <p className="sub">
        The standard travels with the data. Every exchange carries its definitions.
      </p>
      <div className="two-pane">
        <OutboundPane />
        <InboundPane />
      </div>
    </>
  );
}
