import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  isRegistered,
  renderComponent,
  RENDERERS,
  supportedTypesFor,
  type RenderContext,
} from "../components/registry";
import type { Component, ScreenResponse } from "../types/sdui";
import { V1_COMPONENTS, V2_COMPONENTS } from "../types/sdui";

function ctx(version: 1 | 2 = 2): RenderContext {
  return {
    clientVersion: version,
    onAction: vi.fn(),
    formValues: {},
    onInputChange: vi.fn(),
  };
}

describe("component registry", () => {
  it("registers v1 and v2 catalogs", () => {
    expect(supportedTypesFor(1)).toEqual([...V1_COMPONENTS]);
    expect(supportedTypesFor(2)).toEqual([...V2_COMPONENTS]);
    for (const type of V2_COMPONENTS) {
      expect(type in RENDERERS).toBe(true);
    }
  });

  it("marks pix_qr as unsupported on App v1", () => {
    expect(isRegistered("pix_qr", 1)).toBe(false);
    expect(isRegistered("pix_qr", 2)).toBe(true);
    expect(isRegistered("biometric_prompt", 1)).toBe(false);
  });

  it("renders UnknownComponent for unsupported types without crashing", () => {
    const unknown = {
      type: "futuristic_hologram",
      id: "sim_unknown_widget",
      content: "Holographic payment confirmation (unsupported)",
    } as Component;

    render(<>{renderComponent(unknown, ctx(2))}</>);

    const fallback = screen.getByTestId("unknown-component");
    expect(fallback).toBeInTheDocument();
    expect(fallback).toHaveTextContent("Unsupported component");
    expect(fallback).toHaveTextContent("futuristic_hologram");
  });

  it("renders known header on both client versions", () => {
    const header = {
      type: "header" as const,
      id: "hdr",
      title: "Acme Pay",
      subtitle: "Checkout",
    };
    const { rerender } = render(<>{renderComponent(header, ctx(1))}</>);
    expect(screen.getByText("Acme Pay")).toBeInTheDocument();
    rerender(<>{renderComponent(header, ctx(2))}</>);
    expect(screen.getByText("Acme Pay")).toBeInTheDocument();
  });
});

describe("ScreenResponse shape (contract mirror)", () => {
  it("accepts a minimal valid screen payload", () => {
    const screen: ScreenResponse = {
      schema_version: "1.0",
      screen_id: "welcome",
      title: "Welcome",
      layout: {
        type: "column",
        sections: [{ id: "hero", component_ids: ["hdr"] }],
      },
      components: [{ type: "header", id: "hdr", title: "Hi" }],
      data: {},
      meta: {},
    };
    expect(screen.components).toHaveLength(1);
  });
});
