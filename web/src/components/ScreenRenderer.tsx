import { useMemo, useState } from "react";
import type { Action, Component, ScreenResponse } from "../types/sdui";
import { renderComponent, type ActionHandler } from "./registry";

type Props = {
  screen: ScreenResponse | null;
  clientVersion: 1 | 2;
  onAction: ActionHandler;
  loading?: boolean;
  error?: string | null;
};

export function ScreenRenderer({
  screen,
  clientVersion,
  onAction,
  loading,
  error,
}: Props) {
  const [formValues, setFormValues] = useState<Record<string, string>>({});

  const byId = useMemo(() => {
    const map = new Map<string, Component>();
    for (const c of screen?.components ?? []) {
      map.set(c.id, c);
    }
    return map;
  }, [screen]);

  if (loading) {
    return <div className="sdui-state">Loading screen…</div>;
  }
  if (error) {
    return <div className="sdui-state sdui-state--error">{error}</div>;
  }
  if (!screen) {
    return <div className="sdui-state">No screen loaded</div>;
  }

  const ctx = {
    clientVersion,
    onAction: (action: Action) => onAction(action),
    formValues,
    onInputChange: (name: string, value: string) =>
      setFormValues((prev) => ({ ...prev, [name]: value })),
  };

  return (
    <article className="sdui-screen" data-screen={screen.screen_id}>
      <div className="sdui-screen__chrome">
        <span className="sdui-pill">App v{clientVersion}</span>
        <span className="sdui-screen__title">{screen.title}</span>
      </div>
      <div className={`sdui-screen__body sdui-layout--${screen.layout.type}`}>
        {screen.layout.sections.map((section) => (
          <section key={section.id} className="sdui-section" data-section={section.id}>
            {section.component_ids.map((id) => {
              const comp = byId.get(id);
              if (!comp) {
                return (
                  <div key={id} className="sdui-state sdui-state--error">
                    Missing component: {id}
                  </div>
                );
              }
              return renderComponent(comp, ctx);
            })}
          </section>
        ))}
      </div>
    </article>
  );
}
