# keyword-market-research-tool
Search Volume, Competition for list of keywords on Google Search Engine

Install Requirements.txt using pip

Replace the KEYWORD_FILE and CUSTOMER_ID with your own in new_key_vol.py 
KEYWORD_FILE - A file with new line seperated keyword phrases

client_secret.json - Download from google cloud console

google-ads.yaml - Follow this and create all the required config details required:

You should have a googleads.yaml file that came with team-specific credentials. If you didn't there are instructions to follow here: 
https://developers.google.com/adwords/api/docs/guides/first-api-call

You can use get_ads.py to retreive your Refresh Token required for google-ads.yaml:
```
python get_ads.py
```

Run: 
```
python new_key_vol.py
```
