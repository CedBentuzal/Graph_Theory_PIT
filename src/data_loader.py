import csv
import math
import sys
from pathlib import Path

MIN_PLACES = 3      # the contract says 3 to 10 places
MAX_PLACES = 10
START_LABEL = "A"   # A is always the start (index 0)

ROOT = Path(__file__).resolve().parent.parent
MATRIX_FILE = ROOT / "data" / "distance_matrix.csv"
LOCATIONS_FILE = ROOT / "data" / "locations.csv"

# The 4-place sample from the guide (used only to say "this is still the sample").
SAMPLE_MATRIX = [[0, 10, 15, 20], [10, 0, 35, 25], [15, 35, 0, 30], [20, 25, 30, 0]]


class DataError(ValueError):
    """A CSV file does not follow the data contract."""


def _read_rows(path):
    """Read a CSV file into a list of rows. Empty lines are skipped."""
    name = Path(path).name
    text = None
    
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(path, newline="", encoding=encoding) as f:
                text = f.read()
            break
        except FileNotFoundError:
            raise DataError(f"File not found: {path}") from None
        except UnicodeDecodeError:
            continue
    if text is None:
        raise DataError(f"Cannot read {name}. Save it as CSV (UTF-8).")

    rows = [[cell.strip() for cell in row] for row in csv.reader(text.splitlines())]
    rows = [row for row in rows if any(cell != "" for cell in row)]
    if not rows:
        raise DataError(f"{name} is empty")

    
    first_row = rows[0]
    if len(first_row) == 1:
        for wrong, wrong_name in ((";", "semicolons (;)"), ("\t", "tabs")):
            if wrong in first_row[0]:
                raise DataError(
                    f"{name} uses {wrong_name} between values. "
                    "Save it as CSV with commas."
                )
    return rows


def _trim(row, keep):
    
    while len(row) > keep and row[-1] == "":
        row = row[:-1]
    return row


def _to_number(text):
    
    try:
        value = float(text)
    except ValueError:
        return None
    if not math.isfinite(value):   
        return None
    return value


def load_matrix(path):
    #Read data/distance_matrix.csv.

    rows = _read_rows(path)

    
    labels = _trim(rows[0], 1)[1:]
    n = len(labels)
    if not MIN_PLACES <= n <= MAX_PLACES:
        raise DataError(
            f"The matrix has {n} places, expected {MIN_PLACES} to {MAX_PLACES}"
        )
    for position, label in enumerate(labels, start=1):
        if label == "":
            raise DataError(f"Column {position} has no label")
        if labels.count(label) > 1:
            raise DataError(f"Label {label} appears more than once")
    if labels[0] != START_LABEL:
        raise DataError(
            f"The first label must be '{START_LABEL}' (the start), "
            f"found '{labels[0]}'"
        )

    
    data_rows = rows[1:]
    if len(data_rows) != n:
        raise DataError(f"The matrix has {n} column labels but {len(data_rows)} rows")

    matrix = []
    for i, row in enumerate(data_rows):
        row = _trim(row, n + 1)
        row_label = row[0]

        
        if row_label != labels[i]:
            raise DataError(
                f"Row {i + 1} label '{row_label}' does not match "
                f"column label '{labels[i]}'"
            )

        
        cells = row[1:]
        if len(cells) != n:
            raise DataError(f"Row {row_label} has {len(cells)} values, expected {n}")

        numbers = []
        for j, text in enumerate(cells):
            # Check 3: every cell is a number (no "km" text, no comma decimals).
            value = _to_number(text)
            if value is None:
                raise DataError(
                    f"Cell {row_label}->{labels[j]} is not a number: '{text}'"
                )
         
            if i == j and value != 0:
                raise DataError(f"Diagonal {row_label}->{labels[j]} must be 0")
            
            if i != j and value <= 0:
                raise DataError(f"Distance {row_label}->{labels[j]} must be > 0")
            numbers.append(value)
        matrix.append(numbers)

    return labels, matrix


