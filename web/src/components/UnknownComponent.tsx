type Props = {
  type: string;
  id: string;
  raw: Record<string, unknown>;
};

/** Graceful fallback boundary for unsupported component types. */
export function UnknownComponent({ type, id, raw }: Props) {
  return (
    <div className="sdui-unknown" role="status" data-testid="unknown-component">
      <strong>Unsupported component</strong>
      <span>
        <code>{type}</code> (<code>{id}</code>) is not available on this client.
      </span>
      <details>
        <summary>Raw payload</summary>
        <pre>{JSON.stringify(raw, null, 2)}</pre>
      </details>
    </div>
  );
}
