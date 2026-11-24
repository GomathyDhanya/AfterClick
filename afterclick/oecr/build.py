"""Build an opt-in instrumented frontend without editing frozen application sources."""

import json
import subprocess
from pathlib import Path


def build():
    root = Path("artifacts/oecr-web")
    (root / "src").mkdir(parents=True, exist_ok=True)
    original = Path("apps/flowboard-web")
    text = (original / "src/main.tsx").read_text()
    text = text.replace(
        "function App() {",
        """const boot = (window as any).oecrBootstrap;
function App() {
  const refreshBusy = useRef(0);
  const held = useRef(!!boot);
  const queue = useRef<string[]>(boot?.queue ?? []);
  const saveDue = useRef<number | null>(null);
  const saveRemaining = useRef<number | null>(boot?.saveRemaining ?? null);
  const cursor = useRef(boot?.cursor ?? "0");
""",
    )
    mappings = {
        "useState<Task[]>([])": "useState<Task[]>(boot?.tasks ?? [])",
        'useState("TASK-42")': 'useState(boot?.selected ?? "TASK-42")',
        "useState<Task | null>(null)": "useState<Task | null>(boot?.draft ?? null)",
        'useState<SaveState>("Committed")': 'useState<SaveState>(boot?.saveState ?? "Committed")',
        ('const [error, setError] = useState("")'): (
            'const [error, setError] = useState(boot?.error ?? "")'
        ),
        ("const [connected, setConnected] = useState(false)"): (
            "const [connected, setConnected] = useState(boot?.connected ?? false)"
        ),
        "useState<Activity[]>([])": "useState<Activity[]>(boot?.activity ?? [])",
        "useState<Notice[]>([])": "useState<Notice[]>(boot?.notices ?? [])",
        ">([]);\n  const [comment": ">(boot?.comments ?? []);\n  const [comment",
        ('const [comment, setComment] = useState("")'): (
            'const [comment, setComment] = useState(boot?.comment ?? "")'
        ),
        "useRef<Task | null>(null)": "useRef<Task | null>(boot?.base ?? null)",
        "useRef<Partial<Editable>>({})": "useRef<Partial<Editable>>(boot?.dirty ?? {})",
        "useRef<Operation | null>(null)": "useRef<Operation | null>(boot?.operation ?? null)",
        ("const session = useRef(crypto.randomUUID())"): (
            "const session = useRef(boot?.session ?? crypto.randomUUID())"
        ),
    }
    for a, b in mappings.items():
        assert a in text, a
        text = text.replace(a, b)
    text = text.replace(
        "async function refresh() {",
        "async function refresh() {\n    refreshBusy.current++;\n    try {",
    )
    text = text.replace(
        "\n  useEffect(() => {\n    let active",
        "\n    finally { refreshBusy.current--; }\n  }\n\n  useEffect(() => {\n    let active",
        1,
    )
    # Existing refresh closing brace now closes try; inserted finally closes function.
    text = text.replace(
        "    refresh().catch((e) => setError(String(e)));\n    const events",
        "    if (!boot) refresh().catch((e) => setError(String(e)));\n    const events",
        1,
    )
    text = text.replace(
        "events.onopen = () => setConnected(true);",
        "events.onopen = () => { if (!held.current) setConnected(true); };",
    )
    text = text.replace(
        "events.onerror = () => setConnected(false);",
        "events.onerror = () => { if (!held.current) setConnected(false); };",
    )
    text = text.replace(
        "      if (!active) return;",
        (
            "      if (!active) return;\n      cursor.current=event.lastEventId"
            ";\n      if (held.current) { queue.current.push(event.lastEventId)"
            "; return; }"
        ),
        1,
    )
    text = text.replace(
        "    timer.current = setTimeout(() => void save(), 600);",
        (
            "    saveDue.current = Date.now()+600;\n    timer.current = setTime"
            "out(() => { saveDue.current=null; void save(); }, 600);"
        ),
    )
    hook = """
  (window as any).oecr = {
    pause: () => { held.current=true; clearTimeout(timer.current);
      if(saveDue.current!==null) {
        saveRemaining.current=Math.max(0,saveDue.current-Date.now());saveDue.current=null;
      } },
    capture: () => {
      if(busy.current || posting || refreshBusy.current)
        throw new Error("OECR_UNSUPPORTED_INFLIGHT");
      return JSON.parse(JSON.stringify({version:1,tasks,selected,draft,saveState,error,
        connected,activity,notices,comments,comment,base:base.current,dirty:dirty.current,
        operation:operation.current,session:session.current,queue:queue.current,cursor:cursor.current,
        saveRemaining:saveRemaining.current}));
    },
    resume: async () => {
      held.current=false;
      const pending=[...queue.current]; queue.current=[];
      for(const id of pending) await fetch(`/api/events/${id}/ack`,{
        method:"POST",headers:{"X-Session-ID":session.current}});
      if(pending.length) await refresh();
      if(saveRemaining.current!==null) {
        const remaining=saveRemaining.current;saveRemaining.current=null;
        saveDue.current=Date.now()+remaining;
        timer.current=setTimeout(()=>{saveDue.current=null;void save();},remaining);
      }
    },
    inflight: () => !!(busy.current || posting || refreshBusy.current),
    refresh: () => refresh(),
    queue: () => [...queue.current],
  };
"""
    text = text.replace("  const locked =", hook + "\n  const locked =", 1)
    (root / "src/main.tsx").write_text(text)
    (root / "src/style.css").write_bytes((original / "src/style.css").read_bytes())
    (root / "index.html").write_bytes((original / "index.html").read_bytes())
    (root / "tsconfig.json").write_bytes((original / "tsconfig.json").read_bytes())
    (root / "package.json").write_text(json.dumps({"type": "module"}))
    modules = root / "node_modules"
    if not modules.exists():
        modules.symlink_to((original / "node_modules").resolve(), target_is_directory=True)
    subprocess.run(
        [
            str((original / "node_modules/.bin/vite").resolve()),
            "build",
            str(root),
            "--outDir",
            "dist",
        ],
        check=True,
    )
    return root / "dist"


if __name__ == "__main__":
    build()
