import sqlite3
import re
from difflib import SequenceMatcher


# ============================================================
# DATABASE CONNECTION
# ============================================================

DATABASE_NAME = "hospital.db"

conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()

print("=" * 70)
print("HOSPITAL PATIENT DATA MANAGEMENT SYSTEM")
print("=" * 70)

print("\n[1] Connecting to database...")

if conn:
    print("Database connection successful.")


# ============================================================
# CREATE PATIENT TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Patient (
    Patient_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Age INTEGER,
    Gender TEXT,
    Phone TEXT,
    Email TEXT,
    Diagnosis TEXT
)
""")

conn.commit()

print("\n[2] Patient table created successfully.")


# ============================================================
# SAMPLE DIRTY PATIENT DATA
# ============================================================

patients = [
    (1, "RAHUL kumar", 25, "male", "9876543210",
     "rahul@gmail.com", "diabetes"),

    (2, "rahul KUMAR", 25, "Male", "9876543210",
     "rahul@gmail.com", "Diabetes"),

    (3, "PRIYA SHARMA", -5, "FEMALE", "98765",
     None, "hypertension"),

    (4, "Arjun KUMAR", 150, "M", "9123456789",
     "arjun@gmail", "fever"),

    (5, "Sneha Rao", 29, "f", None,
     "sneha@gmail.com", "DIABETES"),

    (6, "Amit Singh", 40, "MALE", "8123456789",
     "amit@gmail.com", "cold"),

    (7, "Amit Singh", 40, "MALE", "8123456789",
     "amit@gmail.com", "cold"),

    (8, "Rhaul Kumar", 25, "male", "9876543210",
     "rahul@gmail.com", "diabetes")
]


# ============================================================
# CLEAR EXISTING DATA
# ============================================================

cursor.execute("DELETE FROM Patient")


# ============================================================
# INSERT DATA
# ============================================================

cursor.executemany("""
INSERT INTO Patient
(Patient_ID, Name, Age, Gender, Phone, Email, Diagnosis)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", patients)

conn.commit()

print("[3] Patient records inserted successfully.")


# ============================================================
# DISPLAY ORIGINAL DATA
# ============================================================

def display_table(table_name):
    print("\n" + "-" * 100)
    print(f"{table_name.upper()} TABLE")
    print("-" * 100)

    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    for row in rows:
        print(row)


display_table("Patient")


# ============================================================
# REGEX PATTERNS
# ============================================================

PHONE_PATTERN = r'^[6-9]\d{9}$'

EMAIL_PATTERN = r'^[\w\.-]+@[\w\.-]+\.\w+$'


# ============================================================
# STANDARDIZATION FUNCTIONS
# ============================================================

def normalize_name(name):
    """
    Removes unnecessary spaces and converts
    the name into title case.
    """

    if name is None:
        return None

    name = " ".join(name.strip().split())

    return name.title()


def standardize_gender(gender):
    """
    Converts different gender representations
    into Male or Female.
    """

    if gender is None:
        return None

    gender = gender.strip().lower()

    gender_map = {
        "m": "Male",
        "male": "Male",
        "f": "Female",
        "female": "Female"
    }

    return gender_map.get(gender, None)


def standardize_diagnosis(diagnosis):
    """
    Removes unnecessary spaces and standardizes
    capitalization of diagnosis.
    """

    if diagnosis is None:
        return None

    diagnosis = " ".join(diagnosis.strip().split())

    return diagnosis.title()


# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

def validate_age(age):
    """
    Valid age range is 0 to 120.
    Invalid values are converted to None.
    """

    if age is None:
        return None

    if 0 <= age <= 120:
        return age

    return None


def validate_phone(phone):
    """
    Validates a 10-digit Indian mobile number.
    """

    if phone is None:
        return None

    phone = str(phone).strip()

    if re.fullmatch(PHONE_PATTERN, phone):
        return phone

    return None


def validate_email(email):
    """
    Validates basic email format.
    """

    if email is None:
        return None

    email = email.strip()

    if re.fullmatch(EMAIL_PATTERN, email):
        return email.lower()

    return None


# ============================================================
# CLEAN ONE RECORD
# ============================================================

def clean_record(record):

    patient_id, name, age, gender, phone, email, diagnosis = record

    cleaned_name = normalize_name(name)
    cleaned_age = validate_age(age)
    cleaned_gender = standardize_gender(gender)
    cleaned_phone = validate_phone(phone)
    cleaned_email = validate_email(email)
    cleaned_diagnosis = standardize_diagnosis(diagnosis)

    return (
        patient_id,
        cleaned_name,
        cleaned_age,
        cleaned_gender,
        cleaned_phone,
        cleaned_email,
        cleaned_diagnosis
    )


# ============================================================
# CLEAN ALL PATIENT RECORDS
# ============================================================

