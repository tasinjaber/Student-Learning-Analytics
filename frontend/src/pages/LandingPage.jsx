import { Link } from "react-router-dom";

const NAV_LINKS = [
  { label: "Features", href: "#features" },
  { label: "How it works", href: "#how" },
  { label: "Tech stack", href: "#tech" },
];

const STATS = [
  { value: "6+", label: "Chart types" },
  { value: "3", label: "AI providers" },
  { value: "Real-time", label: "Analytics" },
  { value: "Multi", label: "Dataset support" },
];

const FEATURES = [
  {
    icon: "📊",
    title: "Engagement Analytics",
    desc: "Track daily interactions, activity mix, and platform behavior to understand participation patterns over time.",
  },
  {
    icon: "⚠️",
    title: "At-Risk Detection",
    desc: "Automatically flag students with low scores, prolonged inactivity, or weak engagement using a risk scoring model.",
  },
  {
    icon: "📈",
    title: "Performance Forecasting",
    desc: "Project future engagement trends using linear regression on historical interaction data — 7-day outlook.",
  },
  {
    icon: "🔍",
    title: "Anomaly Detection",
    desc: "Detect unusual spikes or drops in activity using z-score analysis highlighted directly on the trend chart.",
  },
  {
    icon: "🤖",
    title: "AI-Powered Insights",
    desc: "Generate natural-language summaries of your analytics data using Groq (LLaMA 3.3), Gemini, or ChatGPT.",
  },
  {
    icon: "📅",
    title: "Activity Heatmap",
    desc: "Visualise a full year of student activity in a GitHub-style calendar — spot engagement patterns at a glance.",
  },
  {
    icon: "👤",
    title: "Student Profiles",
    desc: "Drill into any individual student: activity timeline, score trend, event breakdown, and risk assessment.",
  },
  {
    icon: "⚖️",
    title: "Side-by-Side Comparison",
    desc: "Select any two students and compare their metrics — score, events, duration, and top activity — in one view.",
  },
  {
    icon: "📁",
    title: "Multi-Dataset Support",
    desc: "Upload your own CSV / Excel, link a Google Sheet, or use the default Kaggle dataset — switch anytime.",
  },
];

const HOW_STEPS = [
  { num: "01", title: "Connect your data", body: "Upload a CSV / Excel file, paste a Google Sheets link, or use the bundled Kaggle Open edX dataset." },
  { num: "02", title: "Explore the dashboard", body: "Instantly see engagement trends, score distributions, activity breakdown, and heatmap calendar." },
  { num: "03", title: "Identify at-risk students", body: "The platform scores each learner automatically. Admins get a prioritised at-risk workbook." },
  { num: "04", title: "Generate AI insights", body: "One click sends your analytics summary to Groq, Gemini, or ChatGPT for a plain-English briefing." },
];

const TECH = [
  { name: "React", role: "UI & routing", color: "#61dafb" },
  { name: "Recharts", role: "Charts & visualisation", color: "#22c55e" },
  { name: "FastAPI", role: "REST API backend", color: "#009688" },
  { name: "MongoDB", role: "Flexible data store", color: "#47a248" },
  { name: "Pandas", role: "Data ingestion & export", color: "#130654" },
  { name: "Groq / Gemini / GPT", role: "AI insight layer", color: "#6366f1" },
];

export default function LandingPage() {
  return (
    <div className="lp-root">
      {/* Navbar */}
      <header className="lp-nav">
        <div className="lp-nav-inner">
          <img src="/logo.png" alt="Learning Analytics Platform" className="lp-logo-img" />
          <nav className="lp-nav-links">
            {NAV_LINKS.map((l) => (
              <a key={l.label} href={l.href} className="lp-nav-link">{l.label}</a>
            ))}
          </nav>
          <Link to="/dashboard" className="lp-nav-cta">Open Dashboard →</Link>
        </div>
      </header>

      {/* Hero */}
      <section className="lp-hero">
        <div className="lp-hero-glow lp-glow-1" />
        <div className="lp-hero-glow lp-glow-2" />
        <div className="lp-hero-inner">
          <p className="lp-eyebrow">Data-Driven Education</p>
          <h1 className="lp-hero-title">
            Student Learning<br />
            <span className="lp-hero-accent">Behavior Analytics</span>
          </h1>
          <p className="lp-hero-sub">
            Transform online course interaction logs into actionable insights.<br />
            Understand engagement, detect at-risk learners, and forecast trends — all in one platform.
          </p>
          <div className="lp-hero-actions">
            <Link to="/dashboard" className="lp-btn-primary">Get Started</Link>
            <a href="#features" className="lp-btn-ghost">See features ↓</a>
          </div>
        </div>

        <div className="lp-stats">
          {STATS.map((s) => (
            <div key={s.label} className="lp-stat">
              <span className="lp-stat-value">{s.value}</span>
              <span className="lp-stat-label">{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="lp-section" id="features">
        <div className="lp-section-inner">
          <p className="lp-section-eyebrow">Platform capabilities</p>
          <h2 className="lp-section-title">Everything you need to understand your learners</h2>
          <div className="lp-features-grid">
            {FEATURES.map((f) => (
              <div key={f.title} className="lp-feature-card">
                <span className="lp-feature-icon">{f.icon}</span>
                <h3 className="lp-feature-title">{f.title}</h3>
                <p className="lp-feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="lp-section lp-section-alt" id="how">
        <div className="lp-section-inner">
          <p className="lp-section-eyebrow">Workflow</p>
          <h2 className="lp-section-title">Up and running in minutes</h2>
          <div className="lp-steps">
            {HOW_STEPS.map((s) => (
              <div key={s.num} className="lp-step">
                <span className="lp-step-num">{s.num}</span>
                <div>
                  <h3 className="lp-step-title">{s.title}</h3>
                  <p className="lp-step-body">{s.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech stack */}
      <section className="lp-section" id="tech">
        <div className="lp-section-inner">
          <p className="lp-section-eyebrow">Technical foundation</p>
          <h2 className="lp-section-title">Built with production-grade tools</h2>
          <div className="lp-tech-grid">
            {TECH.map((t) => (
              <div key={t.name} className="lp-tech-card">
                <span className="lp-tech-dot" style={{ background: t.color }} />
                <div>
                  <p className="lp-tech-name">{t.name}</p>
                  <p className="lp-tech-role">{t.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="lp-cta-banner">
        <div className="lp-cta-inner">
          <h2 className="lp-cta-title">Ready to explore your data?</h2>
          <p className="lp-cta-sub">Sign in as admin or instructor and open the analytics dashboard.</p>
          <Link to="/dashboard" className="lp-btn-primary lp-btn-lg">Open Dashboard →</Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="lp-footer">
        <img src="/logo.png" alt="Learning Analytics Platform" className="lp-logo-img lp-logo-img-sm" />
        <p className="lp-footer-copy">Student Learning Behavior Analytics Platform · Developed by Tasin Jaber</p>
        <div className="lp-footer-links">
          <Link to="/login" className="lp-footer-link">Login</Link>
          <Link to="/dashboard" className="lp-footer-link">Dashboard</Link>
          <Link to="/compare" className="lp-footer-link">Compare</Link>
        </div>
      </footer>
    </div>
  );
}
