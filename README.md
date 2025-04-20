# DataScienceProject-LOD
# NS Show Trip Planner (Linked Open Data Project)

This project helps users discover upcoming performances at the DeLaMar Theatre in Amsterdam and plan their train trips to and from the show using real-time data from the NS Reisinformatie API.

It combines:
- Web scraping
- RDF + Linked Open Data modeling
- Live SPARQL queries to Wikidata
- NS train planning API
- Command-line interaction

====================
       SETUP
====================

1. Install Dependencies

Make sure Python 3.7+ is installed.

Install required packages:

    pip install rdflib SPARQLWrapper requests

--------------------

2. Set up the NS API Key

- Go to https://developer.ns.nl
- Register, create an app, copy your API key

This project uses real-time train data from the NS Reisinformatie API.

A personal API key is included in the submitted version of this project.
Normally, this key would be considered private.
However, because registering for the API can be confusing or unavailable at times, I’ve chosen to leave my personal key in the code to ensure the project runs smoothly for reviewers.

How to get an API key
1. Visit: https://developer.ns.nl
2. Click Login, then scroll down to click "Nog geen account? Registreren". This option may not always appear, as the NS platform has recently changed.
3. After logging in, go to Dashboard → My Apps
4. Click “Nieuwe App” (New App)
5. Choose "NS Reisinformatie API"
6. After saving, your personal API key will appear in your app details or under your profile


--------------------

3. Generate RDF Data

The project needs:
- scraped_delamar_events.ttl
- performers_enriched.ttl


Rebuild from scratch:

    python scrape_to_rdf_complete.py
    python loop_sparql_dbpedia.py

This creates:
- scraped_delamar_events.ttl (with show info)
- performers.csv (intermediate list of names)
- performers_enriched.ttl (from Wikidata)

--------------------

4. Run the CLI app

    python show_trip_planner.py

You’ll be prompted to:
- Choose a show
- Pick a date
- Enter your departure station
- Define how long to stay after

And you’ll get:
- Trains that arrive before the show
- Trains that depart after the show ends

====================
   EXAMPLE OUTPUT
====================

🎭 Selected: De Gorgels | Naar het kinderboek van Jochem Myjer | DeLaMar  
📅 Date: Saturday 10 May, 13:00  
⏱ Duration: 75 min  
⏳ Return search starts at: 14:30  

🚆 Outgoing trains:
- 11:39 → 12:05
- 11:52 → 12:18

🔁 Return trains:
- 14:35 → 15:04
- 14:54 → 15:21

====================
   FILE OVERVIEW
====================

- show_trip_planner.py — main CLI interface
- train_planner_api.py — talks to NS API
- scrape_to_rdf_complete.py — scrapes show + performer data
- loop_sparql_dbpedia.py — enriches performer info from Wikidata
- scraped_delamar_events.ttl — RDF with shows
- performers.csv — extracted performer names
- performers_enriched.ttl — RDF with bios, dates, etc.

====================
    DATA SOURCES
====================

- delamar.nl — for show listings
- wikidata.org — for performer info via SPARQL
- developer.ns.nl — NS live train travel data


