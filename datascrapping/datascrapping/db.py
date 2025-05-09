import MySQLdb
import pandas as pd
db = MySQLdb.connect(host='localhost',user='root',passwd='pass',database='whatsapp_post_data')

# cursor = db.cursor()
# cursor.execute("""SELECT * FROM insta_reels""")
# result = cursor.fetchall()
# for i in result:print(i)

excel_file_path = fr"C:\Users\admin\Desktop\ITG_Project_WA\Web Scraping Project\ITG\Scraping\JUNE 01 - 31 HINDI CATEGORISED_Ready.xlsx"

cursor = db.cursor()

df = pd.read_excel(excel_file_path)

if 'Unnamed: 0' in df.columns:
    df = df.drop(columns=['Unnamed: 0'])


table_name = 'whatsapp_data_categorised'

df = df.fillna({
    'Date': '1970-01-01',          # Default date for missing values
    'Time': '00:00:00',            # Default time
    'Channel': '',                 # Empty string for text columns
    'Chn_Language': '',
    'Post_Content': '',
    'Links': '',
    'Category': '',
    'Engagement': 0,               # Default value for numeric columns
    'Poll': '',
    'Poll_Response': 0,
    'Total_Poll_Reaction': 0
})

# Debugging step to verify no NaN values remain
nan_rows = df[df.isna().any(axis=1)]
if not nan_rows.empty:
    print("Rows with NaN values after replacement:")
    print(nan_rows)
else:
    print("No NaN values remain in the data.")


# Inserting data into MySQL table
for _, row in df.iterrows():
    # Enclose column names in backticks
    insert_data_query = f"INSERT INTO {table_name} (`{('`, `'.join(df.columns))}`) VALUES ({', '.join(['%s'] * len(df.columns))})"
    cursor.execute(insert_data_query, tuple(row))
# Save changes
db.commit()
print("Data imported successfully!")

