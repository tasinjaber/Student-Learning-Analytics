export default function InfoTip({ text }) {
  return (
    <span className="infotip">
      <span className="infotip-icon">i</span>
      <span className="infotip-tooltip">{text}</span>
    </span>
  );
}
