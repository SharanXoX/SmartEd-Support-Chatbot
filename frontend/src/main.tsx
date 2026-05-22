import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import ErrorBoundary from "./components/ErrorBoundary";
import { ChatProvider } from "./context/ChatContext";
import { ActiveUserProvider } from "./context/ActiveUserContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
      <ActiveUserProvider>
        <ChatProvider>
          <App />
        </ChatProvider>
      </ActiveUserProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
);