cursor.execute("SELECT * FROM Patient")
original_records = cursor.fetchall()

cleaned_records = []

for record in original_records:
    cleaned_record = clean_record(record)
    cleaned_records.append(cleaned_record)


print("\n[4] Data cleaning completed.")


# ============================================================
# DISPLAY CLEANED RECORDS
# ============================================================

print("\n" + "-" * 100)
print("CLEANED RECORDS")
print("-" * 100)

for record in cleaned_records:
    print(record)


# ============================================================
# EXACT DUPLICATE DETECTION
# ============================================================

def find_exact_duplicates(records):

    duplicates = []

    seen = set()

    for record in records:

        # Exclude Patient_ID from duplicate comparison
        comparison_key = record[1:]

        if comparison_key in seen:
            duplicates.append(record)

        else:
            seen.add(comparison_key)

    return duplicates


exact_duplicates = find_exact_duplicates(cleaned_records)

print("\n" + "-" * 70)
print("EXACT DUPLICATE RECORDS")
print("-" * 70)

if exact_duplicates:

    for duplicate in exact_duplicates:
        print(duplicate)

else:
    print("No exact duplicates found.")


# ============================================================
# REMOVE EXACT DUPLICATES
# ============================================================

unique_records = []

seen_records = set()

for record in cleaned_records:

    comparison_key = record[1:]

    if comparison_key not in seen_records:

        unique_records.append(record)

        seen_records.add(comparison_key)


# ============================================================
# FUZZY MATCHING
# ============================================================

def similarity(value1, value2):

    if not value1 or not value2:
        return 0

    return SequenceMatcher(
        None,
        value1.lower(),
        value2.lower()
    ).ratio()


def find_fuzzy_duplicates(records, threshold=0.85):

    potential_duplicates = []

    for i in range(len(records)):

        for j in range(i + 1, len(records)):

            record1 = records[i]
            record2 = records[j]

            name1 = record1[1]
            name2 = record2[1]

            phone1 = record1[4]
            phone2 = record2[4]

            email1 = record1[5]
            email2 = record2[5]

            name_score = similarity(name1, name2)

            phone_match = (
                phone1 is not None
                and phone2 is not None
                and phone1 == phone2
            )

            email_match = (
                email1 is not None
                and email2 is not None
                and email1 == email2
            )

            # Flag as potential duplicate when:
            # 1. Name similarity is high AND
            # 2. Phone OR email matches

            if name_score >= threshold and (
                phone_match or email_match
            ):

                potential_duplicates.append(
                    (
                        record1[0],
                        record2[0],
                        round(name_score, 3),
                        phone_match,
                        email_match
                    )
                )

    return potential_duplicates


fuzzy_duplicates = find_fuzzy_duplicates(
    cleaned_records,
    threshold=0.85
)


print("\n" + "-" * 90)
print("POTENTIAL DUPLICATES USING FUZZY MATCHING")
print("-" * 90)

if fuzzy_duplicates:

    for duplicate in fuzzy_duplicates:

        print(
            f"Patient {duplicate[0]} <-> "
            f"Patient {duplicate[1]} | "
            f"Name Similarity: {duplicate[2]} | "
            f"Phone Match: {duplicate[3]} | "
            f"Email Match: {duplicate[4]}"
        )

else:

    print("No potential duplicates found.")


# ============================================================
# CREATE CLEAN_PATIENT TABLE
# ============================================================

cursor.execute("DROP TABLE IF EXISTS Clean_Patient")

cursor.execute("""
CREATE TABLE Clean_Patient (
    Patient_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Age INTEGER,
    Gender TEXT,
    Phone TEXT,
    Email TEXT,
    Diagnosis TEXT
)
""")

conn.commit()


# ============================================================
# INSERT UNIQUE CLEANED RECORDS
# ============================================================

