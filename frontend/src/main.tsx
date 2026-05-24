import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
console.log("[main] module loaded");
console.log("[main] unique-build-id: 20260519-001");
try {
  const rootEl = document.getElementById("root")!;
  if (!rootEl) console.error("[main] #root not found");
  else {
    console.log("[main] creating root");
    createRoot(rootEl).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
    console.log("[main] render called");
  }
} catch (err) {
  console.error("[main] render error", err);
}
