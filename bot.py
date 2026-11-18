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


def handle_captcha(page):
    """Erkennt ein Google-CAPTCHA und pausiert, bis es manuell gelöst wurde."""
    is_sorry_url = "google.com/sorry" in page.url or "google.ch/sorry" in page.url
    has_recaptcha = page.locator("iframe[src*='recaptcha']").count() > 0

    if is_sorry_url or has_recaptcha:
        print("⚠️ CAPTCHA erkannt! Bitte löse es im Browserfenster...")
        # Wartet bis zu 5 Minuten, bis weder '/sorry/' in der URL ist noch ein reCAPTCHA sichtbar ist
        page.wait_for_function(
            """() => {
                const urlOk = !window.location.href.includes('/sorry/');
                const captchaFrame = document.querySelector("iframe[src*='recaptcha']");
                const frameHidden = !captchaFrame || captchaFrame.offsetParent === null;
                return urlOk && frameHidden;
            }""",
            timeout=300000,
        )
        print("✅ CAPTCHA gelöst! Warte kurz auf Weiterleitung...")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)


with sync_playwright() as p:
    # Browser mit leicht reduzierter Bot-Erkennung starten
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    for i in range(1, MAX_VISITS + 1):
        device_name = random.choice(DEVICES)
        print(f"\n--- Starte Durchlauf {i}/{MAX_VISITS} mit Gerät: {device_name} ---")

        context = browser.new_context(
            **p.devices[device_name],
            locale="de-CH",
            timezone_id="Europe/Zurich",
        )
        # Entfernt das 'navigator.webdriver'-Flag für weniger CAPTCHAs
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()

        try:
            # 1. Google öffnen
            page.goto(
                "https://www.google.ch/",
                wait_until="domcontentloaded",
                timeout=20000,
            )
            handle_captcha(page)
            time.sleep(random.uniform(1.0, 2.0))

            # 2. Cookie-Banner wegklicken (falls vorhanden)
            for btn_text in ["Alle akzeptieren", "Alle ablehnen", "Accept all"]:
                btn = page.locator(f"button:has-text('{btn_text}')").first
                if btn.is_visible():
                    btn.click()
                    time.sleep(1)
                    break

            # 3. Suchbegriff eintippen und absenden
            search_box = page.locator("textarea[name='q'], input[name='q']").first
            search_box.wait_for(state="visible", timeout=10000)
            search_box.click()
            search_box.type(SEARCH_QUERY, delay=random.randint(60, 140))
            page.keyboard.press("Enter")

            # Kurz warten und prüfen, ob nach der Suche das CAPTCHA kommt
            time.sleep(2)
            handle_captcha(page)

            # 4. Auf Suchergebnisse warten und Ziel-Link anklicken
            target_selector = f"a[href*='{TARGET_DOMAIN}']"
            page.wait_for_selector(target_selector, state="visible", timeout=20000)
            time.sleep(random.uniform(1.0, 2.0))

            target_link = page.locator(target_selector).first
            target_link.scroll_into_view_if_needed()
            target_link.click()

            # Warten, bis liss-inderkum.com geladen ist
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            print(f"✅ Besuch {i}/{MAX_VISITS} erfolgreich | Gerät: {device_name}")

            # 5. Auf der Webseite verweilen & scrollen
            time.sleep(random.uniform(3.0, 5.0))
            page.mouse.wheel(0, random.randint(250, 600))
            time.sleep(random.uniform(1.5, 3.0))

        except Exception as e:
            print(f"❌ Fehler bei Durchlauf {i} ({device_name}): {e}")

        finally:
            # Kontext erst schließen, nachdem die Seite besucht wurde (oder bei Fehler)
            context.close()

        if i < MAX_VISITS:
            pause = random.uniform(4.0, 8.0)
            print(f"Warte {pause:.1f}s vor dem nächsten Gerät...")
            time.sleep(pause)

    browser.close()
    print("\nAlle Durchläufe abgeschlossen.")