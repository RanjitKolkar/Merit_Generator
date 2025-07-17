import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Merit List Generator", layout="wide")
st.title("🎓 Merit List Generator")
st.info("This is demo file. Go to menu to upload a file!!!")
st.info("Go to Bottom to generate a Merit List by Category")
CATEGORY_COLORS = {
    "GENERAL": "#D1E8E4",
    "OBC-NCL": "#FFF3CD",
    "SCHEDULED CASTE (SC)": "#F8D7DA",
    "SCHEDULED TRIBE (ST)": "#D6D8D9",
    "EWS": "#CCE5FF"
}

# ============================ Utilities ============================

def extract_program_name(file_name):
    return os.path.splitext(os.path.basename(file_name))[0].replace("_", " ").upper()

def highlight_category_and_ties(df):
    tie_mask = df["ObtainMarks"].duplicated(keep=False)

    def style_row(row):
        base_color = CATEGORY_COLORS.get(str(row["CATEGORY"]).strip().upper(), "#FFFFFF")
        style = []
        is_tie = tie_mask.loc[row.name]
        for col in df.columns:
            cell_style = f"background-color: {base_color};"
            if is_tie:
                cell_style += "border: 2px solid red;"
            style.append(cell_style)
        return style

    return df.style.apply(style_row, axis=1)

def generate_merit_list(df, seat_matrix):
    merit_final = pd.DataFrame()
    for category in df["CATEGORY"].dropna().unique():
        cat_df = df[df["CATEGORY"] == category]
        seats = int(seat_matrix.get(category, 0)) * 2
        top = cat_df.sort_values(by="ObtainMarks", ascending=False).head(seats).copy()
        top.insert(0, "Sl. No.", range(1, len(top) + 1))
        merit_final = pd.concat([merit_final, top])
    selected_cols = ["Sl. No.", "FORM NUMBER", "Applicant Registration No", "NAME OF THE APPLICANT", "CATEGORY", "ObtainMarks"]
    return merit_final[selected_cols]

# ============================ File Handling ============================

demo_folder = "excel_files"
demo_files = [f for f in os.listdir(demo_folder) if f.endswith((".xlsx", ".xls"))]

st.sidebar.subheader("📂 File Selection")

use_demo = st.sidebar.checkbox("Use a demo file from 'excel_files' folder", value=True)
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
            seats = cols[i].number_input(f"{category}", min_value=4, step=1, key=category)
            seat_matrix[category] = seats

        # Preview
        st.subheader("📄 Uploaded Data Preview")
        st.dataframe(df_cleaned.head(10), use_container_width=True)

        # Generate Merit List
        if st.button("🔍 Generate Merit List"):
            st.subheader("🏆 Merit List (2× Seats Per Category)")
            merit_df = generate_merit_list(df_cleaned, seat_matrix)
            styled_df = highlight_category_and_ties(merit_df)
            st.dataframe(styled_df, use_container_width=True)

            # CSV Download
            csv = merit_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", data=csv, file_name=f"{program_name}_merit_list.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Failed to process the file. Error: {e}")
else:
    st.info("Please upload a file or choose from the demo folder.")
