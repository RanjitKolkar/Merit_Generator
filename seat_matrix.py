import pandas as pd

# Goa campus seat matrix data
data = [
    {
        "School": "School of Cyber Security and Digital Forensics",
        "Program": "M.Tech. Cyber Security",
        "Campus": "Goa",
        "Approved Intake": 23,
        "Unreserved": 10,
        "OBC-NCL": 6,
        "SC": 3,
        "ST": 2,
        "EWS": 2,
        "PwD": 1,
        "Armed Forces": 2,
        "J&K Migrants": 1,
        "Foreign Nationals": 6,
        "Grand Total": 32
    },
    {
        "School": "School of Cyber Security and Digital Forensics",
        "Program": "M.Sc. Cyber Security",
        "Campus": "Goa",
        "Approved Intake": 30,
        "Unreserved": 12,
        "OBC-NCL": 8,
        "SC": 5,
        "ST": 2,
        "EWS": 3,
        "PwD": 2,
        "Armed Forces": 2,
        "J&K Migrants": 1,
        "Foreign Nationals": 8,
        "Grand Total": 41
    },
    {
        "School": "School of Cyber Security and Digital Forensics",
        "Program": "M.Sc. Digital Forensics and Information Security",
        "Campus": "Goa",
        "Approved Intake": 25,
        "Unreserved": 10,
        "OBC-NCL": 6,
        "SC": 4,
        "ST": 2,
        "EWS": 3,
        "PwD": 1,
        "Armed Forces": 2,
        "J&K Migrants": 1,
        "Foreign Nationals": 6,
        "Grand Total": 34
    }
]

# Convert to DataFrame
df_goa = pd.DataFrame(data)

# Save to Excel
output_file = "Goa_Campus_Seat_Matrix.xlsx"
df_goa.to_excel(output_file, index=False)

print(f"✅ Excel file '{output_file}' created successfully.")
