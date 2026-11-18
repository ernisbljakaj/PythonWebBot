import random
import time
from playwright.sync_api import sync_playwright

SEARCH_QUERY = "liss inderkum"
TARGET_DOMAIN = "liss-inderkum.com"
MAX_VISITS = 5  # Zum Testen klein halten, damit Google kein CAPTCHA auslöst

DEVICES = [
    "iPhone 14",
    "Pixel 7",
    "Desktop Chrome",
    "Desktop Firefox",
]

with sync_playwright() as p:
    # headless=False ist bei Google-Suchen wichtig, da Headless-Browser sofort geblockt werden
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
            time.sleep(random.uniform(1.0, 2.0))

            # 2. Google Cookie-Banner wegklicken (falls vorhanden)
            for btn_text in ["Alle akzeptieren", "Alle ablehnen", "Accept all"]:
                btn = page.locator(f"button:has-text('{btn_text}')").first
                if btn.is_visible():
                    btn.click()
                    time.sleep(1)
                    break

            # 3. Suchbegriff wie ein Mensch eintippen und Enter drücken
            search_box = page.locator("textarea[name='q'], input[name='q']").first
            search_box.click()
            search_box.type(SEARCH_QUERY, delay=random.randint(60, 140))
            page.keyboard.press("Enter")

            # Warten, bis die Suchergebnisse geladen sind
            page.wait_for_selector("a", timeout=10000)
            time.sleep(random.uniform(1.5, 3.0))

            # 4. Link zu liss-inderkum.com in den Ergebnissen suchen und anklicken
            target_link = page.locator(f"a[href*='{TARGET_DOMAIN}']").first
            if target_link.is_visible():
                target_link.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                print(
                    f"Besuch {i}/{MAX_VISITS} über Google erfolgreich | Gerät:"
                    f" {device_name}"
                )

                # Kurz auf der Seite verweilen & scrollen
                time.sleep(random.uniform(3.0, 5.0))
                page.mouse.wheel(0, random.randint(200, 500))
                time.sleep(random.uniform(1.0, 2.0))
            else:
                print(
                    f"Besuch {i}/{MAX_VISITS}: Seite nicht auf Seite 1 gefunden"
                    " oder Google-CAPTCHA aktiv."
                )

        except Exception as e:
            print(f"Fehler bei Durchlauf {i}: {e}")

        finally:
            context.close()

        # Längere Pause zwischen den Suchen, um Google-Sperren zu vermeiden
        time.sleep(random.uniform(5.0, 10.0))

    browser.close()