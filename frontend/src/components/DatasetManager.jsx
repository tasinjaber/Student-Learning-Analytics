import { useEffect, useRef, useState } from "react";
import {
  addDatasetFromUrl,
  deleteDataset,
  listDatasets,
  uploadDataset,
  validateDataset,
} from "../services/analyticsApi";

const COMPAT_COLORS = {
  full:    { bg: "#dcfce7", color: "#166534" },
  partial: { bg: "#fef9c3", color: "#92400e" },
  low:     { bg: "#fee2e2", color: "#dc2626" },
  empty:   { bg: "#f1f5f9", color: "#64748b" },
  error:   { bg: "#fee2e2", color: "#dc2626" },
};

function CompatBadge({ level, summary }) {
  const style = COMPAT_COLORS[level] ?? COMPAT_COLORS.error;
  return (
    <div className="compat-badge" style={style}>
      <strong>{level?.toUpperCase()}</strong> — {summary}
    </div>
  );
}

export default function DatasetManager({ activeDataset, onSelect, onClose }) {
  const [datasets, setDatasets] = useState([]);
  const [tab, setTab] = useState("upload");
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState({ text: "", ok: true });
  const [validation, setValidation] = useState({});
  const fileRef = useRef();

  useEffect(() => { load(); }, []);

  async function load() {
    const list = await listDatasets();
    setDatasets(list);
    // validate each non-default dataset
    const checks = {};
    await Promise.all(
      list.map(async (ds) => {
        if (ds.dataset_id) {
          checks[ds.dataset_id] = await validateDataset(ds.dataset_id);
        }
      })
    );
    setValidation(checks);
  }

  function setOk(text) { setMsg({ text, ok: true }); }
  function setErr(text) { setMsg({ text, ok: false }); }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file || !name.trim()) return setErr("Name and file are required.");
    setBusy(true); setMsg({ text: "", ok: true });
    try {
      await uploadDataset(name.trim(), file);
      setOk("Uploaded successfully.");
      setName(""); setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      await load();
    } catch { setErr("Upload failed. Check file format."); }
    finally { setBusy(false); }
  }

  async function handleUrl(e) {
    e.preventDefault();
    if (!url.trim() || !name.trim()) return setErr("Name and URL are required.");
    setBusy(true); setMsg({ text: "", ok: true });
    try {
      await addDatasetFromUrl(url.trim(), name.trim());
      setOk("Dataset loaded.");
      setName(""); setUrl("");
      await load();
    } catch { setErr("Failed to load from URL. Ensure it's a public CSV or Google Sheets link."); }
    finally { setBusy(false); }
  }


  async function handleDelete(id) {
    if (!confirm("Delete this dataset?")) return;
    await deleteDataset(id);
    if (activeDataset?.dataset_id === id) onSelect(datasets[0]);
    await load();
  }

  const tabs = [
    { key: "upload", label: "Upload CSV / Excel" },
    { key: "url",    label: "Google Sheets / URL" },
    { key: "kaggle", label: "Kaggle (how-to)" },
  ];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>Dataset Manager</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="dm-list">
          <p className="dm-section-label">Saved datasets</p>
          {datasets.map((ds) => {
            const compat = ds.dataset_id ? validation[ds.dataset_id] : null;
            return (
              <div
                key={ds.dataset_id ?? "__default__"}
                className={`dm-row ${activeDataset?.dataset_id === ds.dataset_id ? "dm-active" : ""}`}
              >
                <button className="dm-select-btn" onClick={() => { onSelect(ds); onClose(); }}>
                  <span className="dm-name">{ds.name}</span>
                  <span className="dm-meta">
                    {ds.source !== "default"
                      ? `${ds.source} · ${ds.record_count ?? "?"} rows`
                      : "always available"}
                  </span>
                  {compat && (
                    <span
                      className="dm-compat-pill"
                      style={COMPAT_COLORS[compat.compatibility]}
                      title={compat.summary}
                    >
                      {compat.compatibility}
                    </span>
                  )}
                </button>
                {ds.dataset_id && (
                  <button className="dm-delete-btn" onClick={() => handleDelete(ds.dataset_id)} title="Delete">✕</button>
                )}
              </div>
            );
          })}
        </div>

        <div className="dm-tabs">
          {tabs.map((t) => (
            <button key={t.key} className={`dm-tab ${tab === t.key ? "active" : ""}`} onClick={() => setTab(t.key)}>
              {t.label}
            </button>
          ))}
        </div>

        {tab === "upload" && (
          <form className="dm-form" onSubmit={handleUpload}>
            <input placeholder="Dataset name" value={name} onChange={(e) => setName(e.target.value)} />
            <input type="file" accept=".csv,.xlsx,.xls" ref={fileRef} onChange={(e) => setFile(e.target.files[0])} />
            <p className="dm-hint">Accepted: CSV, Excel (.xlsx / .xls). Columns are auto-detected.</p>
            <button className="btn btn-primary" type="submit" disabled={busy}>{busy ? "Uploading…" : "Upload"}</button>
          </form>
        )}

        {tab === "url" && (
          <form className="dm-form" onSubmit={handleUrl}>
            <input placeholder="Dataset name" value={name} onChange={(e) => setName(e.target.value)} />
            <input
              placeholder="Google Sheets URL or direct CSV link"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <p className="dm-hint">Google Sheets must be set to <em>Anyone with link can view</em>.</p>
            <button className="btn btn-primary" type="submit" disabled={busy}>{busy ? "Loading…" : "Add"}</button>
          </form>
        )}

        {tab === "kaggle" && (
          <div className="dm-kaggle-guide">
            <p className="dm-guide-step"><span className="dm-step-num">1</span> Go to the Kaggle dataset page</p>
            <p className="dm-guide-step"><span className="dm-step-num">2</span> Click <strong>Download</strong> (you must be logged in to Kaggle)</p>
            <p className="dm-guide-step"><span className="dm-step-num">3</span> Extract the ZIP — you'll find one or more <code>.csv</code> files</p>
            <p className="dm-guide-step"><span className="dm-step-num">4</span> Switch to the <strong>Upload CSV / Excel</strong> tab and upload that file</p>
            <p className="dm-hint" style={{ marginTop: 10 }}>
              Kaggle requires login even for public datasets, so direct URL download is not possible without API credentials.
            </p>
          </div>
        )}

        {msg.text && (
          <p className="dm-msg" style={{ color: msg.ok ? "#16a34a" : "#dc2626" }}>{msg.text}</p>
        )}
      </div>
    </div>
  );
}
