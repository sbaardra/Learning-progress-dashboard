
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Learning Progress Dashboard",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Learning Progress Dashboard")
st.write(
    "Analyze course enrollment, lesson completion, "
    "student progress, and assessment performance."
)

# ==================================================
# 2. LOAD DATA
# ==================================================

DATA_FILE = Path(__file__).parent / "learning_data.csv"

if not DATA_FILE.exists():
    st.error(
        "Dataset not found. Run generate_data.py first."
    )
    st.stop()

df = pd.read_csv(DATA_FILE)

# ==================================================
# 3. DATA CLEANING AND VALIDATION
# ==================================================

required_columns = [
    "student_id",
    "student_name",
    "course",
    "enrollment_date",
    "lessons_completed",
    "total_lessons",
    "progress_score",
    "assessment_score",
    "assessment_attempts"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(f"Missing columns: {missing_columns}")
    st.stop()

df["enrollment_date"] = pd.to_datetime(
    df["enrollment_date"], errors="coerce"
)

numeric_columns = [
    "lessons_completed",
    "total_lessons",
    "progress_score",
    "assessment_score",
    "assessment_attempts"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col], errors="coerce"
    )

df = df.dropna(subset=required_columns).copy()

# Remove duplicate student-course records
df = df.drop_duplicates(
    subset=["student_id", "course"]
).copy()

# Remove invalid records
df = df[
    (df["total_lessons"] > 0)
    & (df["lessons_completed"] >= 0)
    & (df["lessons_completed"] <= df["total_lessons"])
    & (df["assessment_score"].between(0, 100))
    & (df["assessment_attempts"] >= 1)
].copy()

if df.empty:
    st.error("No valid records available.")
    st.stop()

# Calculate progress using lesson counts
df["progress_score"] = (
    df["lessons_completed"]
    / df["total_lessons"]
    * 100
)

# Calculate remaining lessons
df["lessons_remaining"] = (
    df["total_lessons"] - df["lessons_completed"]
)

# Classify learning status
df["status"] = "In Progress"

df.loc[
    df["progress_score"] < 30, "status"
] = "At Risk"

df.loc[
    df["progress_score"] >= 100, "status"
] = "Completed"

# ==================================================
# 4. SIDEBAR FILTERS
# ==================================================

st.sidebar.header("Dashboard Filters")

course_options = sorted(df["course"].unique())

selected_courses = st.sidebar.multiselect(
    "Select Courses",
    options=course_options,
    default=course_options
)

min_date = df["enrollment_date"].min().date()
max_date = df["enrollment_date"].max().date()

