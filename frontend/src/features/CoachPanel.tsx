import { useState } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type Props = {
  intent?: string;
  repository?: string;
};

const promptPresets = [
  "What should I review first?",
  "Summarize the riskiest change in one sentence.",
  "Which file is most likely to cause regressions?",
  "Draft a concise review comment for the author.",
];

export default function CoachPanel({ intent, repository }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    // Add user message
    const newMessages: Message[] = [
      ...messages,
      { role: "user", content: text },
    ];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/coach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          intent,
          repo: repository,
          conversation_history: messages,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get coach response");
      }

      const data = await response.json();
      setMessages([
        ...newMessages,
        { role: "assistant", content: data.response },
      ]);
    } catch (error) {
      console.error("Coach error:", error);
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content:
            "Sorry, I encountered an error. Please try again or analyze a diff first.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handlePresetPrompt = (prompt: string) => {
    handleSendMessage(prompt);
  };

  return (
    <div className="card-panel tab-panel">
      <div className="section-head">
        <div>
          <div className="eyebrow">Interactive AI Coach</div>
          <h2>Review assistant</h2>
        </div>
        <span className="repo-chip">
          {repository || "No repository selected"}
        </span>
      </div>

      <p className="coach-intro">
        Use the coach to frame the review, explain the intent, and prepare
        follow-up questions for the author or the team.
      </p>

      {messages.length === 0 ? (
        <>
          <div className="coach-panel">
            <strong>Current intent</strong>
            <p>
              {intent || "Analyze a diff first to populate the intent summary."}
            </p>
          </div>

          <div>
            <strong>Suggested prompts</strong>
            <div className="prompt-grid">
              {promptPresets.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="prompt-chip"
                  onClick={() => handlePresetPrompt(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="chat-container">
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.role}`}>
                <div className="message-label">
                  {msg.role === "user" ? "You" : "Coach"}
                </div>
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="chat-message assistant">
                <div className="message-label">Coach</div>
                <div className="message-content loading">
                  <span className="dot" />
                  <span className="dot" />
                  <span className="dot" />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="coach-input-area">
        <input
          type="text"
          placeholder="Ask the coach anything..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !loading) {
              handleSendMessage(input);
            }
          }}
          disabled={loading}
          className="coach-input"
        />
        <button
          type="button"
          className="coach-send"
          onClick={() => handleSendMessage(input)}
          disabled={!input.trim() || loading}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
