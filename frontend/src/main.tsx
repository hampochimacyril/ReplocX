import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";
import { SelectionProvider } from "./state/selection";
import { ScenarioProvider } from "./state/scenario";
import { CompareProvider } from "./state/compare";
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/app.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

const root = document.getElementById("root");
if (!root) throw new Error("Root element #root not found");

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ScenarioProvider>
          <CompareProvider>
            <SelectionProvider>
              <App />
            </SelectionProvider>
          </CompareProvider>
        </ScenarioProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
