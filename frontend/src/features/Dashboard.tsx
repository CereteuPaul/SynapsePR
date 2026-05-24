type RepositoryStatus = {
  name: string;
  activePRs: number;
  state: string;
};

type ReviewItem = {
  id: string;
  title: string;
  repo: string;
  state: string;
};

type WorkspaceSection =
  | "dashboard"
  | "repositories"
  | "active-prs"
  | "team-settings";

type Props = {
  repositories: RepositoryStatus[];
  selectedRepository: string;
  onSelectRepository: (repositoryName: string) => void;
  activeTab: string;
  onSelectTab: (tab: string) => void;
  workspaceSection: WorkspaceSection;
  onSelectWorkspaceSection: (section: WorkspaceSection) => void;
  selectedTenant: string;
  onToggleExplorer: () => void;
  explorerCollapsed: boolean;
  reviews: ReviewItem[];
};

const workspaceTabs: { id: WorkspaceSection; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "repositories", label: "Repositories" },
  { id: "active-prs", label: "Active PR Reviews" },
  { id: "team-settings", label: "Team Settings" },
];

const canvasTabs = [
  { id: "overview", label: "Overview" },
  { id: "visual-map", label: "Visual Map" },
  { id: "security", label: "Security / Risk" },
  { id: "coach", label: "Interactive AI Coach" },
];

function RepositoryDot({ state }: { state: string }) {
  const className =
    state === "All Clear" ? "repo-dot clear" : "repo-dot active";
  return <span className={className} aria-hidden="true" />;
}

export default function Dashboard({
  repositories,
  selectedRepository,
  onSelectRepository,
  activeTab,
  onSelectTab,
  workspaceSection,
  onSelectWorkspaceSection,
  selectedTenant,
  onToggleExplorer,
  explorerCollapsed,
  reviews,
}: Props) {
  return (
    <div className="dashboard-shell">
      <section className="nav-panel">
        <div className="panel-title">Navigation</div>
        <nav className="tab-list" aria-label="Workspace navigation">
          {workspaceTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`tab-button ${workspaceSection === tab.id ? "active" : ""}`}
              onClick={() => onSelectWorkspaceSection(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="nav-summary">
          <div>
            <strong>Workspace</strong>
            <p>{selectedTenant}</p>
          </div>
          <button
            type="button"
            className="link-button"
            onClick={onToggleExplorer}
          >
            {explorerCollapsed
              ? "Expand repository explorer"
              : "Collapse repository explorer"}
          </button>
        </div>
      </section>

      <section className={`repo-panel ${explorerCollapsed ? "collapsed" : ""}`}>
        <div className="panel-title">Repositories</div>
        {!explorerCollapsed && (
          <div className="repo-list" role="list">
            {repositories.map((repository) => (
              <button
                key={repository.name}
                type="button"
                className={`repo-row ${selectedRepository === repository.name ? "selected" : ""}`}
                onClick={() => onSelectRepository(repository.name)}
                role="listitem"
              >
                <RepositoryDot state={repository.state} />
                <div className="repo-copy">
                  <div className="repo-name">{repository.name}</div>
                  <div className="repo-meta">
                    {repository.activePRs} Active PRs
                  </div>
                </div>
                <span className="repo-state">{repository.state}</span>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="workspace-panel">
        {workspaceSection === "dashboard" && (
          <div className="workspace-card">
            <div className="panel-title">Dashboard</div>
            <div className="stats-grid">
              <div>
                <strong>{repositories.length}</strong>
                <p>Repositories</p>
              </div>
              <div>
                <strong>{reviews.length}</strong>
                <p>Open reviews</p>
              </div>
              <div>
                <strong>
                  {
                    repositories.filter((repo) => repo.state === "All Clear")
                      .length
                  }
                </strong>
                <p>Green repos</p>
              </div>
            </div>
          </div>
        )}

        {workspaceSection === "repositories" && (
          <div className="workspace-card">
            <div className="panel-title">Repositories</div>
            <p>
              Selected repository: <strong>{selectedRepository}</strong>
            </p>
            <p>
              Use the explorer to switch context and inspect active PR load.
            </p>
          </div>
        )}

        {workspaceSection === "active-prs" && (
          <div className="workspace-card">
            <div className="panel-title">Active PR Reviews</div>
            <div className="review-queue">
              {reviews.map((review) => (
                <div key={review.id} className="review-queue-item">
                  <div>
                    <strong>{review.title}</strong>
                    <p>{review.repo}</p>
                  </div>
                  <span className="repo-state">{review.state}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {workspaceSection === "team-settings" && (
          <div className="workspace-card">
            <div className="panel-title">Team Settings</div>
            <div className="settings-stack">
              <label className="setting-row">
                <span>Auto-assign reviewers</span>
                <input type="checkbox" defaultChecked />
              </label>
              <label className="setting-row">
                <span>Show architectural drift alerts</span>
                <input type="checkbox" defaultChecked />
              </label>
              <label className="setting-row">
                <span>Mirror workspace theme</span>
                <input type="checkbox" defaultChecked />
              </label>
            </div>
          </div>
        )}
      </section>

      <section className="canvas-tabs-card">
        <div className="panel-title">Synapse View</div>
        <div className="sub-tabs" aria-label="Canvas tabs">
          {canvasTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`sub-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => onSelectTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
