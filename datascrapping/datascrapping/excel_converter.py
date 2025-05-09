import datetime
import pandas as pd
import re

file_path=rf"C:\Users\admin\Downloads\AUG 01 - 31 HINDI CATEGORISED (1).xlsx"
# file_path=rf"C:\Users\rismo\Desktop\Web Scraping\India Today\Data Categorisation Model\WA_Jul27_Aug02__Eng_Categorised.xlsx"
# file_path=rf"C:\Users\rismo\Desktop\Web Scraping\India Today\Project2- Whatsapp Channels Data\BT\May\Whatsapp_Post_Data_BT_Jul_W5.xlsx"

orig_df = pd.read_excel(file_path)


orig_df.rename(columns={
    "Channel_Name": "Channel",
    "Channel_Language": "Chn_Language",
    "Post_Reaction": "Engagement",
    "Poll Responses": "Poll_Response",
    "Total Poll Reactions": "Total_Poll_Reaction"
}, inplace=True)


orig_df.drop(columns=["TimeStamp"], inplace=True)

col_order = ["Date", "Time", "Channel", "Chn_Language", "Post_Content", "Links", "Category", "Engagement", "Poll", "Poll_Response", "Total_Poll_Reaction"]
orig_df = orig_df[col_order]


orig_df["Date"] = pd.to_datetime(orig_df["Date"], format="mixed").dt.strftime("%Y-%m-%d")
#orig_df["Time"] = orig_df["Time"].apply(lambda x: f"{x}:00")

#*********E+H***********#

# def format_time(x):
#     if re.match(r'\d{2}:\d{2}:\d{2}', x):  # Check if time already contains seconds
#         return x
#     else:
#         return f"{x}:00"

#**********B************#

def format_time(x):
    if isinstance(x, datetime.time):
        return x.strftime("%H:%M:%S")
    elif isinstance(x, str):
        if re.match(r'\d{2}:\d{2}:\d{2}', x):  # Check if time already contains seconds
            return x
        else:
            return f"{x}:00"
    else:
        return x  # Return as is for other types

#***********************#

orig_df["Time"] = orig_df["Time"].apply(format_time)

# print(orig_df.head(30))
orig_df.to_excel("demo.xlsx", index=False)
print("Modification Succesfull !")