def load_locations(path, labels=None):
    
    rows = _read_rows(path)

    header = [cell.lower() for cell in _trim(rows[0], 4)]
    expected = ["label", "name", "latitude", "longitude"]
    if header != expected:
        raise DataError("locations.csv must start with: " + ",".join(expected))

    locations = {}
    for row in rows[1:]:
        row = _trim(row, 4)
        if len(row) != 4:
            raise DataError(
                f"locations.csv row '{row[0]}' has {len(row)} values, expected 4"
            )
        label, name, lat_text, lon_text = row
        if label in locations:
            raise DataError(f"Label {label} appears more than once in locations.csv")
        if name == "":
            raise DataError(f"Label {label} has no name in locations.csv")

        latitude = _to_number(lat_text)
        if latitude is None or not -90 <= latitude <= 90:
            raise DataError(f"Latitude of {label} is not valid: '{lat_text}'")
        longitude = _to_number(lon_text)
        if longitude is None or not -180 <= longitude <= 180:
            raise DataError(f"Longitude of {label} is not valid: '{lon_text}'")

        locations[label] = (name, latitude, longitude)

   
    if labels is not None:
        for label in labels:
            if label not in locations:
                raise DataError(
                    f"Label {label} is in the matrix but not in locations.csv"
                )
        for label in locations:
            if label not in labels:
                raise DataError(
                    f"Label {label} is in locations.csv but not in the matrix"
                )

    return locations



def find_suspicious(labels, matrix):
    """Return a list of sentences about numbers that look like typos."""
    n = len(labels)
    notes = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            direct = matrix[i][j]
            back = matrix[j][i]

            # 1. One direction is more than 3 times the other (and > 1 km apart).
            #    Example: 2.4 typed as 24.
            if i < j:
                big, small = max(direct, back), min(direct, back)
                if big > 3 * small and big - small > 1:
                    notes.append(
                        f"{labels[i]}->{labels[j]} is {direct:g} km but "
                        f"{labels[j]}->{labels[i]} is {back:g} km "
                        "(very different in each direction)"
                    )

            # 2. The direct road is more than 2 times a route through one
            #    other place (and > 1 km longer).
            for k in range(n):
                if k in (i, j):
                    continue
                via = matrix[i][k] + matrix[k][j]
                if direct > 2 * via and direct - via > 1:
                    notes.append(
                        f"{labels[i]}->{labels[j]} is {direct:g} km but "
                        f"{labels[i]}->{labels[k]}->{labels[j]} is only {via:g} km "
                        "(the direct road is much longer)"
                    )
                    break    
    return notes


def check_data(matrix_path=MATRIX_FILE, locations_path=LOCATIONS_FILE):
    """Print a short report about the two data files. Returns 0 if they load."""
    print("=== Data check ===")
    print(f"Matrix file    : {matrix_path}")
    print(f"Locations file : {locations_path}")
    try:
        labels, matrix = load_matrix(matrix_path)
        locations = load_locations(locations_path, labels)
    except DataError as error:
        print(f"DATA ERROR: {error}")
        print("Fix the CSV file and run again.")
        return 1

    n = len(labels)
    print("Format         : OK (follows the data contract)")
    print(f"Places         : {n} ({labels[0]} to {labels[-1]})")
    for label in labels:
        print(f"  {label} {locations[label][0]}")

    # Count the pairs where A->B is not the same as B->A (one-way roads).
    pairs = n * (n - 1) // 2
    one_way = sum(1 for i in range(n) for j in range(i + 1, n)
                  if not math.isclose(matrix[i][j], matrix[j][i]))
    print(f"One-way pairs  : {one_way} of {pairs} pairs differ by direction")

    if matrix == SAMPLE_MATRIX:
        print("NOTE: this is still the 4-place SAMPLE from the guide, not real data.")

    notes = find_suspicious(labels, matrix)
    if notes:
        print("Numbers to double-check with Ced's spreadsheet "
              "(they may still be correct):")
        for note in notes:
            print(f"  - {note}")
    else:
        print("Numbers to double-check: none found")
    print("Ready. Now run: python src/main.py")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")    # never crash on odd letters
    sys.exit(check_data(*sys.argv[1:3]))
