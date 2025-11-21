import argparse
import json
import os
from datetime import datetime

# =========================
# 1️⃣ Parse command-line arguments
# =========================
def parse_arguments():
    parser = argparse.ArgumentParser(description="Flight Schedule Parser")
    parser.add_argument("-i", "--input", help="Parse a single CSV file")
    parser.add_argument("-d", "--dir", help="Parse all CSV files in a folder")
    parser.add_argument("-o", "--output", help="Custom output JSON path")
    parser.add_argument("-j", "--jsondb", help="Load existing JSON database")
    parser.add_argument("-q", "--query", help="Execute queries from JSON file")
    return parser.parse_args()


# =========================
# 2️⃣ Parse CSV file and validate rows
# =========================
def parse_csv_file(path):
    valid_flights = []
    errors = []

    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            original = line.strip()
            if not original:
                continue
            if original.startswith("#"):
                errors.append((line_number, original, "comment line, ignored for data parsing"))
                continue
            parts = [p.strip() for p in original.split(",")]
            ok, result = validate_row(parts)
            if ok:
                valid_flights.append(result)
            else:
                errors.append((line_number, original, result))
    return valid_flights, errors


# =========================
# 3️⃣ Parse folder of CSV files
# =========================
def parse_csv_folder(folder_path):
    all_valid = []
    all_errors = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".csv"):
            path = os.path.join(folder_path, filename)
            print("Parsing:", path)
            valid, errors = parse_csv_file(path)
            all_valid.extend(valid)
            all_errors.extend(errors)
    return all_valid, all_errors


# =========================
# 4️⃣ Save errors to errors.txt
# =========================
def save_errors(errors, output_path="output/errors.txt"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for line, content, message in errors:
            f.write(f"Line {line}: {content} → {message}\n")


# =========================
# 5️⃣ Save valid flights to db.json
# =========================
def save_to_json(data, output_path="output/db.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =========================
# 6️⃣ Validate a CSV row
# =========================
def validate_row(parts):
    if len(parts) != 6:
        return False, "missing required fields"

    flight_id, origin, destination, dep_dt, arr_dt, price = parts
    errors = []

    if not (2 <= len(flight_id) <= 8) or not flight_id.isalnum():
        errors.append("invalid flight_id")

    for code, name in [(origin, "origin"), (destination, "destination")]:
        if len(code) != 3 or not code.isupper():
            errors.append(f"invalid {name} code")

    try:
        dep = datetime.strptime(dep_dt, "%Y-%m-%d %H:%M")
    except:
        errors.append("invalid departure datetime")
        dep = None
    try:
        arr = datetime.strptime(arr_dt, "%Y-%m-%d %H:%M")
    except:
        errors.append("invalid arrival datetime")
        arr = None
    if dep and arr and arr <= dep:
        errors.append("arrival before departure")

    try:
        price_val = float(price)
        if price_val <= 0:
            errors.append("negative price value")
    except:
        errors.append("invalid price")

    if errors:
        return False, ", ".join(errors)

    return True, {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": dep_dt,
        "arrival_datetime": arr_dt,
        "price": float(price)
    }


# =========================
# 7️⃣ Execute queries
# =========================
def execute_queries(database, query_file, student_id, name, lastname):
    with open(query_file, "r", encoding="utf-8") as f:
        queries = json.load(f)
    if isinstance(queries, dict):
        queries = [queries]

    responses = []

    for q in queries:
        matches = []
        for flight in database:
            ok = True
            for key in ["flight_id", "origin", "destination"]:
                if key in q and flight.get(key) != q[key]:
                    ok = False
            if "departure_datetime" in q:
                q_dep = datetime.strptime(q["departure_datetime"], "%Y-%m-%d %H:%M")
                f_dep = datetime.strptime(flight["departure_datetime"], "%Y-%m-%d %H:%M")
                if f_dep < q_dep:
                    ok = False
            if "arrival_datetime" in q:
                q_arr = datetime.strptime(q["arrival_datetime"], "%Y-%m-%d %H:%M")
                f_arr = datetime.strptime(flight["arrival_datetime"], "%Y-%m-%d %H:%M")
                if f_arr > q_arr:
                    ok = False
            if "price" in q:
                if flight["price"] > float(q["price"]):
                    ok = False
            if ok:
                matches.append(flight)
        responses.append({
            "query": q,
            "matches": matches
        })

    now_str = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = f"response_{student_id}_{name}_{lastname}_{now_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=2)

    print("Saved query response to:", output_file)


# =========================
# 8️⃣ Main function
# =========================
def main():
    args = parse_arguments()

    # Load existing JSON database
    if args.jsondb:
        with open(args.jsondb, "r", encoding="utf-8") as f:
            database = json.load(f)
        print("Loaded existing JSON database:", args.jsondb)

        if args.query:
            student_id = "123456"   # <-- replace with your student ID
            name = "John"           # <-- replace with your first name
            lastname = "Doe"        # <-- replace with your last name
            execute_queries(database, args.query, student_id, name, lastname)
        return

    # Parse single CSV
    if args.input:
        print("Parsing CSV file:", args.input)
        valid, errors = parse_csv_file(args.input)
        output_path = args.output or "output/db.json"
        save_to_json(valid, output_path)
        save_errors(errors, "output/errors.txt")
        print("Saved valid flights to:", output_path)
        print("Saved errors to output/errors.txt")
        return

    # Parse folder of CSVs
    if args.dir:
        print("Parsing CSV files in folder:", args.dir)
        valid, errors = parse_csv_folder(args.dir)
        output_path = args.output or "output/db.json"
        save_to_json(valid, output_path)
        save_errors(errors, "output/errors.txt")
        print("Saved valid flights to:", output_path)
        print("Saved errors to output/errors.txt")
        return

    print("No input provided. Use -i FILE or -d FOLDER or -j DB.")


# =========================
# 9️⃣ Entry point
# =========================
if __name__ == "__main__":
    main()
