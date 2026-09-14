import threeca

r = threeca.refresh_catalog()
print("Categories:", len(r["categories"]))
for c in r["categories"]:
    print("  " + c["name"] + ": " + str(c["reported_studies"]) + " studies")

# Search for studies with 'metabolic' in title
print("\nSearching for metabolic studies...")
for s in r["studies"]:
    if "metabolic" in s["title"].lower() or "metabolism" in s["title"].lower():
        print(s["id"], s["title"], s["category"])

# Search for studies with 'metabolic' in description
print("\nSearching for metabolic in description...")
for s in r["studies"]:
    if "metabolic" in s.get("description", "").lower() or "metabolism" in s.get("description", "").lower():
        print(s["id"], s["title"], s["category"])