cursor.executemany("""
INSERT INTO Clean_Patient
(Patient_ID, Name, Age, Gender, Phone, Email, Diagnosis)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", unique_records)

conn.commit()

print("\n[5] Clean_Patient table created successfully.")
print("[6] Cleaned records inserted successfully.")


# ============================================================
# DISPLAY CLEAN_PATIENT
# ============================================================

display_table("Clean_Patient")


# ============================================================
# CRUD OPERATIONS
# ============================================================

print("\n" + "=" * 70)
print("CRUD OPERATIONS")
print("=" * 70)


# ----------------------------
# SELECT
# ----------------------------

print("\nSELECT Operation:")

cursor.execute("""
SELECT Patient_ID, Name, Age, Gender
FROM Clean_Patient
""")

for row in cursor.fetchall():
    print(row)


# ----------------------------
# UPDATE
# ----------------------------

print("\nUPDATE Operation:")

cursor.execute("""
UPDATE Clean_Patient
SET Diagnosis = 'Diabetes'
WHERE Patient_ID = 1
""")

conn.commit()

cursor.execute("""
SELECT * FROM Clean_Patient
WHERE Patient_ID = 1
""")

print(cursor.fetchone())


# ----------------------------
# DELETE
# ----------------------------

print("\nDELETE Operation:")

# Delete one confirmed exact duplicate
if exact_duplicates:

    duplicate_id = exact_duplicates[0][0]

    cursor.execute("""
    DELETE FROM Clean_Patient
    WHERE Patient_ID = ?
    """, (duplicate_id,))

    conn.commit()

    print(
        f"Patient {duplicate_id} deleted "
        "because it was an exact duplicate."
    )

else:

    print("No exact duplicate available for DELETE demonstration.")


# ============================================================
# FINAL CLEANED DATA
# ============================================================

print("\n" + "=" * 70)
print("FINAL CLEAN_PATIENT DATA")
print("=" * 70)

cursor.execute("""
SELECT * FROM Clean_Patient
ORDER BY Patient_ID
""")

for row in cursor.fetchall():
    print(row)


# ============================================================
# UNSEEN DIRTY TEST DATA
# ============================================================

test_records = [
    (101, "JOHN DOE", 35, "m", "9876543212",
     "john@gmail.com", "diabetes"),

    (102, "john doe", 35, "Male", "9876543212",
     "john@gmail.com", "DIABETES"),

    (103, "Meena RAO", -10, "FEMALE", "12345",
     "meena@gmail", "fever"),

    (104, "Arun Kumar", 130, "male", None,
     "arun@gmail.com", "cold"),

    (105, "Karthik  RAJ", 28, "M", "8765432109",
     "karthik@gmail.com", "DIABETES")
]


# ============================================================
# TEST DATA TABLE
# ============================================================

cursor.execute("DROP TABLE IF EXISTS Test_Patient")

cursor.execute("""
CREATE TABLE Test_Patient (
    Patient_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Age INTEGER,
    Gender TEXT,
    Phone TEXT,
    Email TEXT,
    Diagnosis TEXT
)
""")

cursor.executemany("""
INSERT INTO Test_Patient
(Patient_ID, Name, Age, Gender, Phone, Email, Diagnosis)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", test_records)

conn.commit()


# ============================================================
# CLEAN TEST DATA
# ============================================================

cursor.execute("SELECT * FROM Test_Patient")

test_original_records = cursor.fetchall()

test_cleaned_records = [
    clean_record(record)
    for record in test_original_records
]


# ============================================================
# DISPLAY TEST RESULTS
# ============================================================

print("\n" + "=" * 70)
print("UNSEEN DIRTY DATA TESTING")
print("=" * 70)

print("\nOriginal Test Records:")

for record in test_original_records:
    print(record)


print("\nCleaned Test Records:")

for record in test_cleaned_records:
    print(record)


# ============================================================
# TEST FUZZY MATCHING
# ============================================================

test_fuzzy_duplicates = find_fuzzy_duplicates(
    test_cleaned_records,
    threshold=0.85
)


print("\nPotential duplicates in unseen test data:")

if test_fuzzy_duplicates:

    for duplicate in test_fuzzy_duplicates:

        print(
            f"Patient {duplicate[0]} <-> "
            f"Patient {duplicate[1]} | "
            f"Name Similarity: {duplicate[2]} | "
            f"Phone Match: {duplicate[3]} | "
            f"Email Match: {duplicate[4]}"
        )

else:

    print("No potential duplicates found.")


# ============================================================
# TEST EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("TEST EVALUATION")
print("=" * 70)

test_passed = True

for record in test_cleaned_records:

    patient_id = record[0]
    name = record[1]
    age = record[2]
    gender = record[3]
    phone = record[4]
    email = record[5]
    diagnosis = record[6]

    if patient_id == 103:

        if age is not None:
            test_passed = False

        if phone is not None:
            test_passed = False

        if email is not None:
            test_passed = False

    if patient_id == 104:

        if age is not None:
            test_passed = False

        if phone is not None:
            test_passed = False

    if gender not in ["Male", "Female"]:
        test_passed = False


if test_passed:

    print("UNSEEN DATA TEST: PASSED")
    print(
        "The cleaning system successfully handled "
        "previously unseen dirty records."
    )

else:

    print("UNSEEN DATA TEST: FAILED")


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("PROJECT SUMMARY")
print("=" * 70)

print(f"Original records: {len(original_records)}")
print(f"Exact duplicates detected: {len(exact_duplicates)}")
print(f"Potential fuzzy duplicates: {len(fuzzy_duplicates)}")
print(f"Unique cleaned records: {len(unique_records)}")
print(f"Unseen test records: {len(test_records)}")
print(
    "Unseen test status:",
    "PASSED" if test_passed else "FAILED"
)


# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()

print("\nDatabase connection closed.")
print("\nProject execution completed successfully.")
