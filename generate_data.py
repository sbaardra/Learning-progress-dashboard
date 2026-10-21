
import pandas as pd
import numpy as np

# Make the results reproducible
np.random.seed(42)

# Sample size
number_of_students = 120

# Courses offered on the learning platform
courses = [
    "Python",
    "Data Analytics",
    "Web Development",
    "Machine Learning",
    "SQL"
]

# Generate fictional student records
data = []

for i in range(1, number_of_students + 1):

    student_id = f"S{i:03d}"
    student_name = f"Student {i}"

    # Randomly assign a course
    course = np.random.choice(courses)

    # Generate enrollment date
    enrollment_date = (
        pd.Timestamp("2026-01-01")
        + pd.Timedelta(days=int(np.random.randint(0, 290)))
    )

    # Each course has between 10 and 30 lessons
    total_lessons = int(np.random.randint(10, 31))

    # Generate the number of completed lessons
    lessons_completed = int(
        np.random.randint(0, total_lessons + 1)
    )

    # Calculate progress percentage
    progress_score = round(
        (lessons_completed / total_lessons) * 100, 2
    )

    # Generate assessment score between 0 and 100
    assessment_score = int(
        np.clip(np.random.normal(70, 15), 0, 100)
    )

    # Generate assessment attempts
    assessment_attempts = int(np.random.randint(1, 5))

    # Store one record
    data.append({
        "student_id": student_id,
        "student_name": student_name,
        "course": course,
        "enrollment_date": enrollment_date,
        "lessons_completed": lessons_completed,
        "total_lessons": total_lessons,
        "progress_score": progress_score,
        "assessment_score": assessment_score,
        "assessment_attempts": assessment_attempts
    })

# Convert the records to a DataFrame
df = pd.DataFrame(data)

# Save as a CSV file
df.to_csv("learning_data.csv", index=False)

print("Sample learning dataset created successfully!")
print("Number of records:", len(df))
print("\nFirst five records:")
print(df.head())
print("\nDataset information:")
print(df.info())
