import { useEffect, useMemo, useState } from "react";
import { Room } from "livekit-client";

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
  const livekitUrl = import.meta.env.VITE_LIVEKIT_URL;
  const staticToken = import.meta.env.VITE_LIVEKIT_TOKEN;
  const tokenServer = import.meta.env.VITE_TOKEN_SERVER;
  const identity = useMemo(
    () => `intake-ui-${Math.random().toString(36).slice(2, 8)}`,
    []
  );
  const [status, setStatus] = useState("idle");
  const [room, setRoom] = useState(null);
  const [formState, setFormState] = useState({
    name: "",
    dob: "",
    complaint: "",
    duration: "",
    notes: ""
  });

  useEffect(() => {
    if (!livekitUrl) {
      setStatus("missing LiveKit URL");
      return;
    }
    let active = true;
    const lkRoom = new Room();

    const connect = async () => {
      setStatus("connecting");
      let token = staticToken;
      if (!token && tokenServer) {
        const response = await fetch(
          `${tokenServer}/token?identity=${encodeURIComponent(identity)}`
        );
        const data = await response.json();
        token = data.token;
      }
      if (!token) {
        setStatus("missing token");
        return;
      }
      await lkRoom.connect(livekitUrl, token);
      if (!active) {
        lkRoom.disconnect();
        return;
      }
      setRoom(lkRoom);
      setStatus("connected");
    };

    connect().catch((error) => {
      console.error(error);
      setStatus("connection failed");
    });

    return () => {
      active = false;
      lkRoom.disconnect();
    };
  }, [identity, livekitUrl, staticToken, tokenServer]);

  const updateField = (field) => (event) => {
    setFormState((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleSave = async () => {
    if (!room) {
      setStatus("not connected");
      return;
    }
    const payload = {
      type: "intake.update",
      fields: {
        name: formState.name,
        dob: formState.dob,
        chief_complaint: formState.complaint,
        symptom_duration: formState.duration,
        notes: formState.notes
      }
    };
    await room.localParticipant.publishData(JSON.stringify(payload), {
      reliable: true
    });
    setStatus("sent update");
  };

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
          <p className="status">LiveKit status: {status}</p>
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
              <input
                type="text"
                placeholder="Jordan Lee"
                value={formState.name}
                onChange={updateField("name")}
              />
            </label>
            <label>
              Date of birth
              <input type="date" value={formState.dob} onChange={updateField("dob")} />
            </label>
            <label>
              Chief complaint
              <input
                type="text"
                placeholder="Cough, fatigue"
                value={formState.complaint}
                onChange={updateField("complaint")}
              />
            </label>
            <label>
              Symptom duration
              <input
                type="text"
                placeholder="2 weeks"
                value={formState.duration}
                onChange={updateField("duration")}
              />
            </label>
            <label className="full">
              Notes for clinician
              <textarea
                rows="4"
                placeholder="Additional context for clinician..."
                value={formState.notes}
                onChange={updateField("notes")}
              />
            </label>
            <button className="primary full" type="button" onClick={handleSave}>
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
