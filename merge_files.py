# merge_files.py

import os
import pandas as pd
import difflib

# Directories
excel_folder = "excel_files"
merge_folder = "merge_by_mistake_international"
merged_folder = "merged_files"

os.makedirs(merged_folder, exist_ok=True)

# Required columns
required_columns = [
    "Merit No.", "FORM NUMBER", "NAME OF THE APPLICANT", "CATEGORY",
    "PwD (PERCENTAGE OF DISABILITY)", "EMAIL", "MOBILE",
    "OU CENTER PREFERENCE 1", "OU CENTER PREFERENCE 2", "Final_Attendance","ObtainMarks"
]

# Utility functions
def clean_name(name):
    return os.path.splitext(name.lower().replace("_", " ").replace("-", " ").strip())[0]

def get_closest_match(file, file_list):
    file_base = clean_name(file)
    matches = difflib.get_close_matches(file_base, [clean_name(f) for f in file_list], n=1, cutoff=0.4)
    if matches:
        for f in file_list:
            if clean_name(f) == matches[0]:
                return f
    return None

# Merge logic
def merge_files_by_keyword():
    excel_files = [f for f in os.listdir(excel_folder) if f.endswith((".xlsx", ".xls"))]
    merge_files = [f for f in os.listdir(merge_folder) if f.endswith((".xlsx", ".xls"))]

    merged_count = 0

    for ef in excel_files:
        match = get_closest_match(ef, merge_files)
        if match:
            path1 = os.path.join(excel_folder, ef)
            path2 = os.path.join(merge_folder, match)

            try:
                df1 = pd.read_excel(path1)
                df2 = pd.read_excel(path2)

                combined = pd.concat([df1, df2], ignore_index=True)
                combined = combined.drop_duplicates()

                # Filter only required columns
                available_cols = [col for col in required_columns if col in combined.columns]
                missing_cols = [col for col in required_columns if col not in available_cols]
                for col in missing_cols:
                    combined[col] = None

                merged_df = combined[required_columns]

                merged_name = f"merged_{clean_name(ef).replace(' ', '_')}.xlsx"
                merged_path = os.path.join(merged_folder, merged_name)
                merged_df.to_excel(merged_path, index=False)
                print(f"✅ Merged: {ef} + {match} ➜ {merged_name}")
                merged_count += 1
            except Exception as e:
                print(f"❌ Failed to merge {ef} with {match}: {e}")

    if merged_count == 0:
        print("⚠️ No files were merged.")
    else:
        print(f"\n✅ Done. Total merged files: {merged_count}")

if __name__ == "__main__":
    merge_files_by_keyword()
