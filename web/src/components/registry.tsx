import type { ComponentType, ReactNode } from "react";
import type {
  Action,
  BiometricPromptComponent,
  ButtonComponent,
  Component,
  HeaderComponent,
  InputComponent,
  PixQrComponent,
  TextComponent,
} from "../types/sdui";
import { V1_COMPONENTS, V2_COMPONENTS } from "../types/sdui";
import { UnknownComponent } from "./UnknownComponent";

export type ActionHandler = (action: Action) => void;

export type RenderContext = {
  clientVersion: 1 | 2;
  onAction: ActionHandler;
  formValues: Record<string, string>;
  onInputChange: (name: string, value: string) => void;
};

type CompProps<T> = { component: T; ctx: RenderContext };

function HeaderView({ component }: CompProps<HeaderComponent>) {
  return (
    <header className="sdui-header">
      <h2>{component.title}</h2>
      {component.subtitle ? <p>{component.subtitle}</p> : null}
    </header>
  );
}

function TextView({ component }: CompProps<TextComponent>) {
  const variant = component.variant ?? "body";
  return (
    <div className={`sdui-text sdui-text--${variant}`}>
      <p>{component.content}</p>
      {component.copyable ? (
        <button
          type="button"
          className="sdui-copy"
          onClick={() => void navigator.clipboard?.writeText(component.content)}
        >
          Copy
        </button>
      ) : null}
    </div>
  );
}

function InputView({ component, ctx }: CompProps<InputComponent>) {
  return (
    <label className="sdui-input">
      <span>{component.label}</span>
      <input
        name={component.name}
        type={component.input_type ?? "text"}
        placeholder={component.placeholder ?? undefined}
        required={component.required}
        value={ctx.formValues[component.name] ?? ""}
        onChange={(e) => ctx.onInputChange(component.name, e.target.value)}
      />
    </label>
  );
}

function ButtonView({ component, ctx }: CompProps<ButtonComponent>) {
  const variant = component.variant ?? "primary";
  return (
    <button
      type="button"
      className={`sdui-btn sdui-btn--${variant}`}
      onClick={() => ctx.onAction(component.action)}
    >
      {component.label}
    </button>
  );
}

function PixQrView({ component }: CompProps<PixQrComponent>) {
  return (
    <div className="sdui-pix" data-testid="pix-qr">
      <div className="sdui-pix__qr" aria-hidden="true">
        <span>PIX</span>
        <small>QR</small>
      </div>
      <div className="sdui-pix__meta">
        <strong>R$ {component.amount}</strong>
        <p className="mono">{component.copy_paste_key}</p>
        <small>Expires in {Math.round((component.expires_in_seconds ?? 300) / 60)} min</small>
      </div>
    </div>
  );
}

function BiometricView({ component, ctx }: CompProps<BiometricPromptComponent>) {
  return (
    <div className="sdui-bio" data-testid="biometric-prompt">
      <div className="sdui-bio__icon" aria-hidden="true">
        ⌖
      </div>
      <div>
        <strong>{component.title}</strong>
        <p>{component.reason}</p>
        <div className="sdui-bio__actions">
          <button
            type="button"
            className="sdui-btn sdui-btn--primary"
            onClick={() => ctx.onAction(component.action)}
          >
            Authenticate
          </button>
          <button
            type="button"
            className="sdui-btn sdui-btn--secondary"
            onClick={() => ctx.onAction(component.action)}
          >
            {component.fallback_label ?? "Use verification code"}
          </button>
        </div>
      </div>
    </div>
  );
}

type AnyRenderer = ComponentType<{ component: Component; ctx: RenderContext }>;

const RENDERERS: Record<string, AnyRenderer> = {
  header: HeaderView as AnyRenderer,
  text: TextView as AnyRenderer,
  input: InputView as AnyRenderer,
  button: ButtonView as AnyRenderer,
  pix_qr: PixQrView as AnyRenderer,
  biometric_prompt: BiometricView as AnyRenderer,
};

export function supportedTypesFor(version: 1 | 2): readonly string[] {
  return version === 1 ? V1_COMPONENTS : V2_COMPONENTS;
}

export function isRegistered(type: string, version: 1 | 2): boolean {
  return supportedTypesFor(version).includes(type) && type in RENDERERS;
}

export function renderComponent(component: Component, ctx: RenderContext): ReactNode {
  if (!isRegistered(component.type, ctx.clientVersion)) {
    return (
      <UnknownComponent
        key={component.id}
        type={component.type}
        id={component.id}
        raw={component as Record<string, unknown>}
      />
    );
  }
  const Renderer = RENDERERS[component.type];
  return <Renderer key={component.id} component={component} ctx={ctx} />;
}

export { RENDERERS };
