from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the scope for Google Ads API
SCOPES = ["https://www.googleapis.com/auth/adwords"]

def get_refresh_token():
    # Start the OAuth 2.0 flow
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # Print the refresh token
    print("Access Token:", creds.token)
    print("Refresh Token:", creds.refresh_token)

    # You can save the tokens for later use if needed
    return creds.refresh_token

# Run the function to get the refresh token
refresh_token = get_refresh_token()

# Now, you can use the refresh token to set up the google-ads.yaml file.
print("Your refresh token is:", refresh_token)
