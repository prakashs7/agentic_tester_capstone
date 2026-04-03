from pathlib import Path
from playwright.sync_api import sync_playwright, expect, ConsoleMessage

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Collect JavaScript errors (ignore network resolution errors)
        js_errors = []

        def on_console(msg: ConsoleMessage):
            if msg.type == "error" and "net::ERR_NAME_NOT_RESOLVED" not in msg.text:
                js_errors.append(msg.text)

        page.on("console", on_console)

        # ---------- Home Page ----------
        page.goto("https://the-internet.herokuapp.com/")
        expect(page).to_have_title("The Internet")
        # Verify that all example links are reachable (no 404)
        links = page.locator("ul li a")
        link_count = links.count()
        for i in range(link_count):
            href = links.nth(i).get_attribute("href")
            if not href:
                continue
            full_url = page.url.rstrip("/") + "/" + href.lstrip("/")
            response = page.goto(full_url)
            if response is None or response.status != 200:
                raise AssertionError(f"Link {href} returned status {response.status if response else 'None'}")
            # Return to home page for next iteration
            page.goto("https://the-internet.herokuapp.com/")

        # ---------- Checkbox Page ----------
        page.click("a[href='/checkboxes']")
        expect(page).to_have_url("**/checkboxes")
        # Verify at least two checkboxes exist
        checkboxes = page.locator("input[type='checkbox']")
        expect(checkboxes).to_have_count(2)

        # Verify labels for each checkbox
        label1 = page.locator("label", has_text="checkbox 1")
        label2 = page.locator("label", has_text="checkbox 2")
        expect(label1).to_be_visible()
        expect(label2).to_be_visible()

        # Toggle first checkbox and verify state changes
        cb1 = checkboxes.nth(0)
        initial_state = cb1.is_checked()
        cb1.click()
        if initial_state:
            expect(cb1).not_to_be_checked()
        else:
            expect(cb1).to_be_checked()

        # ---------- Form Authentication ----------
        page.goto("https://the-internet.herokuapp.com/login")
        expect(page).to_have_url("**/login")
        # Verify presence of fields and button
        username_input = page.locator("#username")
        password_input = page.locator("#password")
        login_button = page.locator("button[type='submit']")
        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(login_button).to_have_text("Login")

        # Successful login
        username_input.fill("tomsmith")
        password_input.fill("SuperSecretPassword!")
        login_button.click()
        expect(page).to_have_url("**/secure")
        success_msg = page.locator("#flash")
        expect(success_msg).to_contain_text("You logged into a secure area!")

        # Logout to reset state
        page.click("a[href='/logout']")
        expect(page).to_have_url("**/login")

        # Unsuccessful login
        username_input.fill("invalid")
        password_input.fill("wrong")
        login_button.click()
        error_msg = page.locator("#flash")
        expect(error_msg).to_contain_text("Your username is invalid!")

        # ---------- File Upload ----------
        page.goto("https://the-internet.herokuapp.com/upload")
        expect(page).to_have_url("**/upload")
        file_input = page.locator('input[type="file"]')
        upload_button = page.locator('#file-submit')
        expect(file_input).to_be_visible()
        expect(upload_button).to_be_visible()

        # Prepare a temporary file for upload
        temp_file = Path("temp_upload.txt")
        temp_file.write_text("Playwright upload test")
        file_input.set_input_files(str(temp_file))
        upload_button.click()
        # Verify upload success
        uploaded_msg = page.locator("h3")
        expect(uploaded_msg).to_have_text("File Uploaded!")
        uploaded_name = page.locator("#uploaded-files")
        expect(uploaded_name).to_have_text("temp_upload.txt")
        temp_file.unlink()  # Clean up

        # ---------- Usability Checks ----------
        # Discoverability: ensure at least one focusable interactive element exists
        focusable = page.locator("a, button, input, select, textarea")
        expect(focusable).to_have_count(lambda count: count > 0)

        # Visual distinction: verify that buttons have non‑empty accessible name
        buttons = page.locator("button")
        button_count = buttons.count()
        for i in range(button_count):
            btn = buttons.nth(i)
            # Prefer visible text; fallback to aria-label
            text = btn.inner_text().strip()
            aria = btn.get_attribute("aria-label") or ""
            if not text and not aria:
                raise AssertionError("Button without descriptive text or aria-label found")

        # ---------- Console Error Verification ----------
        if js_errors:
            raise AssertionError(f"JavaScript errors detected: {js_errors}")

        # Cleanup
        context.close()
        browser.close()

if __name__ == "__main__":
    run_tests()
