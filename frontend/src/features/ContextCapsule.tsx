type Props = {
  intent?: string;
  explanation?: string | null;
};

export default function ContextCapsule({ intent, explanation }: Props) {
  return (
    <div
      style={{
        marginTop: 12,
        padding: 12,
        borderRadius: 12,
        background: "rgba(2,6,23,0.6)",
        border: "1px solid rgba(148,163,184,0.06)",
      }}
    >
      <div style={{ fontSize: 12, color: "#cbd5e1", marginBottom: 6 }}>
        Context Capsule
      </div>
      <div style={{ color: "#e2e8f0", fontWeight: 700 }}>
        {intent || "No intent available"}
      </div>
      {explanation ? (
        <div style={{ marginTop: 8, color: "#cbd5e1" }}>{explanation}</div>
      ) : (
        <div style={{ marginTop: 8, color: "#94a3b8" }}>
          No additional context provided.
        </div>
      )}
    </div>
  );
}
