import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App.jsx";
import "./index.css";


// Find the HTML element where React will render the application.
const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("React root element was not found.");
}


// Render the application with additional development checks enabled.
createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);