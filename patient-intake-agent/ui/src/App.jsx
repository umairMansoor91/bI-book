const intakeChecklist = [
  "Name and date of birth",
  "Chief complaint and symptom duration",
  "Allergies and medications",
  "Consent to share with clinician"
];

const sampleTimeline = [
  {
    time: "09:12 AM",
    title: "Patient checked in",
    detail: "Prefers telehealth follow-up if available."
  },
  {
    time: "09:14 AM",
    title: "Intake started",
    detail: "Agent gathering demographics and symptoms."
  },
  {
    time: "09:18 AM",
    title: "Summary generated",
    detail: "Ready to send to clinician."
  }
];

export default function App() {
  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">LiveKit Agent Demo</p>
          <h1>Patient Intake Assistant</h1>
          <p className="subhead">
            A friendly intake flow that captures demographics, symptoms, and consent
            before the clinician joins.
          </p>
          <div className="hero-actions">
            <button className="primary">Start intake</button>
            <button className="secondary">View sample summary</button>
          </div>
        </div>
        <div className="summary-card">
          <h2>Today&apos;s Intake</h2>
          <div className="pill">Live</div>
          <p className="summary-text">
            “Hi, I&apos;m here for lingering cough and fatigue for two weeks. No known
            allergies. Taking vitamin D.”
          </p>
          <div className="summary-meta">
            <div>
              <span>Patient</span>
              <strong>Jordan Lee</strong>
            </div>
            <div>
              <span>Room</span>
              <strong>Clinic Intake A</strong>
            </div>
            <div>
              <span>Status</span>
              <strong>Awaiting clinician</strong>
            </div>
          </div>
        </div>
      </header>

      <main className="content">
        <section className="panel">
          <h2>Intake checklist</h2>
          <ul>
            {intakeChecklist.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="panel form-panel">
          <h2>Patient details</h2>
          <form className="intake-form">
            <label>
              Full name
              <input type="text" placeholder="Jordan Lee" />
            </label>
            <label>
              Date of birth
              <input type="date" />
            </label>
            <label>
              Chief complaint
              <input type="text" placeholder="Cough, fatigue" />
            </label>
            <label>
              Symptom duration
              <input type="text" placeholder="2 weeks" />
            </label>
            <label className="full">
              Notes for clinician
              <textarea rows="4" placeholder="Additional context for clinician..." />
            </label>
            <button className="primary full" type="button">
              Save intake summary
            </button>
          </form>
        </section>

        <section className="panel">
          <h2>Activity timeline</h2>
          <div className="timeline">
            {sampleTimeline.map((item) => (
              <div key={item.time} className="timeline-item">
                <div className="time">{item.time}</div>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
