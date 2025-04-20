import requests
import datetime
import json

# Function to calculate duration in hours and minutes
def calculate_duration(dep_time, arr_time):
    fmt = "%Y-%m-%dT%H:%M:%S%z"
    dep = datetime.datetime.strptime(dep_time, fmt)
    arr = datetime.datetime.strptime(arr_time, fmt)
    duration = arr - dep
    minutes = duration.total_seconds() // 60
    return f"{int(minutes // 60)}h {int(minutes % 60)}m"

# NS API request function
def request_trip(departure, arrival, travel_date, departure_time, search_for_departure=True):
    url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips"
    headers = {
        "Ocp-Apim-Subscription-Key": "Personal-API-Key"
    }

    params = {
        "fromStation": departure,
        "toStation": arrival,
        "dateTime": f"{travel_date}T{departure_time}:00"
    }

    # ✅ Set correct mode explicitly
    if search_for_departure:
        params["searchForDeparture"] = "true"
    else:
        params["searchForArrival"] = "true"

    print("🔄 Requesting trip from NS API...")
    print(f"🌐 URL: {url}")
    response = requests.get(url, headers=headers, params=params)
    print(f"📶 Status: {response.status_code}")

    if response.status_code == 200:
        print("✅ Trip data received!")
        return response.json()
    else:
        print("❌ Failed to retrieve data:", response.text)
        return None

# Main function 
def main():
    print("🔵 NS Train Planner API Test")
    departure = input("Enter your departure station: ")
    arrival = "Amsterdam Centraal"
    date = input("Enter travel date (YYYY-MM-DD): ")
    dep_time = input("Enter desired departure time (HH:MM): ")

    data = request_trip(departure, arrival, date, dep_time)

    if data and "trips" in data:
        trips = data["trips"]
        for i, trip in enumerate(trips[:5], 1):
            first_leg = trip["legs"][0]
            last_leg = trip["legs"][-1]
            dep_time = first_leg["origin"]["plannedDateTime"]
            arr_time = last_leg["destination"]["plannedDateTime"]
            duration = calculate_duration(dep_time, arr_time)

            print(f"\n🔵 Trip {i}")
            print(f"• From: {first_leg['origin']['name']}")
            print(f"• Departure: {dep_time[11:16]}")
            print(f"• To: {last_leg['destination']['name']}")
            print(f"• Arrival: {arr_time[11:16]}")
            print(f"• Duration: {duration}")
            print("-" * 30)
    else:
        print("❌ No trip data found.")

# Run the script directly
if __name__ == "__main__":
    main()
