import streamlit as st
import pandas as pd
import os
import zipfile
from io import BytesIO


st.set_page_config(page_title="Merit List Generator", layout="wide")
st.title("🎓 Merit List Generator with Seat Matrix Integration")

EXPORT_COLUMNS = [
    "Merit No.", "FORM NUMBER", "NAME OF THE APPLICANT", "CATEGORY", "EMAIL", "MOBILE",
    "ObtainMarks", "Counselling Status"
]

@st.cache_data
def load_seat_matrix():
    return pd.DataFrame([
        {
            "School": "School of Cyber Security and Digital Forensics",
            "Program": "M.Tech. Cyber Security",
            "Campus": "Goa",
            "Approved Intake": 23,
            "GENERAL": 10,
            "OBC-NCL": 6,
            "SC": 3,
            "ST": 2,
            "EWS": 2,
            "PwD": 1
        },
        {
            "School": "School of Cyber Security and Digital Forensics",
            "Program": "M.Sc. Cyber Security",
            "Campus": "Goa",
            "Approved Intake": 30,
            "GENERAL": 12,
            "OBC-NCL": 8,
            "SC": 5,
            "ST": 2,
            "EWS": 3,
            "PwD": 2
        },
        {
            "School": "School of Cyber Security and Digital Forensics",
            "Program": "M.Sc. Digital Forensics and Information Security",
            "Campus": "Goa",
            "Approved Intake": 25,
            "GENERAL": 10,
            "OBC-NCL": 6,
            "SC": 4,
            "ST": 2,
            "EWS": 3,
            "PwD": 1
        }
    ])

def extract_program_name(file_name):
    return os.path.splitext(os.path.basename(file_name))[0].replace("_", " ").replace("MERGED", "").strip().upper()


def assign_merit_numbers(df):
    df = df.sort_values(by="ObtainMarks", ascending=False).copy()
    df["Merit No."] = df["ObtainMarks"].rank(method="min", ascending=False).astype(int)
    return df

def generate_general_merit_list(df, seats):
    total_call = seats.get("GENERAL", 0) * 3
    df_sorted = assign_merit_numbers(df)
    df_sorted["Counselling Status"] = ["Called for Counselling" if i < total_call else "Waitlisted" for i in range(len(df_sorted))]
    return df_sorted

def generate_category_merit_lists(df, seats):
    category_dfs = {}
    for cat in df["CATEGORY"].dropna().unique():
        if cat.strip().upper() == "GENERAL":
            continue
        sub_df = df[df["CATEGORY"] == cat].copy()
        sub_df = assign_merit_numbers(sub_df)
        top_n = seats.get(cat.strip().upper(), 0) * 3
        sub_df["Counselling Status"] = ["Called for Counselling" if i < top_n else "Waitlisted" for i in range(len(sub_df))]
        category_dfs[cat] = sub_df
    return category_dfs

def generate_pwd_merit_list(df):
    df["PwD (PERCENTAGE OF DISABILITY)"] = pd.to_numeric(df["PwD (PERCENTAGE OF DISABILITY)"], errors='coerce').fillna(0)
    pwd_df = df[df["PwD (PERCENTAGE OF DISABILITY)"] > 0].copy()
    pwd_df = assign_merit_numbers(pwd_df)
    pwd_df["Counselling Status"] = "--"
    return pwd_df

def display_tie_summary(df, label=""):
    tie_df = df[df.duplicated(subset=["ObtainMarks"], keep=False)]
    # if not tie_df.empty:
    #     st.markdown(f"#### ⚠️ Tie Summary {label}")
    #     grouped = tie_df.groupby("ObtainMarks")
    #     for marks, group in grouped:
    #         if len(group) > 1:
    #             st.markdown(f"🎯 Marks: **{marks}** — {len(group)} candidates tied")
    #             st.dataframe(group[EXPORT_COLUMNS])
import re

def normalize_category(cat):
    if not isinstance(cat, str):
        return cat

    cat = cat.strip().upper()

    # Normalize OBC - NCL variants
    cat = re.sub(r"OBC\s*-\s*NCL", "OBC-NCL", cat)

    # Map other variants
    replacements = {
        "SCHEDULED CASTE (SC)": "SC",
        "SCHEDULED TRIBE (ST)": "ST",
        "SCHEDULED CAST (SC)": "SC",
        "SCHEDULED TRIBE(ST)": "ST",
        "SCHEDULEDCASTE(SC)": "SC",
        "SCHEDULEDTRIBE(ST)": "ST",
    }

    return replacements.get(cat, cat)


# Load merged files
MERGED_FOLDER = "merged_files"
merged_files = [f for f in os.listdir(MERGED_FOLDER) if f.endswith(('.xlsx', '.xls'))]
selected_file = st.sidebar.selectbox("📁 Select Merged File", merged_files)

seat_matrix_df = load_seat_matrix()

