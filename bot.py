import random
import time
from playwright.sync_api import sync_playwright

SEARCH_QUERY = "liss inderkum"
TARGET_DOMAIN = "liss-inderkum.com"
MAX_VISITS = 5

DEVICES = [
    "iPhone 14",
    "Pixel 7",
    "Desktop Chrome",
    "Desktop Firefox",
]


def wait_for_captcha(page):
    """Prüft, ob Google ein CAPTCHA anzeigt, und wartet auf manuelle Lösung."""
    if (
        "google.com/sorry" in page.url
        or "google.ch/sorry" in page.url
        or page.locator("iframe[src*='recaptcha']").count() > 0
    ):
        print(
            "⚠️ CAPTCHA erkannt! Bitte löse es im Browserfenster. Das Skript"
            " wartet automatisch..."
        )
        # Wartet bis zu 5 Minuten (300000 ms), bis die URL nicht mehr '/sorry/' enthält
        page.wait_for_url(
            lambda url: "/sorry/" not in url,
            timeout=300000,
        )
        print("✅ CAPTCHA gelöst! Mache weiter...")
        time.sleep(2)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    for i in range(1, MAX_VISITS + 1):
        device_name = random.choice(DEVICES)
        context = browser.new_context(
            **p.devices[device_name],
            locale="de-CH",
            timezone_id="Europe/Zurich",
        )
        page = context.new_page()

        try:
            # 1. Google öffnen
            page.goto(
                "https://www.google.ch/",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            wait_for_captcha(page)
            time.sleep(random.uniform(1.0, 2.0))

            # 2. Google Cookie-Banner wegklicken (falls vorhanden)
            for btn_text in ["Alle akzeptieren", "Alle ablehnen", "Accept all"]:
                btn = page.locator(f"button:has-text('{btn_text}')").first
                if btn.is_visible():
                    btn.click()
                    time.sleep(1)
                    break

            # 3. Suchbegriff eintippen und Enter drücken
            search_box = page.locator("textarea[name='q'], input[name='q']").first
            search_box.click()
            search_box.type(SEARCH_QUERY, delay=random.randint(60, 140))
            page.keyboard.press("Enter")

            # Kurz warten und prüfen, ob nach dem Absenden ein CAPTCHA erscheint
            time.sleep(2)
            wait_for_captcha(page)

            # Warten, bis die Suchergebnisse geladen sind
            page.wait_for_selector(f"a[href*='{TARGET_DOMAIN}']", timeout=15000)
            time.sleep(random.uniform(1.0, 2.5))

            # 4. Link anklicken
            target_link = page.locator(f"a[href*='{TARGET_DOMAIN}']").first
            if target_link.is_visible():
                target_link.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                print(
                    f"Besuch {i}/{MAX_VISITS} über Google erfolgreich | Gerät:"
                    f" {device_name}"
                )

                # Auf der Seite verweilen & scrollen
                time.sleep(random.uniform(3.0, 5.0))
                page.mouse.wheel(0, random.randint(200, 500))
                time.sleep(random.uniform(1.0, 2.0))
            else:
                print(
                    f"Besuch {i}/{MAX_VISITS}: Link auf Seite 1 nicht sichtbar."
                )

        except Exception as e:
            print(f"Fehler bei Durchlauf {i}: {e}")

        finally:
            context.close()

        time.sleep(random.uniform(4.0, 8.0))

    browser.close()