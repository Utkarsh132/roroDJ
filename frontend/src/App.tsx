import {
  AudioLines,
  ChevronRight,
  CircleAlert,
  FileAudio,
  MessageSquareText,
  Moon,
  Send,
  SlidersHorizontal,
  Sparkles,
  Sun,
  Upload,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { analyzeAudio, sendChat } from "./api";
import type { AudioAnalysis, CreativeRole, Message } from "./types";

const ROLES: { id: CreativeRole; label: string; detail: string }[] = [
  { id: "dj", label: "DJ", detail: "Sets, transitions, energy" },
  { id: "singer", label: "Singer", detail: "Vocals, hooks, recording" },
  { id: "producer", label: "Producer", detail: "Arrangement, sound, mix" },
  { id: "musician", label: "Musician", detail: "Harmony, technique, melody" },
  { id: "general", label: "General", detail: "Music and platform help" },
];

const EQ_BANDS = [60, 120, 250, 500, 1000, 2000, 4000, 8000];

function Logo() {
  return (
    <div className="brand" aria-label="roroDJ">
      <svg className="logo" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <path d="M7 25V15M13 30V10M19 25V15M25 33V7M31 27V13" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        <path d="M5 20h28" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity=".45" />
      </svg>
      <span>roro<strong>DJ</strong></span>
    </div>
  );
}

function Studio() {
  const [file, setFile] = useState<File | null>(null);
  const [sourceUrl, setSourceUrl] = useState("");
  const [gains, setGains] = useState<number[]>(EQ_BANDS.map(() => 0));
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const filtersRef = useRef<BiquadFilterNode[]>([]);
  const connectedRef = useRef(false);

  useEffect(() => {
    return () => {
      if (sourceUrl) URL.revokeObjectURL(sourceUrl);
    };
  }, [sourceUrl]);

  const prepareAudio = () => {
    if (!audioRef.current || connectedRef.current) return;
    const context = new AudioContext();
    const source = context.createMediaElementSource(audioRef.current);
    const filters = EQ_BANDS.map((frequency, index) => {
      const filter = context.createBiquadFilter();
      filter.type = index === 0 ? "lowshelf" : index === EQ_BANDS.length - 1 ? "highshelf" : "peaking";
      filter.frequency.value = frequency;
      filter.Q.value = 1.1;
      filter.gain.value = gains[index];
      return filter;
    });
    source.connect(filters[0]);
    filters.forEach((filter, index) => filter.connect(filters[index + 1] || context.destination));
    contextRef.current = context;
    filtersRef.current = filters;
    connectedRef.current = true;
  };

  const togglePlayback = async () => {
    if (!audioRef.current) return;
    prepareAudio();
    await contextRef.current?.resume();
    if (audioRef.current.paused) {
      await audioRef.current.play();
      setPlaying(true);
    } else {
      audioRef.current.pause();
      setPlaying(false);
    }
  };

  const chooseFile = (next: File | null) => {
    if (!next) return;
    if (sourceUrl) URL.revokeObjectURL(sourceUrl);
    setFile(next);
    setSourceUrl(URL.createObjectURL(next));
    setPlaying(false);
    connectedRef.current = false;
    filtersRef.current = [];
    contextRef.current?.close();
    contextRef.current = null;
  };

  const changeGain = (index: number, value: number) => {
    setGains((current) => current.map((gain, i) => (i === index ? value : gain)));
    if (filtersRef.current[index]) filtersRef.current[index].gain.value = value;
  };

  return (
    <section className="studio" aria-labelledby="studio-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Browser audio engine</span>
          <h1 id="studio-title">Shape the tone before export.</h1>
        </div>
        <span className="status"><span /> Non-destructive</span>
      </div>

      <div className="deck">
        <div className="track-well">
          <AudioLines size={26} />
          {file ? (
            <div>
              <strong>{file.name}</strong>
              <span>{(file.size / 1024 / 1024).toFixed(1)} MB</span>
            </div>
          ) : (
            <div>
              <strong>No track loaded</strong>
              <span>Choose an audio file to activate the EQ</span>
            </div>
          )}
          <label className="file-button">
            <Upload size={17} />
            Load track
            <input data-testid="input-studio-audio" type="file" accept="audio/*" onChange={(event) => chooseFile(event.target.files?.[0] || null)} />
          </label>
        </div>
        <audio ref={audioRef} src={sourceUrl} onEnded={() => setPlaying(false)} />
        <button className="transport" data-testid="button-playback" disabled={!file} onClick={togglePlayback}>
          {playing ? "Pause" : "Play through EQ"}
        </button>
      </div>

      <div className="eq-panel">
        <div className="eq-head">
          <div><SlidersHorizontal size={19} /><strong>Eight-band equalizer</strong></div>
          <button data-testid="button-reset-eq" onClick={() => gains.forEach((_, i) => changeGain(i, 0))}>Reset</button>
        </div>
        <div className="eq-bands">
          {EQ_BANDS.map((frequency, index) => (
            <label className="eq-band" key={frequency}>
              <output>{gains[index] > 0 ? "+" : ""}{gains[index].toFixed(1)}</output>
              <input
                data-testid={`input-eq-${frequency}`}
                type="range"
                min="-12"
                max="12"
                step=".5"
                value={gains[index]}
                onChange={(event) => changeGain(index, Number(event.target.value))}
                aria-label={`${frequency} hertz gain`}
              />
              <span>{frequency >= 1000 ? `${frequency / 1000}k` : frequency} Hz</span>
            </label>
          ))}
        </div>
      </div>
      <p className="fine-print">The EQ is real-time and stays inside your browser. Export and automation are the next studio milestone.</p>
    </section>
  );
}

function App() {
  const [activeView, setActiveView] = useState<"copilot" | "studio">("copilot");
  const [role, setRole] = useState<CreativeRole>("producer");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { id: "welcome", author: "assistant", content: "What are we making today? Give me a genre, mood, reference, or upload a rough bounce." },
  ]);
  const [suggestions, setSuggestions] = useState(["Build an arrangement", "Diagnose a mix", "Create a sound-design recipe"]);
  const [analysis, setAnalysis] = useState<AudioAnalysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">(
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
  );
  const sessionId = useMemo(() => crypto.randomUUID(), []);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const submit = async (event?: FormEvent, override?: string) => {
    event?.preventDefault();
    const text = (override || message).trim();
    if (!text || busy) return;
    setMessage("");
    setError("");
    setMessages((items) => [...items, { id: crypto.randomUUID(), author: "user", content: text }]);
    setBusy(true);
    try {
      const result = await sendChat(sessionId, role, text);
      setMessages((items) => [...items, { id: crypto.randomUUID(), author: "assistant", content: result.reply }]);
      setSuggestions(result.suggested_actions);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "roroDJ could not answer.");
    } finally {
      setBusy(false);
    }
  };

  const uploadForAnalysis = async (file: File | null) => {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      setAnalysis(await analyzeAudio(file));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Audio analysis failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <header>
        <Logo />
        <nav aria-label="Primary">
          <button data-testid="nav-copilot" className={activeView === "copilot" ? "active" : ""} onClick={() => setActiveView("copilot")}>
            <MessageSquareText size={17} /> Copilot
          </button>
          <button data-testid="nav-studio" className={activeView === "studio" ? "active" : ""} onClick={() => setActiveView("studio")}>
            <SlidersHorizontal size={17} /> Studio
          </button>
        </nav>
        <button className="icon-button" data-testid="button-theme" aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`} onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </header>

      <main id="main">
        {activeView === "studio" ? <Studio /> : (
          <div className="app-grid">
            <aside aria-label="Creative mode">
              <div className="aside-title">
                <span className="eyebrow">Creative mode</span>
                <p>roroDJ changes its tools and vocabulary around your work.</p>
              </div>
              <div className="role-list">
                {ROLES.map((item) => (
                  <button
                    data-testid={`role-${item.id}`}
                    className={role === item.id ? "role active" : "role"}
                    key={item.id}
                    onClick={() => setRole(item.id)}
                  >
                    <span><strong>{item.label}</strong><small>{item.detail}</small></span>
                    <ChevronRight size={17} />
                  </button>
                ))}
              </div>
              <label className="upload-card">
                <FileAudio size={22} />
                <strong>Analyze a recording</strong>
                <span>BPM, key, levels, clipping, silence and mic guidance.</span>
                <input data-testid="input-analysis-audio" type="file" accept="audio/*" onChange={(event) => uploadForAnalysis(event.target.files?.[0] || null)} />
              </label>
            </aside>

            <section className="chat-shell" aria-labelledby="copilot-title">
              <div className="chat-header">
                <div>
                  <span className="eyebrow">roroDJ copilot</span>
                  <h1 id="copilot-title">{ROLES.find((item) => item.id === role)?.label} session</h1>
                </div>
                <span className="status"><span /> Ready</span>
              </div>

              <div className="messages" ref={scrollRef} aria-live="polite">
                {messages.map((item) => (
                  <article className={`message ${item.author}`} key={item.id}>
                    {item.author === "assistant" && <Sparkles size={17} aria-hidden="true" />}
                    <p>{item.content}</p>
                  </article>
                ))}
                {busy && <div className="thinking"><span /><span /><span /><em>Listening to the idea</em></div>}
                {error && <div className="error" role="alert"><CircleAlert size={18} /><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError("")}><X size={17} /></button></div>}
              </div>

              <div className="suggestions" aria-label="Suggested prompts">
                {suggestions.map((suggestion) => (
                  <button data-testid={`suggestion-${suggestion.toLowerCase().replaceAll(" ", "-")}`} key={suggestion} onClick={() => submit(undefined, suggestion)}>
                    {suggestion}
                  </button>
                ))}
              </div>
              <form className="composer" onSubmit={submit}>
                <label className="sr-only" htmlFor="message">Message roroDJ</label>
                <textarea
                  id="message"
                  data-testid="input-message"
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      submit();
                    }
                  }}
                  placeholder={`Ask in ${role} mode…`}
                  rows={2}
                />
                <button data-testid="button-send" type="submit" disabled={!message.trim() || busy} aria-label="Send message"><Send size={19} /></button>
              </form>
            </section>

            <aside className="analysis-panel" aria-label="Audio analysis">
              <span className="eyebrow">Signal report</span>
              {!analysis ? (
                <div className="empty-analysis">
                  <AudioLines size={34} />
                  <strong>Your audio fingerprint appears here.</strong>
                  <p>Upload a bounce or vocal take to get technical feedback.</p>
                </div>
              ) : (
                <div className="analysis-content" data-testid="audio-analysis">
                  <strong className="filename">{analysis.filename}</strong>
                  <div className="metrics">
                    <div><span>BPM</span><strong>{analysis.metrics.bpm ?? "—"}</strong></div>
                    <div><span>Key</span><strong>{analysis.metrics.key_estimate ?? "—"}</strong></div>
                    <div><span>Peak</span><strong>{analysis.metrics.peak_dbfs} dB</strong></div>
                    <div><span>RMS</span><strong>{analysis.metrics.rms_dbfs} dB</strong></div>
                  </div>
                  {analysis.warnings.map((warning) => <p className="warning" key={warning}>{warning}</p>)}
                  <ul>{analysis.suggestions.map((tip) => <li key={tip}>{tip}</li>)}</ul>
                </div>
              )}
            </aside>
          </div>
        )}
      </main>
    </>
  );
}

export default App;
