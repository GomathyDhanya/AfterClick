import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Task = {
  id: string;
  title: string;
  description: string;
  reviewed: boolean;
  ready: boolean;
  priority: string;
  assignee: string;
  status: string;
  version: number;
};
type Editable = Pick<
  Task,
  "description" | "reviewed" | "priority" | "assignee" | "status"
>;
type Activity = {
  id: number;
  kind: string;
  actor: string;
  after: Record<string, unknown>;
};
type Notice = { id: string; message: string; delivered: boolean };
type SaveState =
  | "Committed"
  | "Locally edited"
  | "Saving"
  | "Failed"
  | "Conflict";
type Operation = {
  expected_version: number;
  operation_id: string;
  changes: Partial<Editable>;
};

async function get<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selected, setSelected] = useState("TASK-42");
  const [draft, setDraft] = useState<Task | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("Committed");
  const [error, setError] = useState("");
  const [connected, setConnected] = useState(false);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [comments, setComments] = useState<
    { id: string; body: string; actor: string }[]
  >([]);
  const [comment, setComment] = useState("");
  const [posting, setPosting] = useState(false);
  const selectedRef = useRef(selected);
  selectedRef.current = selected;
  const base = useRef<Task | null>(null);
  const dirty = useRef<Partial<Editable>>({});
  const operation = useRef<Operation | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const busy = useRef(false);
  const session = useRef(crypto.randomUUID());

  async function refresh() {
    const [board, events, inbox, discussion] = await Promise.all([
      get<Task[]>("/api/projects/release/tasks"),
      get<Activity[]>(`/api/tasks/${selected}/activity`),
      get<Notice[]>("/api/notifications"),
      get<{ id: string; body: string; actor: string }[]>(
        `/api/tasks/${selected}/comments`,
      ),
    ]);
    if (selectedRef.current !== selected) return;
    setTasks((previous) =>
      board.map((t) => {
        const existing = previous.find((p) => p.id === t.id);
        return existing && existing.version > t.version ? existing : t;
      }),
    );
    setActivity((previous) =>
      events.length >= previous.length ? events : previous,
    );
    setNotices(inbox);
    setComments(discussion);
    if (
      !busy.current &&
      !Object.keys(dirty.current).length &&
      !operation.current
    ) {
      const next = board.find((t) => t.id === selected)!;
      if (
        !base.current ||
        base.current.id !== next.id ||
        next.version >= base.current.version
      ) {
        base.current = next;
        setDraft(next);
      }
    }
  }

  useEffect(() => {
    let active = true;
    refresh().catch((e) => setError(String(e)));
    const events = new EventSource("/api/events");
    events.onopen = () => setConnected(true);
    events.onerror = () => setConnected(false);
    events.onmessage = (event) => {
      if (!active) return;
      // Acknowledge actual browser receipt separately from server publication.
      fetch(`/api/events/${event.lastEventId}/ack`, {
        method: "POST",
        headers: { "X-Session-ID": session.current },
      }).catch(() => setError("Live-update receipt could not be recorded."));
      refresh().catch((e) => setError(String(e)));
    };
    return () => {
      active = false;
      events.close();
    };
  }, [selected]);

  useEffect(() => {
    const guard = (event: BeforeUnloadEvent) => {
      if (Object.keys(dirty.current).length || operation.current) {
        event.preventDefault();
      }
    };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, []);

  async function save(retry = false) {
    if (busy.current || !base.current) return;
    busy.current = true;
    setSaveState("Saving");
    setError("");
    const op =
      retry && operation.current
        ? operation.current
        : {
            expected_version: base.current.version,
            operation_id: crypto.randomUUID(),
            changes: { ...dirty.current },
          };
    operation.current = op;
    try {
      let response = await fetch(`/api/tasks/${selected}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(op),
      });
      if (response.status === 409) {
        const latest = await get<Task>(`/api/tasks/${selected}`);
        const fields = Object.keys(op.changes) as (keyof Editable)[];
        // Rebase only if every edited field is still equal to the original base.
        if (fields.some((key) => latest[key] !== base.current![key])) {
          operation.current = null;
          setSaveState("Conflict");
          setError(
            "This field changed in another session. Your draft is preserved; load the latest version to resolve.",
          );
          return;
        }
        op.expected_version = latest.version;
        op.operation_id = crypto.randomUUID();
        response = await fetch(`/api/tasks/${selected}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(op),
        });
      }
      if (!response.ok)
        throw new Error(
          `Save failed (${response.status}). Retry uses the same operation ID.`,
        );
      const saved: Task = await response.json();
      base.current = saved;
      dirty.current = {};
      operation.current = null;
      setDraft(saved);
      setSaveState("Committed");
    } catch (e) {
      setError(String(e));
      setSaveState("Failed");
    } finally {
      busy.current = false;
      await refresh().catch((e) => setError(String(e)));
    }
  }

  function edit<K extends keyof Editable>(key: K, value: Editable[K]) {
    dirty.current = { ...dirty.current, [key]: value };
    setDraft((previous) =>
      previous ? { ...previous, [key]: value } : previous,
    );
    setSaveState("Locally edited");
    clearTimeout(timer.current);
    timer.current = setTimeout(() => void save(), 600);
  }

  async function reload() {
    clearTimeout(timer.current);
    dirty.current = {};
    operation.current = null;
    setError("");
    setSaveState("Committed");
    await refresh();
  }

  async function postComment() {
    if (!comment.trim() || posting) return;
    setPosting(true);
    try {
      const response = await fetch(`/api/tasks/${selected}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          body: comment,
          operation_id: crypto.randomUUID(),
        }),
      });
      if (!response.ok) throw new Error("Comment could not be saved.");
      setComment("");
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setPosting(false);
    }
  }

  const locked =
    saveState === "Saving" ||
    saveState === "Failed" ||
    saveState === "Conflict";
  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="FlowBoard home">
          <span className="brand-mark">f</span>FlowBoard
          <span className="brand-dot">.</span>
        </a>
        <div className="workspace">
          <span className="workspace-icon">A</span>
          <div>
            AfterClick lab<small>Research workspace</small>
          </div>
          <span>⌄</span>
        </div>
        <p className="nav-label">WORKSPACE</p>
        <div className="nav-active">
          <span>▦</span> Projects <span className="count">1</span>
        </div>
        <div className="project-link">
          <span className="tiny-dot" /> API v2 launch
        </div>
        <div className="sidebar-bottom">
          <span className="avatar">M</span>
          <div>
            Maya Chen<small>Project owner</small>
          </div>
          <span className="online-dot" />
        </div>
      </aside>
      <main>
        <header>
          <div className="breadcrumb">
            Workspace <span>/</span> Projects <span>/</span>
            <strong>API v2 launch</strong>
          </div>
          <span className={`live ${connected ? "" : "offline"}`}>
            <i />
            {connected ? "Live updates" : "Connecting"}
          </span>
        </header>
        <section className="page-heading">
          <div>
            <p className="eyebrow">RELEASE WORKSPACE</p>
            <h1>Good work, in motion.</h1>
            <p>A shared place to bring the next release together.</p>
          </div>
          <div className="team">
            <span className="avatar">M</span>
            <span className="avatar lavender">A</span>
            <span className="avatar sand">J</span>
            <small>Release team</small>
          </div>
        </section>
        <section className="project-banner">
          <div className="project-icon">↗</div>
          <div>
            <h2>API v2 launch</h2>
            <p>Integration experience · Engineering</p>
          </div>
          <span className="pill">In progress</span>
          <div className="progress-label">
            <strong>
              {tasks.filter((t) => t.status === "Done").length} / {tasks.length}
            </strong>
            <small>tasks complete</small>
          </div>
        </section>
        <div className="section-heading">
          <h2>
            Project tasks <span>{tasks.length}</span>
          </h2>
          <span>Changes save automatically</span>
        </div>
        <div className="content-grid">
          <section className="task-list" aria-label="Project tasks">
            {tasks.map((t) => (
              <button
                key={t.id}
                className={`task-card ${selected === t.id ? "selected" : ""}`}
                disabled={saveState !== "Committed"}
                onClick={() => {
                  setDraft(null);
                  setActivity([]);
                  setSelected(t.id);
                }}
              >
                <div className="task-meta">
                  <span>{t.id}</span>
                  <span className={t.ready ? "ready-dot" : "task-dot"} />
                </div>
                <h3>{t.title}</h3>
                <p>{t.description}</p>
                <div className="task-footer">
                  <span className="status-chip">{t.status}</span>
                  <span className="mini-avatar">{t.assignee[0]}</span>
                </div>
                {t.id === "TASK-43" && (
                  <div className="dependency">
                    ↳{" "}
                    {t.ready
                      ? "Prerequisite satisfied"
                      : "Waiting for TASK-42 review"}
                  </div>
                )}
              </button>
            ))}
            <div className="note">
              <span>◎</span>
              <div>
                <strong>One shared view</strong>
                <p>
                  Edits and release readiness stay in sync across your team’s
                  sessions.
                </p>
              </div>
            </div>
          </section>
          <section className="editor" aria-label="Task editor">
            {!draft ? (
              <p>Loading task…</p>
            ) : (
              <>
                <div className="editor-top">
                  <span className="task-key">
                    {draft.id} <span>/ Task details</span>
                  </span>
                  <span
                    role="status"
                    className={`save-state ${saveState === "Committed" ? "saved" : ""}`}
                  >
                    {saveState === "Committed" ? "✓ " : ""}
                    {saveState}
                  </span>
                </div>
                <h2>{draft.title}</h2>
                <p className="editor-subtitle">
                  Keep the team aligned on what comes next.
                </p>
                <fieldset disabled={locked}>
                  <div className="fields">
                    <label>
                      Status
                      <select
                        aria-label="Status"
                        value={draft.status}
                        onChange={(e) => edit("status", e.target.value)}
                      >
                        {["Backlog", "In progress", "Done"].map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Priority
                      <select
                        aria-label="Priority"
                        value={draft.priority}
                        onChange={(e) => edit("priority", e.target.value)}
                      >
                        {["Normal", "High", "Critical"].map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Assignee
                      <select
                        aria-label="Assignee"
                        value={draft.assignee}
                        onChange={(e) => edit("assignee", e.target.value)}
                      >
                        {["Maya", "Alex", "Jordan"].map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <label className="description-label" htmlFor="description">
                    Description <span>Autosaves after you stop typing</span>
                  </label>
                  <textarea
                    aria-label="Description"
                    id="description"
                    value={draft.description}
                    onChange={(e) => edit("description", e.target.value)}
                  />
                  <div className="review-row">
                    <div>
                      <strong>Review status</strong>
                      <p>Reviewing a prerequisite updates release readiness.</p>
                    </div>
                    <button
                      aria-pressed={draft.reviewed}
                      className={`review-button ${draft.reviewed ? "reviewed" : ""}`}
                      onClick={() => edit("reviewed", !draft.reviewed)}
                    >
                      {draft.reviewed ? "✓ Reviewed" : "Mark reviewed"}
                    </button>
                  </div>
                </fieldset>
                {error && (
                  <div className="error" role="alert">
                    {error}
                    {saveState === "Failed" && (
                      <button onClick={() => void save(true)}>
                        Retry save
                      </button>
                    )}
                    {saveState === "Conflict" && (
                      <button onClick={() => void reload()}>
                        Discard draft and load latest
                      </button>
                    )}
                  </div>
                )}
                <div className="activity-heading">
                  <h3>Activity</h3>
                  <span>Version {draft.version}</span>
                </div>
                <div className="activity-list">
                  {activity.length ? (
                    activity
                      .slice(-5)
                      .reverse()
                      .map((a) => (
                        <div className="activity-item" key={a.id}>
                          <span className="activity-dot" />
                          <div>
                            <strong>
                              {a.kind === "task.updated"
                                ? "Task updated"
                                : a.kind === "readiness.updated"
                                  ? "Release readiness updated"
                                  : a.kind === "task.compensated"
                                    ? "Task restored"
                                    : a.kind.replaceAll(".", " ")}
                            </strong>
                            <p>
                              {Object.entries(a.after || {})
                                .map(([k, v]) => `${k}: ${String(v)}`)
                                .join(" · ")}
                            </p>
                          </div>
                        </div>
                      ))
                  ) : (
                    <p className="empty">
                      Your team’s updates will appear here.
                    </p>
                  )}
                </div>
                <div className="comments">
                  <h3>Discussion</h3>
                  {comments.map((c) => (
                    <p key={c.id}>
                      <strong>{c.actor}</strong> {c.body}
                    </p>
                  ))}
                  <div className="comment-compose">
                    <input
                      aria-label="Comment"
                      placeholder="Share an update with the team…"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                    />
                    <button
                      disabled={posting || !comment.trim()}
                      onClick={() => void postComment()}
                    >
                      Post
                    </button>
                  </div>
                </div>
              </>
            )}
          </section>
        </div>
        {notices.length > 0 && (
          <section className="inbox">
            <h3>Release inbox</h3>
            {notices.map((n) => (
              <div key={n.id}>
                <span>{n.delivered ? "●" : "○"}</span>
                {n.message}
                <small>
                  {n.delivered
                    ? "Received by release observer"
                    : "Pending delivery"}
                </small>
              </div>
            ))}
          </section>
        )}
        <footer>
          FlowBoard <span>Connected work. Considered actions.</span>
          <span className="fixture-label">
            AfterClick · controlled research testbed
          </span>
        </footer>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
