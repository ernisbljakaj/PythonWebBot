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
    """Pausiert das Skript, solange ein Google-CAPTCHA aktiv ist."""
    time.sleep(1.5)
    is_sorry = "google.com/sorry" in page.url or "google.ch/sorry" in page.url
    has_captcha = page.locator("iframe[src*='recaptcha']").count() > 0

    if is_sorry or has_captcha:
        print("\a⚠️ CAPTCHA erkannt! Bitte im Browser lösen...")
        # Wartet bis zu 5 Minuten, bis Google auf die Suchergebnisse weiterleitet
        page.wait_for_function(
            """() => {
                const urlOk = !window.location.href.includes('/sorry/');
                const frame = document.querySelector("iframe[src*='recaptcha']");
                const frameGone = !frame || frame.offsetParent === null;
                return urlOk && frameGone;
            }""",
            timeout=300000,
        )
        print("✅ CAPTCHA gelöst! Lade Suchergebnisse...")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)


with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    for i in range(1, MAX_VISITS + 1):
        device_name = random.choice(DEVICES)
        print(f"\n--- Durchlauf {i}/{MAX_VISITS} | Gerät: {device_name} ---")

        context = browser.new_context(
            **p.devices[device_name],
            locale="de-CH",
            timezone_id="Europe/Zurich",
        )
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

            # 2. Cookie-Banner wegklicken (falls vorhanden)
            for btn_text in ["Alle akzeptieren", "Alle ablehnen", "Accept all"]:
                btn = page.locator(f"button:has-text('{btn_text}'):visible").first
                if btn.count() > 0:
                    btn.click()
                    time.sleep(1)
                    break

            # 3. Suchbegriff eingeben und Enter drücken
            search_box = page.locator("textarea[name='q']:visible, input[name='q']:visible").first
            search_box.click()
            search_box.type(SEARCH_QUERY, delay=random.randint(60, 140))
            page.keyboard.press("Enter")

            # 4. Prüfen, ob nach der Suche ein CAPTCHA kommt & warten bis gelöst
            handle_captcha(page)

            # 5. Auf sichtbaren Suchergebnis-Link warten
            visible_link_selector = f"#search a[href*='{TARGET_DOMAIN}']:visible, #rso a[href*='{TARGET_DOMAIN}']:visible"
            page.wait_for_selector(visible_link_selector, timeout=20000)
            time.sleep(random.uniform(1.0, 2.0))

            target_link = page.locator(visible_link_selector).first
            target_link.scroll_into_view_if_needed()
            
            # Klick ausführen (mit Fallback, falls Google-Overlay den Klick abfängt)
            try:
                target_link.click(timeout=5000)
            except Exception:
                href = target_link.get_attribute("href")
                if href:
                    page.goto(href, wait_until="domcontentloaded")

            # Warten, bis die Zielseite wirklich geladen ist
            page.wait_for_url(f"**/*{TARGET_DOMAIN}*", timeout=20000)
            print(f"🌐 Erfolgreich auf {page.url} gelandet!")

            # 6. Auf der Webseite verweilen & scrollen
            time.sleep(random.uniform(3.0, 5.0))
            page.mouse.wheel(0, random.randint(250, 600))
            time.sleep(random.uniform(1.5, 3.0))

        except Exception as e:
            print(f"❌ Fehler bei Durchlauf {i} ({device_name}): {e}")

        finally:
            context.close()

        if i < MAX_VISITS:
            pause = random.uniform(4.0, 8.0)
            print(f"Nächstes Gerät in {pause:.1f}s...")
            time.sleep(pause)

    browser.close()
    print("\nFertig!")