selected_dates = st.sidebar.date_input(
    "Enrollment Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

selected_statuses = st.sidebar.multiselect(
    "Learning Status",
    options=["Completed", "In Progress", "At Risk"],
    default=["Completed", "In Progress", "At Risk"]
)

min_progress, max_progress = st.sidebar.slider(
    "Progress Score Range (%)",
    min_value=0,
    max_value=100,
    value=(0, 100)
)

# ==================================================
# 5. APPLY FILTERS
# ==================================================

filtered_df = df[
    df["course"].isin(selected_courses)
    & df["status"].isin(selected_statuses)
    & df["progress_score"].between(
        min_progress, max_progress
    )
].copy()

if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates

        filtered_df = filtered_df[
            filtered_df["enrollment_date"].dt.date.between(
                start_date, end_date
            )
        ]

    elif len(selected_dates) == 1:
        selected_date = selected_dates[0]

        filtered_df = filtered_df[
            filtered_df["enrollment_date"].dt.date
            == selected_date
        ]

elif selected_dates:
    filtered_df = filtered_df[
        filtered_df["enrollment_date"].dt.date
        == selected_dates
    ]

# ==================================================
# 6. SUMMARY METRICS
# ==================================================

st.subheader("Learning Overview")

if filtered_df.empty:
    st.warning(
        "No records match the selected filters. "
        "Change the filters to see results."
    )

else:
    total_enrollments = len(filtered_df)

    unique_students = filtered_df[
        "student_id"
    ].nunique()

    average_progress = filtered_df[
        "progress_score"
    ].mean()

    average_assessment = filtered_df[
        "assessment_score"
    ].mean()

    # Completion rate per enrollment
    completion_rate = (
        filtered_df["status"].eq("Completed").mean()
        * 100
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Enrollments",
        f"{total_enrollments:,}"
    )

    col2.metric(
        "Unique Students",
        f"{unique_students:,}"
    )

    col3.metric(
        "Average Progress",
        f"{average_progress:.1f}%"
    )

    col4, col5 = st.columns(2)

    col4.metric(
        "Average Assessment Score",
        f"{average_assessment:.1f}/100"
    )

    col5.metric(
        "Course Completion Rate",
        f"{completion_rate:.1f}%"
    )

    # ==================================================
    # 7. COURSE ENROLLMENT
    # ==================================================

    st.subheader("1. Course Enrollment")

    enrollment_data = (
        filtered_df.groupby("course")
        .size()
        .reset_index(name="enrollments")
        .sort_values("enrollments", ascending=False)
    )

    fig_enrollment = px.bar(
        enrollment_data,
        x="course",
        y="enrollments",
        color="course",
        text="enrollments",
        title="Number of Enrollments by Course",
        labels={
            "course": "Course",
            "enrollments": "Enrollments"
        }
    )

    fig_enrollment.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fig_enrollment,
        use_container_width=True
    )

    # ==================================================
    # 8. MONTHLY ENROLLMENT TRENDS
    # ==================================================

    st.subheader("2. Monthly Enrollment Trends")

    monthly_data = (
        filtered_df.assign(
            month=filtered_df[
                "enrollment_date"
            ].dt.to_period("M")
        )
        .groupby("month")
        .size()
        .reset_index(name="enrollments")
    )

    monthly_data["month"] = (
        monthly_data["month"].astype(str)
    )

    fig_monthly = px.line(
        monthly_data,
        x="month",
        y="enrollments",
        markers=True,
        title="Monthly Course Enrollments",
        labels={
            "month": "Month",
            "enrollments": "Enrollments"
        }
    )

    st.plotly_chart(
        fig_monthly,
        use_container_width=True
    )

    # ==================================================
    # 9. PROGRESS DISTRIBUTION
    # ==================================================

    st.subheader("3. Student Progress Distribution")

    fig_progress = px.histogram(
        filtered_df,
        x="progress_score",
        nbins=10,
        color="status",
        title="Distribution of Student Progress",
        labels={
            "progress_score": "Progress (%)",
            "status": "Learning Status"
        }
    )

    st.plotly_chart(
        fig_progress,
        use_container_width=True
    )

    # ==================================================
    # 10. LESSON COMPLETION
    # ==================================================

    st.subheader("4. Lesson Completion by Course")

    lesson_data = (
        filtered_df.groupby("course", as_index=False)
        .agg(
            lessons_completed=("lessons_completed", "sum"),
            lessons_remaining=("lessons_remaining", "sum")
        )
    )

    lesson_data_long = lesson_data.melt(
        id_vars="course",
        value_vars=[
            "lessons_completed",
            "lessons_remaining"
        ],
        var_name="lesson_status",
        value_name="lesson_count"
    )

    fig_lessons = px.bar(
        lesson_data_long,
        x="course",
        y="lesson_count",
        color="lesson_status",
        barmode="stack",
        title="Completed vs Remaining Lessons",
        labels={
            "course": "Course",
            "lesson_count": "Number of Lessons",
            "lesson_status": "Lesson Status"
        }
    )

    st.plotly_chart(
        fig_lessons,
        use_container_width=True
    )

    # ==================================================
    # 11. ASSESSMENT PERFORMANCE
    # ==================================================

    st.subheader("5. Assessment Performance by Course")

    assessment_data = (
        filtered_df.groupby("course", as_index=False)
        .agg(
            average_score=("assessment_score", "mean"),
            student_count=("student_id", "nunique")
        )
    )

    assessment_data["average_score"] = (
        assessment_data["average_score"].round(2)
    )

    fig_assessment = px.bar(
        assessment_data,
        x="course",
        y="average_score",
        color="average_score",
        text="average_score",
        title="Average Assessment Score by Course",
        labels={
            "course": "Course",
            "average_score": "Average Score out of 100"
        },
        color_continuous_scale="Blues"
    )

    fig_assessment.update_yaxes(range=[0, 100])

    st.plotly_chart(
        fig_assessment,
        use_container_width=True
    )

    # ==================================================
    # 12. PROGRESS VS ASSESSMENT SCORE
    # ==================================================

    st.subheader("6. Progress vs Assessment Score")

    fig_scatter = px.scatter(
        filtered_df,
        x="progress_score",
        y="assessment_score",
        color="course",
        hover_data=[
            "student_id",
            "student_name",
            "lessons_completed",
            "assessment_attempts"
        ],
        title="Learning Progress vs Assessment Scores",
        labels={
            "progress_score": "Progress (%)",
            "assessment_score": "Assessment Score"
        }
    )

    st.plotly_chart(
        fig_scatter,
        use_container_width=True
    )

    # ==================================================
    # 13. LEARNING STATUS SUMMARY
    # ==================================================

    st.subheader("7. Learning Status Summary")

    status_data = (
        filtered_df["status"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="enrollments")
    )

    fig_status = px.pie(
        status_data,
        names="status",
        values="enrollments",
        hole=0.45,
        title="Distribution of Learning Status"
    )

    st.plotly_chart(
        fig_status,
        use_container_width=True
    )

    # ==================================================
    # 14. STUDENT DETAILS TABLE
    # ==================================================

    st.subheader("Student-Level Details")

    display_columns = [
        "student_id",
        "student_name",
        "course",
        "enrollment_date",
        "lessons_completed",
        "total_lessons",
        "progress_score",
        "assessment_score",
        "assessment_attempts",
        "status"
    ]

    display_df = filtered_df[
        display_columns
    ].copy()

    display_df["enrollment_date"] = (
        display_df["enrollment_date"]
        .dt.strftime("%Y-%m-%d")
    )

    display_df["progress_score"] = (
        display_df["progress_score"].round(1)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # ==================================================
    # 15. DOWNLOAD FILTERED DATA
    # ==================================================

    st.subheader("Download Results")

    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_data,
        file_name="filtered_learning_data.csv",
        mime="text/csv"
    )

# ==================================================
# 16. FOOTER
# ==================================================

st.divider()

st.caption(
    "Learning Progress Dashboard | "
    "Built with Python, Pandas, Plotly, and Streamlit. "
    "Sample data is fictional."
)
