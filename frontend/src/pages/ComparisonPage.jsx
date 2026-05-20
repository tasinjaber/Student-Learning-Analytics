import { useEffect, useState } from "react";
import { fetchComparison, fetchStudentIds } from "../services/analyticsApi";

function StatRow({ label, a, b }) {
  const numA = parseFloat(a);
  const numB = parseFloat(b);
  const aWins = !isNaN(numA) && !isNaN(numB) && numA > numB;
  const bWins = !isNaN(numA) && !isNaN(numB) && numB > numA;
  return (
    <tr>
      <td className={`cmp-cell ${aWins ? "cmp-winner" : ""}`}>{a ?? "—"}</td>
      <td className="cmp-label">{label}</td>
      <td className={`cmp-cell ${bWins ? "cmp-winner" : ""}`}>{b ?? "—"}</td>
    </tr>
  );
}

export default function ComparisonPage({ activeDataset }) {
  const [students, setStudents] = useState([]);
  const [selA, setSelA] = useState("");
  const [selB, setSelB] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const dsId = activeDataset?.dataset_id ?? null;

  useEffect(() => {
    fetchStudentIds(dsId).then((ids) => {
      setStudents(ids);
      if (ids.length >= 2) { setSelA(ids[0]); setSelB(ids[1]); }
    });
  }, [dsId]);

  async function compare() {
    if (!selA || !selB || selA === selB) return setError("Select two different students.");
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetchComparison(selA, selB, dsId);
      setResult(res);
    } catch { setError("Comparison failed."); }
    finally { setLoading(false); }
  }

  return (
    <section className="comparison-page">
      <h2 className="page-title">Student Comparison</h2>

      <div className="cmp-selectors">
        <select value={selA} onChange={(e) => setSelA(e.target.value)}>
          {students.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <span className="cmp-vs">vs</span>
        <select value={selB} onChange={(e) => setSelB(e.target.value)}>
          {students.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button className="btn btn-primary" onClick={compare} disabled={loading}>
          {loading ? "Comparing…" : "Compare"}
        </button>
      </div>

      {error && <p className="state-text error">{error}</p>}

      {result && (
        <div className="cmp-table-wrap">
          <table className="cmp-table">
            <thead>
              <tr>
                <th>{result.a.student_id}</th>
                <th>Metric</th>
                <th>{result.b.student_id}</th>
              </tr>
            </thead>
            <tbody>
              <StatRow label="Avg Score" a={result.a.avg_score} b={result.b.avg_score} />
              <StatRow label="Total Events" a={result.a.total_events} b={result.b.total_events} />
              <StatRow label="Duration (min)" a={result.a.total_duration_minutes} b={result.b.total_duration_minutes} />
              <StatRow label="Inactivity (days)" a={result.a.inactivity_days} b={result.b.inactivity_days} />
              <tr>
                <td className="cmp-cell">{result.a.top_activity}</td>
                <td className="cmp-label">Top Activity</td>
                <td className="cmp-cell">{result.b.top_activity}</td>
              </tr>
              <tr>
                <td className="cmp-cell">{result.a.courses?.join(", ") || "—"}</td>
                <td className="cmp-label">Courses</td>
                <td className="cmp-cell">{result.b.courses?.join(", ") || "—"}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
