import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Fonts load from /fonts/fonts.css (link in index.html), before these two files.
import "./tokens/tokens.css";
import "./styles/exaktiv.css";
import { App } from "./App";

const root = document.getElementById("root");
if (root === null) throw new Error("root element missing");
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
