from playwright.sync_api import sync_playwright, Page, expect

def take_test(page: Page, answers_to_give: dict):
    """Helper function to take the test with a specific set of answers."""
    expect(page.get_by_role("heading", name="Tes Minat Bakat Holland")).to_be_visible(timeout=30000)

    # Answer the questions
    for q_id, answer_index in answers_to_give.items():
        page.locator(f'input[type="radio"][key="q_{q_id}"]').nth(answer_index - 1).check()

    page.get_by_role("button", name="Selesaikan & Lihat Hasil").click()
    expect(page.get_by_text("Tes berhasil diselesaikan!")).to_be_visible(timeout=30000)

def run_verification(page: Page):
    """
    Verifies that a student can take the test multiple times and view the history.
    """
    # 1. Login as student
    page.goto("http://localhost:8501", timeout=60000)
    expect(page.get_by_role("heading", name="Sistem Tes Minat Bakat Siswa")).to_be_visible(timeout=30000)
    page.get_by_label("Nama Pengguna").fill("student1")
    page.get_by_label("Kata Sandi").fill("student123")
    page.get_by_role("button", name="Masuk").click()

    # 2. Take the test for the first time
    expect(page.get_by_role("heading", name="👋 Selamat Datang, Siswa Contoh")).to_be_visible(timeout=30000)
    page.get_by_role("link", name="Mulai Tes").click()
    take_test(page, {1: 5, 2: 5, 4: 5, 5: 5, 10: 5, 12: 5}) # Realistic/Investigative focus

    # 3. Go back and take the test a second time with different answers
    page.get_by_role("button", name="Ambil Tes Lagi").click()
    take_test(page, {7: 5, 8: 5, 10: 5, 11: 5, 13: 5, 14: 5}) # Artistic/Social focus

    # 4. Navigate to the results page to see the history
    page.get_by_role("button", name="Lihat Semua Riwayat Tes").click()
    expect(page.get_by_role("heading", name="Hasil Tes Minat Bakat")).to_be_visible(timeout=30000)

    # 5. Verify that there are two test results
    expect(page.get_by_text("Anda telah menyelesaikan tes sebanyak 2 kali.")).to_be_visible()
    expect(page.locator("div[data-testid='stExpander']")).to_have_count(2)

    # 6. Screenshot the result
    page.screenshot(path="jules-scratch/verification/student_history_verification.png")
    print("Screenshot saved to jules-scratch/verification/student_history_verification.png")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run_verification(page)
        browser.close()

if __name__ == "__main__":
    main()