if selected_file:
    file_path = os.path.join(MERGED_FOLDER, selected_file)
    df_raw = pd.read_excel(file_path)
    
    st.write(f"📄 Total rows before filtering: {len(df_raw)}")
    program_name = extract_program_name(selected_file)

    st.header(f"📘 Program: {program_name}")
    st.info(f"🔍 Extracted Program Name from File: `{program_name}`")
    # Filter Present only
    df = df_raw[df_raw["Final_Attendance"].astype(str).str.strip().str.lower() == "present"].copy()
    df["CATEGORY"] = df["CATEGORY"].astype(str).str.strip()
    df["CATEGORY"] = df["CATEGORY"].apply(normalize_category)  # normalize here
    df["ObtainMarks"] = pd.to_numeric(df["ObtainMarks"], errors="coerce")
    df_cleaned = df.dropna(subset=["ObtainMarks"])

    # Display category count
    category_counts = df_cleaned["CATEGORY"].value_counts().sort_index()

    st.markdown("### 🏷️ Category-wise Count (Present & Valid Marks only):")
    st.dataframe(category_counts.reset_index().rename(columns={"index": "Category", "CATEGORY": "Count"}))


    # Display cleaned detected categories
    detected_categories_cleaned = sorted(df_cleaned["CATEGORY"].dropna().unique())
    st.markdown(f"✅ **Normalized Categories (Present entries only):** {', '.join(detected_categories_cleaned)}")


    # Build dropdown options
    program_options = seat_matrix_df.apply(lambda row: f"{row['Program']} ({row['Campus']})", axis=1).tolist()

    # Show dropdown for user to select the correct program
    selected_program_label = st.selectbox("🎯 Select Matching Program for seat matrix", program_options)

    # Extract the selected row
    program_row = seat_matrix_df[seat_matrix_df.apply(
        lambda row: f"{row['Program']} ({row['Campus']})" == selected_program_label, axis=1
    )].iloc[0]

    seat_inputs = {}

    if program_row is not None:
        st.subheader("🪑 Default Seat Matrix (Editable)")
        editable_columns = ["GENERAL", "OBC-NCL", "SC", "ST", "EWS", "PwD"]
        cols = st.columns(len(editable_columns))
        for i, cat in enumerate(editable_columns):
            default_value = int(program_row[cat])
            seat_inputs[cat] = cols[i].number_input(f"{cat}", min_value=0, value=default_value, key=f"seat_{cat}")
    else:
        st.warning("⚠️ No default seat matrix found. Please enter manually.")
        editable_columns = ["GENERAL", "OBC-NCL", "SC", "ST", "EWS", "PwD"]
        for cat in editable_columns:
            seat_inputs[cat] = st.number_input(f"{cat}", min_value=0, value=0, key=f"seat_{cat}_manual")

    with st.expander("📊 Cleaned Data Preview and Stats", expanded=True):
        
        st.markdown(f"- 📄 **Total Rows Before Filtering:** `{len(df_raw)}`")
        st.markdown(f"- 🧾 **Rows After Filtering (`Present` only):** `{df_cleaned.shape[0]}`")
        st.markdown(f"- 🏷️ **Categories Detected (in Present entries):** `{', '.join(sorted(df_cleaned['CATEGORY'].unique()))}`")
        # st.dataframe(df_cleaned[EXPORT_COLUMNS[:-1]].head(10), use_container_width=True)

if st.button("🔍 Generate Merit Lists"):
    # 🟢 Generate merit lists first
    general_df = generate_general_merit_list(df_cleaned, seat_inputs)
    category_lists = generate_category_merit_lists(df_cleaned, seat_inputs)
    pwd_df = generate_pwd_merit_list(df_cleaned)

    # 🟢 Prepare ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add general merit list
        zip_file.writestr(f"{program_name}_general_merit_list.csv", general_df[EXPORT_COLUMNS].to_csv(index=False))

        # Add category-wise lists
        for cat, cat_df in category_lists.items():
            if cat.strip().upper() == "GENERAL":
                continue
            zip_file.writestr(f"{program_name}_{cat}_merit_list.csv", cat_df[EXPORT_COLUMNS].to_csv(index=False))

        # Add PwD list
        if not pwd_df.empty:
            zip_file.writestr(f"{program_name}_pwd_merit_list.csv", pwd_df[EXPORT_COLUMNS].to_csv(index=False))

    zip_buffer.seek(0)
    st.download_button("📦 Download All Merit Lists as ZIP", data=zip_buffer, file_name=f"{program_name}_all_merit_lists.zip", mime="application/zip")

    # General Merit List
    st.subheader("🌐 General Merit List")
    st.dataframe(general_df[EXPORT_COLUMNS], use_container_width=True)
    st.download_button("⬇️ Download General Merit List", data=general_df[EXPORT_COLUMNS].to_csv(index=False).encode("utf-8"), file_name=f"{program_name}_general_merit_list.csv")

    # Category-wise Merit List
    st.subheader("🏅 Category-wise Merit Lists")
    for cat, cat_df in category_lists.items():
        if cat.strip().upper() == "GENERAL":
            continue
        st.markdown(f"### 📘 Category: `{cat}`")
        st.dataframe(cat_df[EXPORT_COLUMNS], use_container_width=True)
        display_tie_summary(cat_df, cat)
        csv_cat = cat_df[EXPORT_COLUMNS].to_csv(index=False).encode("utf-8")
        st.download_button(f"⬇️ Download `{cat}` Merit List CSV", data=csv_cat, file_name=f"{program_name}_{cat}_merit_list.csv", mime="text/csv", key=f"download_{cat}")

    # PwD List
    st.subheader("♿ PwD Merit List")
    if not pwd_df.empty:
        st.dataframe(pwd_df[EXPORT_COLUMNS], use_container_width=True)
        display_tie_summary(pwd_df, "PwD")
        csv_pwd = pwd_df[EXPORT_COLUMNS].to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download PwD Merit List", data=csv_pwd, file_name=f"{program_name}_pwd_merit_list.csv", mime="text/csv")
    else:
        st.info("No PwD candidates found.")
