from rdflib import Graph, Namespace, RDFS, RDF, Literal, URIRef
from datetime import datetime, timedelta
from train_planner_api import request_trip, calculate_duration
import dateparser
import requests

SCHEMA = Namespace("http://schema.org/")
EX = Namespace("http://example.org/performer/")

g = Graph()
print("📂 Loading RDF data from scraped_delamar_events.ttl...")
g.parse("scraped_delamar_events.ttl", format="turtle")
g_info = Graph()
g_info.parse("performers_enriched.ttl", format="turtle")

def get_show_duration(label, uri):
    durations = list(g.objects(URIRef(uri), SCHEMA.duration))
    if durations:
        text = str(durations[0])
        mins = 0
        if "uur" in text:
            parts = text.split("uur")
            try:
                mins += int(parts[0].strip()) * 60
                if "min" in parts[1]:
                    mins += int(parts[1].split("min")[0].strip())
            except:
                pass
        elif "min" in text:
            try:
                mins += int(text.split("min")[0].strip())
            except:
                pass
        return mins if mins > 0 else 90
    return 90

def fetch_dbpedia_fallback(name):
    url = f"http://dbpedia.org/data/{name.replace(' ', '_')}.json"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return {"description": f"Fallback info from DBpedia: {url}"}
    except:
        pass
    return None

# Parse shows
shows = {}
for s, _, label in g.triples((None, RDFS.label, None)):
    name = str(label).strip()
    if name not in shows:
        shows[name] = {"uri": str(s), "label": name, "dates": []}

    seen = set()
    for _, _, raw_date in g.triples((s, SCHEMA.startDate, None)):
        for line in str(raw_date).split("\n"):
            dt = dateparser.parse(line.strip(), languages=["nl", "en"])
            if dt:
                final_dt = dt.replace(year=2025)
                if final_dt not in seen:
                    seen.add(final_dt)
                    shows[name]["dates"].append({
                        "parsed": final_dt,
                        "raw": line,
                        "url": str(s)
                    })

print("\n🎭 Available Shows:\n")
show_list = list(shows.values())
for i, show in enumerate(show_list, 1):
    print(f"{i}. {show['label']}")
try:
    choice = int(input("\n🎟️ Select a show (number): ")) - 1
    selected_show = show_list[choice]
except:
    print("❌ Invalid input.")
    exit()

print(f"\n🎭 Selected: {selected_show['label']}")

# Enrichment
target = selected_show["label"].split("|")[0].lower().strip()
enriched_data = {}
found = False
for s, _, name in g_info.triples((None, EX.name, None)):
    if isinstance(name, Literal) and target in str(name).lower():
        for pred, obj in g_info.predicate_objects(s):
            if pred != RDF.type:
                enriched_data[pred.split("/")[-1].capitalize()] = str(obj)
        found = True
        break

print("\n🧠 Enriched info:")
if found:
    for k, v in enriched_data.items():
        print(f"• {k}: {v}")
else:
    fallback = fetch_dbpedia_fallback(target)
    if fallback:
        print(f"• {fallback['description']}")
    else:
        print("• No additional info found.")

# Pick date
if not selected_show["dates"]:
    print("❌ No valid dates.")
    exit()

print("\n📅 Performances:")
for i, d in enumerate(selected_show["dates"], 1):
    print(f"{i}. {d['parsed'].strftime('%A %d %B %H:%M')} — {d['url']}")
try:
    date_choice = int(input("\n📅 Select a date (number): ")) - 1
    selected_date = selected_show["dates"][date_choice]
except:
    print("❌ Invalid input.")
    exit()

departure = input("🚉 Enter your departure station: ").strip()
arrival = "Amsterdam Centraal"

start_dt = selected_date["parsed"]
duration_minutes = get_show_duration(selected_show["label"], selected_show["uri"])
show_end = start_dt + timedelta(minutes=duration_minutes)

buffer = input("⏳ Minutes to hang around after the show? (e.g., 15): ").strip()
buffer_minutes = int(buffer) if buffer.isdigit() else 0
show_end_buffered = show_end + timedelta(minutes=buffer_minutes)

print(f"\n📍 Show start: {start_dt.strftime('%H:%M')}")
print(f"📍 Duration: {duration_minutes} min")
print(f"📍 Expected end: {show_end.strftime('%H:%M')}")
print(f"📍 Return trip search starts after: {show_end_buffered.strftime('%H:%M')}")

# OUTGOING TRIP — ARRIVE BEFORE SHOW
out_data = request_trip(
    departure,
    arrival,
    start_dt.strftime("%Y-%m-%d"),
    start_dt.strftime("%H:%M"),
    search_for_departure=False  # searchForArrival = true
)

if out_data and "trips" in out_data:
    print("\n🚆 Outgoing train options:")
    shown = 0
    for trip in out_data["trips"]:
        leg = trip["legs"][0]
        end_leg = trip["legs"][-1]
        dep_time = dateparser.parse(leg["origin"]["plannedDateTime"])
        arr_time = dateparser.parse(end_leg["destination"]["plannedDateTime"])
        
        # Skip trains arriving after the show starts
        if arr_time.replace(tzinfo=None) > start_dt.replace(tzinfo=None):
            continue

        shown += 1
        print(f"\n🔵 Trip {shown}")
        print(f"• From: {leg['origin']['name']} at {dep_time.strftime('%H:%M')}")
        print(f"• To: {end_leg['destination']['name']} at {arr_time.strftime('%H:%M')}")
        print(f"• Duration: {calculate_duration(leg['origin']['plannedDateTime'], end_leg['destination']['plannedDateTime'])}")
        if shown >= 5:
            break

    if shown == 0:
        print("⚠️ No trips found that arrive before the show starts.")
else:
    print("❌ No outgoing trains found.")

# RETURN TRIP — DEPART AFTER SHOW
ret_data = request_trip(
    arrival,
    departure,
    show_end_buffered.strftime("%Y-%m-%d"),
    show_end_buffered.strftime("%H:%M"),
    search_for_departure=True  # searchForDeparture = true
)

if ret_data and "trips" in ret_data:
    print(f"\n🔁 Return trip options (after {show_end_buffered.strftime('%H:%M')}):")
    show_end_naive = show_end_buffered.replace(tzinfo=None)
    shown = 0
    for trip in ret_data["trips"]:
        leg = trip["legs"][0]
        end_leg = trip["legs"][-1]
        dep_time = dateparser.parse(leg["origin"]["plannedDateTime"]).replace(tzinfo=None)
        arr_time = dateparser.parse(end_leg["destination"]["plannedDateTime"]).replace(tzinfo=None)

        if dep_time < show_end_naive:
            continue

        shown += 1
        print(f"\n🔁 Return {shown}")
        print(f"• From: {leg['origin']['name']} at {dep_time.strftime('%H:%M')}")
        print(f"• To: {end_leg['destination']['name']} at {arr_time.strftime('%H:%M')}")
        print(f"• Duration: {calculate_duration(leg['origin']['plannedDateTime'], end_leg['destination']['plannedDateTime'])}")
        if shown >= 5:
            break
    if shown == 0:
        print("⚠️ No return trips found that depart after the show ends.")
else:
    print("❌ No return trip data available.")