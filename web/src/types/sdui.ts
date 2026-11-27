/**
 * TypeScript mirror of the Pydantic ScreenResponse contract.
 * Export JSON Schema from the API: GET /schema/screen
 *   curl -s http://localhost:8000/schema/screen > screen.schema.json
 */

export type NavigateAction = {
  type: "navigate";
  screen_id: string;
};

export type SubmitAction = {
  type: "submit";
  endpoint: string;
  method?: "POST" | "PUT";
};

export type OpenModalAction = {
  type: "open_modal";
  modal_id: string;
  title?: string | null;
};

export type Action = NavigateAction | SubmitAction | OpenModalAction;

export type HeaderComponent = {
  type: "header";
  id: string;
  title: string;
  subtitle?: string | null;
};

export type TextComponent = {
  type: "text";
  id: string;
  content: string;
  variant?: "body" | "caption" | "alert" | "success";
  copyable?: boolean;
};

export type InputComponent = {
  type: "input";
  id: string;
  label: string;
  name: string;
  input_type?: "text" | "email" | "password" | "tel";
  placeholder?: string | null;
  required?: boolean;
};

export type ButtonComponent = {
  type: "button";
  id: string;
  label: string;
  action: Action;
  variant?: "primary" | "secondary" | "danger";
};

export type PixQrComponent = {
  type: "pix_qr";
  id: string;
  payload: string;
  amount: string;
  copy_paste_key: string;
  expires_in_seconds?: number;
};

export type BiometricPromptComponent = {
  type: "biometric_prompt";
  id: string;
  title: string;
  reason: string;
  fallback_label?: string;
  action: Action;
};

/** Known catalog components (App v1 + v2). */
export type KnownComponent =
  | HeaderComponent
  | TextComponent
  | InputComponent
  | ButtonComponent
  | PixQrComponent
  | BiometricPromptComponent;

/** Wire component — may include unknown types from simulate_unknown. */
export type Component = KnownComponent | (Record<string, unknown> & { type: string; id: string });

export type Section = {
  id: string;
  component_ids: string[];
};

export type Layout = {
  type: "column" | "stack";
  sections: Section[];
};

export type ScreenResponse = {
  schema_version: "1.0";
  screen_id: string;
  title: string;
  layout: Layout;
  components: Component[];
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
};

export const V1_COMPONENTS = ["header", "text", "input", "button"] as const;
export const V2_COMPONENTS = [
  ...V1_COMPONENTS,
  "pix_qr",
  "biometric_prompt",
] as const;

export type ClientVersion = 1 | 2;
