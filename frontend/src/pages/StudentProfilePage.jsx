import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Bar, BarChart, CartesianGrid, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { fetchStudentDetail } from "../services/analyticsApi";

export default function StudentProfilePage({ activeDataset }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    fetchStudentDetail(id, activeDataset?.dataset_id ?? null)
      .then(setData)
      .catch(() => setError("Student not found."))
      .finally(() => setLoading(false));
  }, [id, activeDataset]);

  if (loading) return <p className="state-text">Loading student profile…</p>;
  if (error || !data) return <p className="state-text error">{error || "No data."}</p>;

  const riskColor = data.risk_score >= 70 ? "#ef4444" : data.risk_score >= 40 ? "#f59e0b" : "#22c55e";

  return (
    <section className="profile-page">
      <button className="btn btn-secondary-dark back-btn" onClick={() => navigate(-1)}>← Back</button>

      <div className="profile-header">
        <div className="profile-avatar">{String(data.student_id).slice(0, 2).toUpperCase()}</div>
        <div>
          <h2 className="profile-id">{data.student_id}</h2>
          <p className="profile-courses">{data.courses?.join(", ") || "—"}</p>
        </div>
        <div className="profile-risk-badge" style={{ background: riskColor }}>
          Risk {data.risk_score}
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card"><p className="metric-title">Avg Score</p><p className="metric-value">{data.avg_score}</p></div>
        <div className="metric-card"><p className="metric-title">Total Events</p><p className="metric-value">{data.total_events}</p></div>
        <div className="metric-card"><p className="metric-title">Total Duration</p><p className="metric-value">{data.total_duration_minutes} min</p></div>
        <div className="metric-card"><p className="metric-title">Inactivity</p><p className="metric-value">{data.inactivity_days} days</p></div>
      </div>

      <div className="chart-grid">
        {data.timeline?.length > 0 && (
          <article className="chart-card">
            <h3>Activity timeline</h3>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.timeline}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="events" stroke="#6366f1" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </article>
        )}

        {data.score_trend?.length > 0 && (
          <article className="chart-card">
            <h3>Score trend</h3>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.score_trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="avg_score" stroke="#22c55e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </article>
        )}

        {data.activity_breakdown?.length > 0 && (
          <article className="chart-card">
            <h3>Activity breakdown</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.activity_breakdown}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="activity" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#0ea5e9" />
              </BarChart>
            </ResponsiveContainer>
          </article>
        )}
      </div>
    </section>
  );
}
