export default function MetricCard({ title, value, helper }) {
  return (
    <article className="metric-card">
      <p className="metric-title">{title}</p>
      <h3>{value}</h3>
      <p className="metric-helper">{helper}</p>
    </article>
  );
}
