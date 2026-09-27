# Content-Creator Tracker
Tracks the growth (increase in number of subscribers, views and likes) of the latest videos of five different content creators 

## How it works?
- Finds each content creator's channel by their YouTube Handle 
- Obtains subscriber count, total channel views 
- From the most recently uploaded video on their channel, obtains the views and likes 
- Compare the numbers from this run to last run 
- Logs data into a csv file 'snapshot.csv'
- Tracks growth and logs it in 'growth.csv'

Note: A YouTube Data API key is required to run this code. To obtain this create a project in Google cloud console and generate the API key. Copy the .env.example to a .env file and add your key there then run the code.

## Setup & Usage
```bash
pip install -r requirements.txt
python fetch_latest.py
```
Prints a summary for each creator to the terminal 
Appends a row to snapshot.csv after each run
Sppends a row to growth.csv after the second run (first run sets baseline for comparison)

## Files
| File | Purpose |
|---|---|
| `fetch_latest.py` | Main script |
| `.env` | API key not committed, see `.gitignore` |
| `.env.example` | Template showing what `.env` should contain |
| `requirements.txt` | Dependencies |
| `snapshots.csv` | Raw stats history (generated after each run) |
| `growth.csv` | calculated change|

## Built with
- `requests` HTTP calls to the YouTube Data API
- `python-dotenv` loads the API key from `.env`
- Python's built-in `csv` module for logging