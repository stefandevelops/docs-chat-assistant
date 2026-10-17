#!/usr/bin/env python3
"""Drive the Streamlit UI and save screenshots for the README."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ARTIFACTS = Path("/opt/cursor/artifacts")
URL = "http://127.0.0.1:8501"


def save(page, name: str) -> Path:
    DOCS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    dest = DOCS / name
    page.screenshot(path=str(dest), full_page=False)
    extra = ARTIFACTS / name
    extra.write_bytes(dest.read_bytes())
    print(f"wrote {dest}")
    return dest


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--window-size=1440,900"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(URL, wait_until="domcontentloaded")
        page.get_by_text("Chat with the VoltPath help centre").wait_for(timeout=30000)
        page.wait_for_timeout(1500)
        save(page, "ui-home.png")

        page.get_by_role("button", name="How many days do customers have to return a bike?").click()
        page.get_by_text("30 days from the delivery date").first.wait_for(timeout=20000)
        page.get_by_text("01-returns-policy.md").first.wait_for(timeout=10000)
        page.wait_for_timeout(1200)
        save(page, "ui-chat.png")

        box = page.locator("[data-testid='stChatInput'] textarea, textarea").last
        box.click()
        box.fill("What is the CEO's salary?")
        box.press("Enter")
        page.get_by_text("I don't know").wait_for(timeout=20000)
        page.wait_for_timeout(1200)
        save(page, "ui-abstain.png")
        browser.close()


if __name__ == "__main__":
    main()
