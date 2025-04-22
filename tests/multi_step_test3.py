from playwright.sync_api import sync_playwright

def track_clicks():
    with sync_playwright() as p:
        # Launching browser
        browser = p.chromium.launch(headless=False)  # Set to False to watch the browser in action
        page = browser.new_page()

        # Open the desired URL
        page.goto("https://www.penguinrandomhouse.com/books/536247/devotions-a-read-with-jenna-pick-by-mary-oliver/")

        # Listen for any clicks and log the clicked element's selector
        def log_click(event):
            element = event.target
            try:
                selector = element.get_attribute('outerHTML')  # Get the full HTML of the clicked element
                print(f"Clicked Element: {selector}")
            except Exception as e:
                print(f"Error logging click: {str(e)}")

        # Attach the event listener to log the clicked elements
        page.on("click", log_click)

        # Trigger the Quick View for the first recommendation
        page.click('div#recommendationCarousel .element-wrapper:first-child .quick-view')
        print("Quick View clicked!")

        # Wait for the modal dialog to become visible
        page.wait_for_selector("#single-title-view .modal-dialog.quickview-modal", timeout=30000)

        # Wait a while so you can interact with the page manually too
        print("Tracking actions, please interact with the page...")
        page.wait_for_timeout(60000)  # Wait for 1 minute to track clicks

        # Close the browser once done
        browser.close()

# Run the tracking function
track_clicks()
