type Props = {
  level: "Low" | "Medium" | "High" | string;
};

export default function Thermometer({ level }: Props) {
  const map = { Low: 20, Medium: 60, High: 90 };
  const pct = map[level as "Low" | "Medium" | "High"] ?? 40;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 12, color: "#cbd5e1", marginBottom: 6 }}>
        Cognitive Load
      </div>
      <div
        style={{
          height: 12,
          background: "rgba(255,255,255,0.06)",
          borderRadius: 999,
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            borderRadius: 999,
            background:
              pct > 80
                ? "linear-gradient(90deg,#fb7185,#ef4444)"
                : pct > 50
                  ? "linear-gradient(90deg,#f59e0b,#f97316)"
                  : "linear-gradient(90deg,#34d399,#10b981)",
          }}
        />
      </div>
    </div>
  );
}
