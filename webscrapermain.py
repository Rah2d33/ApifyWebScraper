import requests
import time
import json
from bs4 import BeautifulSoup
import webbrowser

# Your new unique ID
UNIQUE_ID = 'dhZheBwCTR3LmvZJ4dhZheBwCTR3LmvZJ4'

# Apify API Token and POST endpoint
APIFY_API_TOKEN = 'apify_api_CIgyUU674qgx2VBInFuD2FTEdlsgob1S1Hqp'
APIFY_POST_ENDPOINT = f'https://api.apify.com/v2/actor-tasks/rahdee.s~myigactor-task/runs?token={APIFY_API_TOKEN}'

# Instagram Graph API token and base URL (replace with your actual token)
INSTAGRAM_ACCESS_TOKEN = 'YOUR_INSTAGRAM_ACCESS_TOKEN'
INSTAGRAM_GRAPH_URL = 'https://graph.instagram.com/'

# Base URL for Apify Task Runs Page
APIFY_TASK_URL = 'https://console.apify.com/actors/rahdee.s~myigactor-task/runs'

# Function to validate Apify API Token
def validate_apify_token():
    try:
        response = requests.get('https://api.apify.com/v2/actor-tasks', headers={'Authorization': f'Bearer {APIFY_API_TOKEN}'})
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error validating Apify token: {str(e)}")
        return False

# Step 1: Scraping Instagram Profile Using BeautifulSoup
def scrape_instagram_profile(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for bad status codes
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to retrieve Instagram profile. {str(e)}"}

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract bio description (meta description tag)
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    bio_description = meta_tag['content'] if meta_tag else 'No description found'

    return {
        'username': username,
        'bio_description': bio_description,
        'profile_url': url
    }

# Step 2: Fetching Instagram Data Using Graph API
def fetch_instagram_data(user_id):
    url = f"{INSTAGRAM_GRAPH_URL}{user_id}?fields=id,username,media_count,account_type&access_token={INSTAGRAM_ACCESS_TOKEN}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to retrieve Instagram data: {str(e)}"}

# Step 3: Trigger the Apify Task Using a POST Request
def trigger_apify_task(username):
    payload = {
        "input": {
            "username": username,
            "startUrls": []
        }
    }
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(APIFY_POST_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for bad status codes
        run_data = response.json()
        return run_data['data'] if 'data' in run_data else run_data
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to trigger Apify task. {str(e)}"}

# Fetch the Apify task results with a timeout and optimized polling
def get_apify_task_result(run_id, timeout=600):
    result_url = f'https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}'
    start_time = time.time()

    while True:
        try:
            response = requests.get(result_url)
            response.raise_for_status()
            task_result = response.json()

            # Check the status of the task
            status = task_result.get('status')
            if status == 'SUCCEEDED':
                print("Task succeeded, fetching results.")
                return task_result.get('data', {})
            elif status in ['FAILED', 'ABORTED']:
                return {"error": f"Apify task failed with status: {status}"}
            else:
                # Polling interval
                print(f"Task status: {status}. Checking again in 2 seconds...")
                time.sleep(2)  # Decrease interval for faster checks in the early phase

            # Timeout check
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                return {"error": "Timeout exceeded while waiting for Apify task result."}
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch Apify task result. {str(e)}"}


# Step 4: Merging Scraped Data with Apify Results
def get_combined_instagram_data(username):
    # Scrape basic profile details
    scraped_data = scrape_instagram_profile(username)

    # Fetch Instagram user ID if available (you'll need to modify this part to get the user ID)
    user_id = "INSTAGRAM_USER_ID"  # Replace with the actual user ID, if known

    # Fetch Instagram data using Graph API
    instagram_data = fetch_instagram_data(user_id)

    # Trigger the Apify task using POST request
    print(f"Triggering Apify task for username: {username}")
    apify_task = trigger_apify_task(username)

    if "error" in apify_task:
        return apify_task  # Return error if task failed to trigger

    # Fetch Apify task result (polling until completion)
    run_id = apify_task.get('id')
    if not run_id:
        return {"error": "No run ID found for the triggered Apify task"}

    print(f"Fetching Apify task result for run ID: {run_id}")
    apify_result = get_apify_task_result(run_id)

    # Redirect to specific task run page
    specific_run_url = f'https://console.apify.com/actors/rahdee.s~myigactor-task/runs/{run_id}'
    print(f"Redirecting to your specific Apify task run page: {specific_run_url}")
    webbrowser.open(specific_run_url)

    # Combine both sets of data
    combined_data = {
        'scraped_data': scraped_data,
        'apify_data': apify_result,
        'instagram_data': instagram_data
    }

    # Extract the social links if available
    social_links = apify_result.get('socialLinks', [])
    combined_data['social_links'] = social_links

    return combined_data

# Step 5: Example Usage
if __name__ == "__main__":
    if not validate_apify_token():
        print("Invalid Apify API token. Please check your token.")
    else:
        username = input("Enter the Instagram username to search: ").strip()
        combined_data = get_combined_instagram_data(username)

        # Output the combined data
        if combined_data:
            print(json.dumps(combined_data, indent=4))
        else:
            print("No data found or an error occurred.")
