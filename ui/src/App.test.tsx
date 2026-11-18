import { render, screen } from "@testing-library/react";
import { App } from "./App";
import tokensCss from "./tokens/tokens.css?raw";

const root = document.documentElement;

beforeEach(() => {
  localStorage.clear();
  root.removeAttribute("data-theme");
});

test("App renders the product name", () => {
  render(<App />);
  expect(screen.getByText("Exaktiv")).toBeTruthy();
});

test("theme defaults to dark", () => {
  render(<App />);
  expect(root.dataset.theme).toBe("dark");
});

test("a stored light theme is used", () => {
  localStorage.setItem("exaktiv.theme", "light");
  render(<App />);
  expect(root.dataset.theme).toBe("light");
});

test("an unknown stored theme falls back to dark", () => {
  localStorage.setItem("exaktiv.theme", "purple");
  render(<App />);
  expect(root.dataset.theme).toBe("dark");
});

test("a throwing localStorage falls back to dark", () => {
  const spy = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
    throw new Error("blocked");
  });
  render(<App />);
  expect(root.dataset.theme).toBe("dark");
  spy.mockRestore();
});

// jsdom resolves the --ex-ground custom property for the active theme (probed 18 Nov 2026).
// It does not follow var() chains, so the test compares the unresolved values.
test("data-theme changes --ex-ground on the root", () => {
  const style = document.createElement("style");
  style.textContent = tokensCss;
  document.head.appendChild(style);
  const ground = () => getComputedStyle(root).getPropertyValue("--ex-ground").trim();
  root.dataset.theme = "dark";
  const darkGround = ground();
  root.dataset.theme = "light";
  const lightGround = ground();
  expect(darkGround).not.toBe("");
  expect(lightGround).not.toBe("");
  expect(darkGround).not.toBe(lightGround);
  style.remove();
});
