import pandas as pd
import requests
import time
from rdflib import Graph, Literal, RDF, URIRef, Namespace

# Load performers
df = pd.read_csv("performers.csv")

# Extract and clean performer names
performers_raw = df["label"].dropna().unique()
performers = [p.split("|")[0].strip() for p in performers_raw if "|" in p]

# RDF graph
g = Graph()
EX = Namespace("http://example.org/performer/")
g.bind("ex", EX)

print("🔁 Starting SPARQL loop over performer names...\n")

for name in performers:
    print(f"🔎 Fetching data for: {name}")

    # Build enriched SPARQL query
    query = f"""
    SELECT ?person ?description ?birthDate ?occupationLabel ?citizenshipLabel ?website WHERE {{
      ?person rdfs:label "{name}"@en .
      OPTIONAL {{ ?person schema:description ?description . FILTER(LANG(?description) = "en") }}
      OPTIONAL {{ ?person wdt:P569 ?birthDate . }}
      OPTIONAL {{ ?person wdt:P106 ?occupation . }}
      OPTIONAL {{ ?person wdt:P27 ?citizenship . }}
      OPTIONAL {{ ?person wdt:P856 ?website . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 1
    """

    response = requests.get(
        "https://query.wikidata.org/sparql",
        headers={"Accept": "application/sparql-results+json"},
        params={"query": query}
    )

    if response.status_code == 200:
        data = response.json()
        bindings = data.get("results", {}).get("bindings", [])

        if bindings:
            result = bindings[0]
            uri = result["person"]["value"]
            performer_uri = URIRef(uri)

            g.add((performer_uri, RDF.type, EX.Performer))
            g.add((performer_uri, EX.name, Literal(name)))

            if "description" in result:
                g.add((performer_uri, EX.description, Literal(result["description"]["value"])))
            if "birthDate" in result:
                g.add((performer_uri, EX.birthDate, Literal(result["birthDate"]["value"])))
            if "occupationLabel" in result:
                g.add((performer_uri, EX.occupation, Literal(result["occupationLabel"]["value"])))
            if "citizenshipLabel" in result:
                g.add((performer_uri, EX.citizenship, Literal(result["citizenshipLabel"]["value"])))
            if "website" in result:
                g.add((performer_uri, EX.website, URIRef(result["website"]["value"])))

            print(f"✅ Added: {name}\n")
        else:
            print(f"⚠️ No match found for: {name}\n")
    else:
        print(f"❌ SPARQL error for {name}: Status {response.status_code}\n")

    time.sleep(1.5)

# Save RDF
output_file = "performers_enriched.ttl"
g.serialize(destination=output_file, format="turtle")
print(f"✅ RDF file created: {output_file}")