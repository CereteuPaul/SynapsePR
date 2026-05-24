import { useState } from "react";
import "./App.css";
import logo from "./assets/SynapsePRlogo.png";
import CoachPanel from "./features/CoachPanel";
import Dashboard from "./features/Dashboard";
import OrgSwitcher, { type Tenant } from "./features/OrgSwitcher";
import SecurityPanel from "./features/SecurityPanel";
import ReviewMap from "./features/ReviewMap";

type AnalyzeResponse = {
  summary: {
    intent: string;
    cognitive_load_score: string;
    total_impacted_modules: number;
  };
  review_roadmap: any[];
  architectural_drift: {
    violates_patterns: boolean;
    explanation: string;
  };
};

type Repository = {
  name: string;
  activePRs: number;
  state: string;
};

function App() {
  const tenants: Tenant[] = [
    { id: "personal", name: "Personal Projects" },
    { id: "acme", name: "Acme Corp" },
    { id: "lateral", name: "Lateral Tech" },
  ];

  const repositoryMap: Record<string, Repository[]> = {
    personal: [
      { name: "portfolio-site", activePRs: 1, state: "All Clear" },
      { name: "notes-api", activePRs: 2, state: "Review Needed" },
      { name: "automation-scripts", activePRs: 0, state: "All Clear" },
    ],
    acme: [
      { name: "core-api", activePRs: 3, state: "Review Needed" },
      { name: "frontend-app", activePRs: 5, state: "Review Needed" },
      { name: "data-pipeline", activePRs: 1, state: "All Clear" },
    ],
    lateral: [
      { name: "billing-service", activePRs: 4, state: "Review Needed" },
      { name: "design-system", activePRs: 1, state: "All Clear" },
      { name: "mobile-client", activePRs: 2, state: "Review Needed" },
    ],
  };

  const [selectedTenant, setSelectedTenant] = useState<string>(tenants[0].id);
  const [selectedRepository, setSelectedRepository] = useState<string>(
    repositoryMap[tenants[0].id][0].name,
  );
  const [workspaceSection, setWorkspaceSection] = useState<
    "dashboard" | "repositories" | "active-prs" | "team-settings"
  >("dashboard");
  const [explorerCollapsed, setExplorerCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [diffText, setDiffText] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const repositories = repositoryMap[selectedTenant] || [];
  const selectedRepositoryMeta =
    repositories.find((item) => item.name === selectedRepository) ||
    repositories[0];

  const activeReviews = [
    {
      id: "pr-101",
      title: "Harden diff ingestion",
      repo: selectedRepository,
      state: "Reviewing",
    },
    {
      id: "pr-102",
      title: "Add workspace tabs",
      repo: "frontend-app",
      state: "Queued",
    },
    {
      id: "pr-103",
      title: "Refine AI validator",
      repo: "core-api",
      state: "Reviewing",
    },
  ];

  async function analyze() {
    setError(null);
    setLoading(true);
    setResult(null);

    if (!diffText || !diffText.trim()) {
      setError("Please paste a git diff into the text area before analyzing.");
      setLoading(false);
      return;
    }

    try {
      const resp = await fetch("http://localhost:8000/api/analyze-diff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          diff_text: diffText,
          repo: "demo-repo",
          tenant: selectedTenant,
        }),
      });

      if (!resp.ok) {
        const t = await resp.text();
        throw new Error(t || resp.statusText);
      }

      const data: AnalyzeResponse = await resp.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo-wrap">
          <img src={logo} alt="SynapsePR" className="site-logo" />
          <div>
            <div className="eyebrow">SynapsePR</div>
            <h1>Multi-tenant review workspace</h1>
          </div>
        </div>
        <OrgSwitcher
          tenants={tenants}
          selected={selectedTenant}
          onSelect={(tenantId) => {
            setSelectedTenant(tenantId);
            setSelectedRepository(repositoryMap[tenantId][0].name);
          }}
        />
      </header>

      <Dashboard
        repositories={repositories}
        selectedRepository={selectedRepository}
        onSelectRepository={setSelectedRepository}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        workspaceSection={workspaceSection}
        onSelectWorkspaceSection={setWorkspaceSection}
        selectedTenant={selectedTenant}
        onToggleExplorer={() => setExplorerCollapsed((value) => !value)}
        explorerCollapsed={explorerCollapsed}
        reviews={activeReviews}
      />

      <main className="main-grid">
        <section className="left">
          <div className="section-head">
            <div>
              <div className="eyebrow">Current repository</div>
              <h2>{selectedRepository}</h2>
            </div>
            <span className="repo-chip">{selectedTenant}</span>
          </div>

          {activeTab === "overview" && (
            <>
              <div className="analyze-card">
                <h2>Analyze Git Diff</h2>
                <textarea
                  placeholder="Paste git diff here"
                  value={diffText}
                  onChange={(e) => setDiffText(e.target.value)}
                  rows={18}
                  className="diff-input"
                />
                <div className="actions">
                  <button onClick={analyze} disabled={loading} className="btn">
                    {loading ? "Analyzing…" : "Analyze"}
                  </button>
                  {error && <div className="error">{error}</div>}
                </div>
              </div>

              {!diffText.trim() && (
                <div className="empty-state">
                  <div className="warning-art" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                  </div>
                  <div>
                    <strong>Waiting for a diff</strong>
                    <p>
                      Paste a git diff above to generate a roadmap, assess
                      cognitive load, and surface architectural drift.
                    </p>
                  </div>
                </div>
              )}
            </>
          )}

          {activeTab === "visual-map" && (
            <div className="tab-panel card-panel">
              <h2>Visual Map</h2>
              <p>
                The D3 map shows the changed files as a dependency graph. Use
                the panel on the right to inspect the ranked review roadmap.
              </p>
              <div className="insight-strip">
                <div>
                  <strong>Repository</strong>
                  <p>{selectedRepositoryMeta?.name}</p>
                </div>
                <div>
                  <strong>Status</strong>
                  <p>{selectedRepositoryMeta?.state}</p>
                </div>
                <div>
                  <strong>Open PRs</strong>
                  <p>{selectedRepositoryMeta?.activePRs}</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <SecurityPanel
              drift={result?.architectural_drift}
              roadmap={result?.review_roadmap}
            />
          )}

          {activeTab === "coach" && (
            <CoachPanel
              intent={result?.summary?.intent}
              repository={selectedRepository}
            />
          )}
        </section>

        <aside className="right">
          {activeTab === "security" ? (
            <ReviewMap
              summary={result?.summary}
              roadmap={result?.review_roadmap}
              drift={result?.architectural_drift}
              activeTab={activeTab}
            />
          ) : activeTab === "coach" ? (
            <ReviewMap
              summary={result?.summary}
              roadmap={result?.review_roadmap}
              drift={result?.architectural_drift}
              activeTab={activeTab}
            />
          ) : (
            <ReviewMap
              summary={result?.summary}
              roadmap={result?.review_roadmap}
              drift={result?.architectural_drift}
              activeTab={activeTab}
            />
          )}
        </aside>
      </main>
    </div>
  );
}

export default App;
