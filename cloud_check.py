from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Cloud provider status page URLs
cloud_status_pages = {
    "AWS": "https://health.aws.amazon.com/health/status",
    "Google Cloud": "https://status.cloud.google.com/",
    "Azure": "https://status.azure.com/"
}

# Initialize Selenium with Chrome in headless mode
def init_headless_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("window-size=1920,1080")
    
    # Path to ChromeDriver executable
    chrome_service = Service('/Users/lukesheppard/Downloads/chromedriver-mac-arm64/chromedriver')
    
    # Return a new browser session
    return webdriver.Chrome(service=chrome_service, options=chrome_options)

def check_cloud_status(provider, url, browser):
    """Load the status page and retrieve specific elements."""
    try:
        browser.get(url)
        time.sleep(5)  # Give it a few seconds to fully load the page
        
        # AWS check
        if provider == "AWS" and "No recent issues" in browser.find_element(By.TAG_NAME, "body").text:
            return "no issues"

        # Google Cloud check
        elif provider == "Google Cloud":
            try:
                total_services = browser.find_elements(By.CSS_SELECTOR, "svg.psd__status-icon")
                green_checkmarks = browser.find_elements(By.CSS_SELECTOR, "svg.psd__status-icon.psd__available")
                warning_icons = browser.find_elements(By.CSS_SELECTOR, "svg.psd__status-icon.psd__warning")
                
                if not total_services:
                    return "unable to determine status"
                
                percentage_available = len(green_checkmarks) / len(total_services) * 100
                percentage_warning = len(warning_icons) / len(total_services) * 100
                
                # Set a threshold for warnings (e.g., 1%)
                warning_threshold = 1.0
                
                if percentage_available == 100:
                    return "no issues"
                elif percentage_warning > warning_threshold:
                    return f"warning: {percentage_warning:.1f}% services with warnings, {percentage_available:.1f}% fully available"
                elif percentage_available >= 99:  # Adjusted from 90 to 99
                    # return "no significant issues"
                    return "no issues"
                else:
                    return f"issues detected: only {percentage_available:.1f}% services fully available"
            except Exception as e:
                return f"unreachable: {str(e)}"

        # Azure check
        elif provider == "Azure" and "There are currently no active events" in browser.find_element(By.TAG_NAME, "body").text:
            return "no issues"
        
        return "issues detected"
    
    except Exception as e:
        return f"unreachable: {str(e)}"

if __name__ == "__main__":
    # Start the browser in headless mode
    browser = init_headless_browser()

    reachable_providers = []
    unreachable_providers = []
    issues_detected = []

    for provider, url in cloud_status_pages.items():
        result = check_cloud_status(provider, url, browser)
        if "no issues" in result:
            reachable_providers.append(provider)
        elif "unreachable" in result:
            unreachable_providers.append((provider, result))
        else:
            issues_detected.append((provider, result))  # Store both provider and result

    # Clean up
    browser.quit()

    print("Reachable Cloud Providers:")
    for provider in reachable_providers:
        print(f"- {provider}")
    


    if len(reachable_providers) == len(cloud_status_pages):
        print("All cloud providers are reachable.")

    print("Cloud Providers with No Issues:")
    for provider in reachable_providers:
        print(f"- {provider}")
    for provider, status in issues_detected:
        if "no significant issues" in status:
            print(f"- {provider}")

    if len(issues_detected) > 0:
        no_significant_issues = False
        issues_to_report = []

        for provider, status in issues_detected:
            if provider == "Google Cloud" and "no significant issues" in status:
                no_significant_issues = True
                break

        if not no_significant_issues and issues_to_report:
            print("\nCloud Providers with Detected Issues:")
            for provider, status in issues_to_report:
                print(f"- {provider}: {status}")


    if len(unreachable_providers) > 0:
        print("\nUnreachable Cloud Providers:")
        for provider, error in unreachable_providers:
            print(f"- {provider}: {error}")
