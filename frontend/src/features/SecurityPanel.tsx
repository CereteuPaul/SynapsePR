type RoadmapItem = {
  file_path: string;
  review_priority: number;
  change_type: string;
  architectural_impact?: string | null;
  risk_flags?: string[];
};

type Drift = {
  violates_patterns: boolean;
  explanation: string;
};

type Props = {
  drift?: Drift;
  roadmap?: RoadmapItem[];
};

export default function SecurityPanel({ drift, roadmap }: Props) {
  const riskItems = (roadmap || [])
    .flatMap((item) => item.risk_flags || [])
    .slice(0, 6);

  const highPriority = (roadmap || []).filter(
    (item) => item.review_priority <= 2,
  ).length;

  return (
    <div className="card-panel tab-panel">
      <div className="section-head">
        <div>
          <div className="eyebrow">Security / Risk</div>
          <h2>Trust boundaries and drift</h2>
        </div>
        <span className="repo-chip">{highPriority} critical</span>
      </div>

      <div className="risk-grid">
        <div className="risk-card">
          <strong>Architectural drift</strong>
          <p>
            {drift?.explanation ||
              "No drift explanation available yet. Analyze a diff to see pattern violations."}
          </p>
        </div>

        <div className="risk-card">
          <strong>Priority focus</strong>
          <p>
            {highPriority > 0
              ? `${highPriority} items are high priority and should be reviewed first.`
              : "No high priority items are currently flagged."}
          </p>
        </div>

        <div className="risk-card">
          <strong>Flag summary</strong>
          {riskItems.length > 0 ? (
            <ul className="risk-list">
              {riskItems.map((flag, index) => (
                <li key={`${flag}-${index}`}>{flag}</li>
              ))}
            </ul>
          ) : (
            <p>No flags were returned in the roadmap response.</p>
          )}
        </div>
      </div>
    </div>
  );
}
