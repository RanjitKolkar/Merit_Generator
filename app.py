import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Merit List Generator", layout="wide")
st.title("🎓 Merit List Generator")
st.info("This is demo file. Go to menu to upload a file!!!")
st.info("Go to Bottom to generate a Merit List by Category and General Merit List")

CATEGORY_COLORS = {
    "GENERAL": "#D1E8E4",
    "OBC-NCL": "#FFF3CD",
    "SCHEDULED CASTE (SC)": "#F8D7DA",
    "SCHEDULED TRIBE (ST)": "#D6D8D9",
    "EWS": "#CCE5FF"
}
TIE_COLOR = "#FFFF00"  # Bright Yellow

# ============================ Utilities ============================

def extract_program_name(file_name):
    return os.path.splitext(os.path.basename(file_name))[0].replace("_", " ").upper()

def highlight_category_and_ties(df):
    tie_mask = df.groupby("CATEGORY")["ObtainMarks"].transform(lambda x: x.duplicated(keep=False))

    def style_row(row):
        base_color = CATEGORY_COLORS.get(str(row["CATEGORY"]).strip().upper(), "#FFFFFF")
        is_tie = tie_mask[row.name]
        bg_color = TIE_COLOR if is_tie else base_color
        return [f"background-color: {bg_color}" for _ in row]

    return df.style.apply(style_row, axis=1)

def generate_category_merit_list(df, seat_matrix):
    merit_final = pd.DataFrame()
    for category in df["CATEGORY"].dropna().unique():
        if category.upper() == "GENERAL":
            continue  # Skip GENERAL from category-wise merit list
        cat_df = df[df["CATEGORY"] == category]
        seats = int(seat_matrix.get(category, 0)) * 3
        top = cat_df.sort_values(by="ObtainMarks", ascending=False).head(seats).copy()
        top.insert(0, "Sl. No.", range(1, len(top) + 1))
        merit_final = pd.concat([merit_final, top])
    selected_cols = ["Sl. No.", "FORM NUMBER", "Applicant Registration No", "NAME OF THE APPLICANT", "CATEGORY", "ObtainMarks"]
    return merit_final[selected_cols]

def generate_general_merit_list(df, seat_matrix):
    general_seats = int(seat_matrix.get("GENERAL", 0)) * 3  # Only GENERAL seats × 2
    df_sorted = df.sort_values(by="ObtainMarks", ascending=False).copy()
    df_sorted.insert(0, "Rank", range(1, len(df_sorted) + 1))
    selected_cols = ["Rank", "FORM NUMBER", "Applicant Registration No", "NAME OF THE APPLICANT", "CATEGORY", "ObtainMarks"]
    return df_sorted[selected_cols].head(general_seats)


def display_tie_summary(df):
    df["CATEGORY"] = df["CATEGORY"].astype(str)
    tie_df = df[df.duplicated(subset=["CATEGORY", "ObtainMarks"], keep=False)]
    if not tie_df.empty:
        st.subheader("⚠️ Tie Summary")
        grouped = tie_df.groupby(["CATEGORY", "ObtainMarks"])
        for (cat, marks), group in grouped:2
            if len(group) > 1:
                st.markdown(f"🎯 **Category:** `{cat}` | **Marks:** {marks} — {len(group)} candidates tied")
                st.dataframe(group[["FORM NUMBER", "NAME OF THE APPLICANT", "CATEGORY", "ObtainMarks"]])
    else:
        st.info("✅ No ties found within any category in the merit list.")

# ============================ File Handling ============================

demo_folder = "excel_files"
demo_files = [f for f in os.listdir(demo_folder) if f.endswith((".xlsx", ".xls"))]

st.sidebar.subheader("📂 File Selection")

use_demo = st.sidebar.checkbox("Use a demo files", value=True)
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if use_demo and demo_files:
    selected_demo = st.sidebar.selectbox("Choose a demo file", demo_files)
    selected_file_path = os.path.join(demo_folder, selected_demo)
else:
    selected_file_path = uploaded_file

# ============================ Main Processing ============================

if selected_file_path:
    try:
        df_raw = pd.read_excel(selected_file_path) if isinstance(selected_file_path, str) else pd.read_excel(selected_file_path)
        program_name = extract_program_name(selected_file_path.name if hasattr(selected_file_path, "name") else selected_file_path)

        st.header(f"📘 Program: {program_name}")

        df = df_raw.copy()
        df["CATEGORY"] = df["CATEGORY"].astype(str).str.strip()
        original_rows = df.shape[0]

        df["ObtainMarks"] = pd.to_numeric(df["ObtainMarks"], errors="coerce")
        df_cleaned = df.dropna(subset=["ObtainMarks"])
        cleaned_rows = df_cleaned.shape[0]
        removed_rows = original_rows - cleaned_rows
        unique_categories = sorted(df_cleaned["CATEGORY"].dropna().unique())
        category_count = len(unique_categories)

        # Stats summary
        with st.expander("📊 File Summary and Statistics", expanded=True):
            st.markdown(f"""
            - 🧾 **Original Rows:** {original_rows}  
            - ❌ **Rows Removed (Missing/Absent):** {removed_rows}  
            - ✅ **Valid Rows Remaining:** {cleaned_rows}  
            - 🧮 **Unique Categories:** {category_count}  
            - 🏷️ **Categories Detected:** `{", ".join(unique_categories)}`
            """)
            cat_counts = df_cleaned["CATEGORY"].value_counts().rename_axis('CATEGORY').reset_index(name='Count')
            st.dataframe(cat_counts)

        # Seat matrix input
        st.subheader("🪑 Enter Available Seats per Category")
        seat_matrix = {}
        cols = st.columns(len(unique_categories))
        for i, category in enumerate(unique_categories):
            seats = cols[i].number_input(f"{category}", min_value=1, step=1, key=category)
            seat_matrix[category] = seats

        # Preview
        st.subheader("📄 Uploaded Data Preview")
        st.dataframe(df_cleaned.head(10), use_container_width=True)

        # Generate Merit Lists
        if st.button("🔍 Generate Merit List"):
            # General Merit List
            st.subheader("🌐 General Merit List (All Applicants Ranked by Marks)")
            general_df = generate_general_merit_list(df_cleaned, seat_matrix)
            st.dataframe(general_df, use_container_width=True)

            # Download general merit list
            csv_general = general_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download General Merit List CSV", data=csv_general, file_name=f"{program_name}_general_merit_list.csv", mime="text/csv")

            # Category-wise Merit List
            st.subheader("🏅 Category-Wise Merit List (Excludes 'GENERAL')")
            merit_df = generate_category_merit_list(df_cleaned, seat_matrix)
            styled_df = highlight_category_and_ties(merit_df)
            st.dataframe(styled_df, use_container_width=True)

            # Tie summary
            display_tie_summary(merit_df)

            # Download category merit list
            csv = merit_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Category-wise Merit List CSV", data=csv, file_name=f"{program_name}_category_merit_list.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Failed to process the file. Error: {e}")
else:
    st.info("Please upload a file or choose from the demo folder.")

# Footer
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        color: #555555;
        text-align: center;
        padding: 8px 0;
        font-size: 12px;
        border-top: 1px solid #ddd;
        z-index: 9999;
    }
    </style>
    <div class="footer">
        ⚠️ <em>This is just a reference app. Not Official App. 
        Developed by ranjit.kolkar@gmail.com</em>
    </div>
    """,
    unsafe_allow_html=True,
)
