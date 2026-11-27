import { useCallback, useEffect, useState } from "react";
import { agentScreen, fetchScreen, submitAction } from "../lib/api";
import type { Action, ClientVersion, ScreenResponse } from "../types/sdui";
import { ScreenRenderer } from "./ScreenRenderer";

type Props = {
  version: ClientVersion;
  simulateUnknown: boolean;
  agentPrompt: string | null;
  agentNonce: number;
};

export function ClientPane({
  version,
  simulateUnknown,
  agentPrompt,
  agentNonce,
}: Props) {
  const [screen, setScreen] = useState<ScreenResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inspectorOpen, setInspectorOpen] = useState(false);

  const load = useCallback(
    async (screenId: string) => {
      setLoading(true);
      setError(null);
      try {
        const next = await fetchScreen(screenId, version, simulateUnknown);
        setScreen(next);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Load failed");
      } finally {
        setLoading(false);
      }
    },
    [version, simulateUnknown],
  );

  useEffect(() => {
    void load("welcome");
  }, [load]);

  useEffect(() => {
    if (!agentPrompt || agentNonce === 0) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const next = await agentScreen(agentPrompt, version, simulateUnknown);
        if (!cancelled) setScreen(next);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Agent failed");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [agentPrompt, agentNonce, version, simulateUnknown]);

  const onAction = useCallback(
    async (action: Action) => {
      if (action.type === "navigate") {
        await load(action.screen_id);
        return;
      }
      if (action.type === "submit") {
        setLoading(true);
        try {
          const result = await submitAction(action.endpoint, version);
          if (result.next_screen) {
            // Adapt next_screen was built for v2 — re-fetch confirmation for this client
            await load(result.next_screen.screen_id);
          }
        } catch (err) {
          setError(err instanceof Error ? err.message : "Submit failed");
        } finally {
          setLoading(false);
        }
        return;
      }
      if (action.type === "open_modal") {
        window.alert(`Modal: ${action.title ?? action.modal_id}`);
      }
    },
    [load, version],
  );

  return (
    <div className="client-pane">
      <ScreenRenderer
        screen={screen}
        clientVersion={version}
        onAction={(a) => void onAction(a)}
        loading={loading}
        error={error}
      />
      <div className="inspector">
        <button
          type="button"
          className="inspector__toggle"
          onClick={() => setInspectorOpen((o) => !o)}
        >
          {inspectorOpen ? "Hide" : "Show"} JSON Contract Inspector (v{version})
        </button>
        {inspectorOpen && screen ? (
          <pre className="inspector__json">{JSON.stringify(screen, null, 2)}</pre>
        ) : null}
      </div>
    </div>
  );
}
