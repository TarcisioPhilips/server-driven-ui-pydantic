import { useState } from "react";
import { ClientPane } from "./components/ClientPane";

const SAMPLE_PROMPTS = [
  "add a Pix discount banner",
  "skip biometric step",
  "show welcome with promo banner",
];

export default function App() {
  const [simulateUnknown, setSimulateUnknown] = useState(false);
  const [prompt, setPrompt] = useState(SAMPLE_PROMPTS[0]);
  const [agentPrompt, setAgentPrompt] = useState<string | null>(null);
  const [agentNonce, setAgentNonce] = useState(0);

  function runAgent() {
    const trimmed = prompt.trim();
    if (!trimmed) return;
    setAgentPrompt(trimmed);
    setAgentNonce((n) => n + 1);
  }

  return (
    <div className="app">
      <div className="atmosphere" aria-hidden="true" />
      <header className="top">
        <div className="brand">
          <span className="brand__mark">Acme Pay</span>
          <h1>Server-Driven UI Simulator</h1>
          <p>
            App v1 (legacy) and App v2 (current) hit the same FastAPI contract —
            negotiation, downgrade, and generative UI side by side.
          </p>
        </div>
        <div className="controls">
          <label className="toggle">
            <input
              type="checkbox"
              checked={simulateUnknown}
              onChange={(e) => setSimulateUnknown(e.target.checked)}
            />
            <span>simulate_unknown</span>
          </label>
          <div className="agent-box">
            <label htmlFor="agent-prompt">Generative UI prompt</label>
            <div className="agent-row">
              <input
                id="agent-prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                list="sample-prompts"
                placeholder='e.g. "add a Pix discount banner"'
              />
              <datalist id="sample-prompts">
                {SAMPLE_PROMPTS.map((p) => (
                  <option key={p} value={p} />
                ))}
              </datalist>
              <button type="button" className="sdui-btn sdui-btn--primary" onClick={runAgent}>
                POST /agent/screen
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="sim-grid">
        <ClientPane
          version={1}
          simulateUnknown={simulateUnknown}
          agentPrompt={agentPrompt}
          agentNonce={agentNonce}
        />
        <ClientPane
          version={2}
          simulateUnknown={simulateUnknown}
          agentPrompt={agentPrompt}
          agentNonce={agentNonce}
        />
      </main>
    </div>
  );
}
