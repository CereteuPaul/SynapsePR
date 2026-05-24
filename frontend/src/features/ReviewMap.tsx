type RoadmapItem = {
  file_path: string;
  review_priority: number;
  change_type: string;
  architectural_impact?: string | null;
  risk_flags?: string[];
};

type Summary = {
  intent: string;
  cognitive_load_score: string;
  total_impacted_modules: number;
};

type Drift = {
  violates_patterns: boolean;
  explanation: string;
};

import Thermometer from "../components/Thermometer";
import SynapseMap from "./SynapseMap";
import ContextCapsule from "./ContextCapsule";

type Props = {
  summary?: Summary;
  roadmap?: RoadmapItem[];
  drift?: Drift;
  activeTab?: string;
};

export default function ReviewMap({
  summary,
  roadmap,
  drift,
  activeTab = "overview",
}: Props) {
  const roadmapItems = roadmap || [];

  return (
    <div className="review-map">
      <div className="review-map-header">
        <h3>Review Roadmap</h3>
        <span className="pill">{activeTab.replace("-", " ")}</span>
      </div>
      {summary ? (
        <div className="summary">
          <Thermometer level={summary.cognitive_load_score} />
          <div className="summary-grid">
            <div>
              <strong>Intent</strong>
              <p>{summary.intent}</p>
            </div>
            <div>
              <strong>Cognitive Load</strong>
              <p>
                <span
                  className={`badge load-${summary.cognitive_load_score.toLowerCase()}`}
                >
                  {summary.cognitive_load_score}
                </span>
              </p>
            </div>
            <div>
              <strong>Impacted Modules</strong>
              <p>{summary.total_impacted_modules}</p>
            </div>
          </div>
          <SynapseMap roadmap={roadmap} />
          {drift && (
            <div
              className={`drift-card ${drift.violates_patterns ? "warning" : "ok"}`}
            >
              <strong>Architectural Risk</strong>
              <p>{drift.explanation}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-review">
          <div className="empty-illustration" aria-hidden="true">
            <div className="empty-node node-a" />
            <div className="empty-node node-b" />
            <div className="empty-node node-c" />
            <div className="empty-line line-a" />
            <div className="empty-line line-b" />
          </div>
          <div>
            <strong>No analysis yet</strong>
            <p>
              Paste a git diff and analyze it to generate the roadmap, risk
              view, and visual map.
            </p>
          </div>
        </div>
      )}

      {summary && (
        <ContextCapsule
          intent={summary.intent}
          explanation={drift?.explanation}
        />
      )}

      <ul className="roadmap-list">
        {roadmapItems.map((r) => (
          <li key={r.file_path} className="roadmap-item">
            <div className="priority">#{r.review_priority}</div>
            <div className="path">{r.file_path}</div>
            <div className="meta">
              <span className="type">{r.change_type}</span>
              {r.risk_flags && r.risk_flags.length > 0 && (
                <span className="risk">⚠️ {r.risk_flags.join(", ")}</span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
