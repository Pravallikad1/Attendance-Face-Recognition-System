import csv
from collections import defaultdict
import matplotlib.pyplot as plt

# ==========================================
# SETTINGS
# ==========================================

ATTENDANCE_FILE = "attendance.csv"
REPORT_FILE = "attendance_report.txt"
SUMMARY_FILE = "attendance_summary.csv"
BAR_CHART_FILE = "attendance_chart.png"
PIE_CHART_FILE = "attendance_pie_chart.png"

LOW_ATTENDANCE_LIMIT = 75


# ==========================================
# LOAD ATTENDANCE
# ==========================================

def load_attendance():
    records = []

    with open(ATTENDANCE_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            records.append(row)

    return records


# ==========================================
# STUDENT ATTENDANCE DATA
# ==========================================

def calculate_student_data(records):
    students = defaultdict(
        lambda: {
            "Present": 0,
            "Absent": 0
        }
    )

    for record in records:
        student_id = record["student_id"]
        status = record["status"]

        if status in ["Present", "Absent"]:
            students[student_id][status] += 1

    return students


# ==========================================
# DAILY ATTENDANCE DATA
# ==========================================

def calculate_daily_data(records):
    daily = defaultdict(
        lambda: {
            "Present": 0,
            "Absent": 0
        }
    )

    for record in records:
        date = record["date"]
        status = record["status"]

        if status in ["Present", "Absent"]:
            daily[date][status] += 1

    return daily


# ==========================================
# GENERATE CSV SUMMARY
# ==========================================

def generate_summary_csv(students):

    with open(SUMMARY_FILE, "w", newline="") as file:

        fieldnames = [
            "student_id",
            "present",
            "absent",
            "attendance_percentage",
            "status"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for student_id, data in sorted(students.items()):

            present = data["Present"]
            absent = data["Absent"]

            total = present + absent

            if total > 0:
                percentage = (present / total) * 100
            else:
                percentage = 0

            if percentage < LOW_ATTENDANCE_LIMIT:
                status = "LOW ATTENDANCE"
            else:
                status = "GOOD"

            writer.writerow({
                "student_id": student_id,
                "present": present,
                "absent": absent,
                "attendance_percentage": f"{percentage:.2f}",
                "status": status
            })

    print()
    print("Attendance summary CSV created successfully!")
    print("File:", SUMMARY_FILE)


# ==========================================
# TEXT REPORT
# ==========================================

def generate_report(students, daily):

    total_present = sum(
        data["Present"]
        for data in students.values()
    )

    total_absent = sum(
        data["Absent"]
        for data in students.values()
    )

    total_records = total_present + total_absent

    if total_records > 0:
        overall_percentage = (
            total_present / total_records
        ) * 100
    else:
        overall_percentage = 0

    report = []

    report.append("================================")
    report.append("       ATTENDANCE REPORT")
    report.append("================================")
    report.append("")

    # Overall summary
    report.append("OVERALL SUMMARY")
    report.append("----------------")
    report.append(f"Total Students: {len(students)}")
    report.append(f"Total Records: {total_records}")
    report.append(f"Total Present: {total_present}")
    report.append(f"Total Absent: {total_absent}")
    report.append(
        f"Overall Attendance: {overall_percentage:.2f}%"
    )
    report.append("")

    # Student attendance
    report.append("STUDENT ATTENDANCE")
    report.append("------------------")

    for student_id, data in sorted(students.items()):

        present = data["Present"]
        absent = data["Absent"]

        total = present + absent

        if total > 0:
            percentage = (present / total) * 100
        else:
            percentage = 0

        if percentage < LOW_ATTENDANCE_LIMIT:
            status = "LOW ATTENDANCE"
        else:
            status = "GOOD"

        report.append(f"Student ID: {student_id}")
        report.append(f"Present: {present}")
        report.append(f"Absent: {absent}")
        report.append(f"Attendance: {percentage:.2f}%")
        report.append(f"STATUS: {status}")
        report.append("------------------")

    # Low attendance
    report.append("")
    report.append("LOW ATTENDANCE STUDENTS")
    report.append("-----------------------")

    low_count = 0

    for student_id, data in sorted(students.items()):

        present = data["Present"]
        absent = data["Absent"]

        total = present + absent

        if total > 0:
            percentage = (present / total) * 100
        else:
            percentage = 0

        if percentage < LOW_ATTENDANCE_LIMIT:
            report.append(
                f"{student_id} - {percentage:.2f}%"
            )
            low_count += 1

    if low_count == 0:
        report.append("No students have low attendance.")

    # Daily attendance
    report.append("")
    report.append("DAILY ATTENDANCE")
    report.append("----------------")

    for date, data in sorted(daily.items()):

        report.append(f"Date: {date}")
        report.append(f"Present: {data['Present']}")
        report.append(f"Absent: {data['Absent']}")
        report.append("------------------")

    # Save report
    with open(REPORT_FILE, "w") as file:
        file.write("\n".join(report))

    print()
    print("\n".join(report))

    print()
    print("================================")
    print("Report saved successfully!")
    print("File:", REPORT_FILE)
    print("================================")


# ==========================================
# DASHBOARD STATISTICS
# ==========================================

def show_dashboard_statistics(students):

    total_present = sum(
        data["Present"]
        for data in students.values()
    )

    total_absent = sum(
        data["Absent"]
        for data in students.values()
    )

    total_records = total_present + total_absent

    if total_records > 0:
        attendance_percentage = (
            total_present / total_records
        ) * 100
    else:
        attendance_percentage = 0

    low_attendance_students = 0

    for student_id, data in students.items():

        total = data["Present"] + data["Absent"]

        if total > 0:
            percentage = (
                data["Present"] / total
            ) * 100
        else:
            percentage = 0

        if percentage < LOW_ATTENDANCE_LIMIT:
            low_attendance_students += 1

    print()
    print("===== DASHBOARD STATISTICS =====")
    print("Total Students:", len(students))
    print("Total Present:", total_present)
    print("Total Absent:", total_absent)
    print(
        "Overall Attendance:",
        round(attendance_percentage, 2),
        "%"
    )
    print(
        "Low Attendance Students:",
        low_attendance_students
    )


# ==========================================
# DATE-SPECIFIC ATTENDANCE
# ==========================================

def show_date_statistics(records, target_date):

    present_students = set()
    absent_students = set()

    for record in records:

        if record["date"] == target_date:

            if record["status"] == "Present":
                present_students.add(
                    record["student_id"]
                )

            elif record["status"] == "Absent":
                absent_students.add(
                    record["student_id"]
                )

    total_students = (
        len(present_students) +
        len(absent_students)
    )

    if total_students > 0:
        percentage = (
            len(present_students) /
            total_students
        ) * 100
    else:
        percentage = 0

    print()
    print("===== DATE ATTENDANCE =====")
    print("Date:", target_date)
    print("Total Students:", total_students)
    print("Present:", len(present_students))
    print("Absent:", len(absent_students))
    print(
        "Attendance:",
        round(percentage, 2),
        "%"
    )


# ==========================================
# BAR CHART
# ==========================================

def generate_attendance_chart(students):

    student_ids = []
    percentages = []

    for student_id, data in sorted(students.items()):

        present = data["Present"]
        absent = data["Absent"]

        total = present + absent

        if total > 0:
            percentage = (present / total) * 100
        else:
            percentage = 0

        student_ids.append(student_id)
        percentages.append(percentage)

    plt.figure(figsize=(10, 6))

    plt.bar(
        student_ids,
        percentages
    )

    plt.xlabel("Student ID")
    plt.ylabel("Attendance Percentage")
    plt.title("Student Attendance Percentage")

    plt.ylim(0, 100)

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(BAR_CHART_FILE)

    plt.close()

    print()
    print("Attendance bar chart created successfully!")
    print("File:", BAR_CHART_FILE)


# ==========================================
# PIE CHART
# ==========================================

def generate_pie_chart(students):

    total_present = sum(
        data["Present"]
        for data in students.values()
    )

    total_absent = sum(
        data["Absent"]
        for data in students.values()
    )

    values = [
        total_present,
        total_absent
    ]

    labels = [
        "Present",
        "Absent"
    ]

    plt.figure(figsize=(7, 7))

    plt.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title("Overall Attendance")

    plt.tight_layout()

    plt.savefig(PIE_CHART_FILE)

    plt.close()

    print()
    print("Attendance pie chart created successfully!")
    print("File:", PIE_CHART_FILE)


# ==========================================
# MAIN PROGRAM
# ==========================================

def main():

    print("================================")
    print("   ATTENDANCE ANALYTICS SYSTEM")
    print("================================")

    # Load data
    records = load_attendance()

    # Calculate data
    students = calculate_student_data(records)
    daily = calculate_daily_data(records)

    # Generate text report
    generate_report(
        students,
        daily
    )

    # Generate CSV summary
    generate_summary_csv(
        students
    )

    # Dashboard statistics
    show_dashboard_statistics(
        students
    )

    # Date statistics
    show_date_statistics(
        records,
        "2026-09-16"
    )

    # Bar chart
    generate_attendance_chart(
        students
    )

    # Pie chart
    generate_pie_chart(
        students
    )

    print()
    print("================================")
    print(" ALL ANALYTICS COMPLETED")
    print("================================")


# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    main()