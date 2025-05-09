############################################################### Importing Libraries ##############################################################
import os
import cv2
import glob
import shutil
import pandas as pd
from tqdm import tqdm
from whatsapp_api_client_python import API
###################################################################################################################################################

# Make Output directories
shutil.rmtree('../Output_Screen_Grab_TV/', ignore_errors=True)
if not os.path.exists(f"../Output_Screen_Grab_TV"):
    os.makedirs(f"../Output_Screen_Grab_TV")

# WhatsApp Green API Instance_ID and API_TOKEN_KEY
ID_INSTANCE = '7103959203'
API_TOKEN_INSTANCE = 'a46ef9b8ad364916a64640e5ae0d1a108fe065b556f848cdb2'

# Instantiating Green API instance
greenAPI = API.GreenApi(ID_INSTANCE, API_TOKEN_INSTANCE)

###############################################################  Defining Functions  ################################################################

# Function to extract frame from Videos at the interval of 30 secs


def extract_frames(video_path, output_path, interval=30):

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Initialize variables
    frame_count = 0
    success = True

    # Set video capture position to start
    cap.set(cv2.CAP_PROP_POS_MSEC, 0)

    # Read the first frame
    success, image = cap.read()

    # Loop through the video
    while success:
        # Calculate the current time (in seconds)
        current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000

        # If the current time is a multiple of the interval, save the frame
        if current_time >= frame_count * interval:
            frame_name = str(video_path.split(
                '.')[-2].split('\\')[-1]) + f"frame_{frame_count}.jpg"
            cv2.imwrite(output_path + frame_name, image)

            frame_count += 1

            # #Nilotpal Kumar for Testing
            # result = greenAPI.sending.sendFileByUpload('918178139556@c.us',
            #     output_path + frame_name,
            #     output_path + frame_name, "")
            # print(result.data)

            # SPAR Group
            result = greenAPI.sending.sendFileByUpload('120363253506759351@g.us',
                                                       output_path + frame_name,
                                                       output_path + frame_name, "")
            print(result.data)
            print('???????????????????????', output_path + frame_name)

        # Read the next frame
        success, image = cap.read()

    # Release the video capture object
    cap.release()

###################################################################################################################################################

# Function to Generate the filenames for the 30 mins interval from start_time


def generate_file_names(file_path):

    # Extract the path without the filename
    path = os.path.dirname(file_path)
    # print("?????????????????? PATH : ", path)

    # Extract the filename
    filename = os.path.basename(file_path)

    # Split the filename to extract the relevant parts
    parts = filename.split('_')

    prefix = '_'.join(parts[0:3])  # '1_TS-15_202'

    # Extracting start and end times
    start_time = parts[3]  # '0200' from '202409070200'
    end_time = parts[4]    # '0230' from '202409070230'

    mid_times = [str(int(start_time) + i)
                 for i in range(31)]  # Generates mid_time1 to mid_time30

    # List to collect video file_names
    file_names = []

    for i in range(30):  # Generate 30 filenames
        file_name = f"{prefix}_{mid_times[i]}_{mid_times[i+1]}.mp4"
        full_file_path = os.path.join(path, file_name)
        file_names.append(full_file_path)

    return file_names

###################################################################################################################################################

# Function to get filenames from dataframe and channel name


def get_filename(df, channel_name):

    # Path to the logger final folder location
    path = "\\\\10.10.7.222\\Media\\LowRess\\"

    # Dictionary for Channel name and its folder location along with full path in logger
    port_dict = {
        "Aaj Tak-HSM15+": str(path) + "1_TS-7_1",
        "ABP News-HSM15+": str(path) + "1_TS-13_203",
        "TV9 Bharatvarsh-HSM15+": str(path) + "1_TS-18_335",
        "India TV-HSM15+": str(path) + "1_TS-14_201",
        "Zee News-HSM15+": str(path) + "1_TS-25_204",
        "Times Now Navbharat-HSM15+": str(path) + "1_TS-16_207",
        "Republic Bharat-HSM15+": str(path) + "1_TS-17_2163",
        "News18 India-HSM15+": str(path) + "1_TS-15_202",
        "Tez-HSM15+": "Logger02Port02",
        "NDTV India-HSM15+": str(path) + "1_TS-19_205",
        "India Today Television - Meg-22+ M AB": str(path) + "1_TS-8_2",
        "Republic TV - Meg-22+ M AB": str(path) + "1_TS-20_23",
        "Times Now - Meg-22+ M AB": str(path) + "1_TS-24_301",
        "CNN News18 - Meg-22+ M AB": str(path) + "1_TS-23_302"
    }

    # Dictionary for Channel name and its folder location in logger
    portname_dict = {
        "Aaj Tak-HSM15+": "1_TS-7_1",
        "ABP News-HSM15+": "1_TS-13_203",
        "TV9 Bharatvarsh-HSM15+":  "1_TS-18_335",
        "India TV-HSM15+": "1_TS-14_201",
        "Zee News-HSM15+": "1_TS-25_204",
        "Times Now Navbharat-HSM15+": "1_TS-16_207",
        "Republic Bharat-HSM15+": "1_TS-17_2163",
        "News18 India-HSM15+": "1_TS-15_202",
        "Tez-HSM15+": "Logger02Port02",
        "NDTV India-HSM15+":  "1_TS-19_205",
        "India Today Television - Meg-22+ M AB": "1_TS-8_2",
        "Republic TV - Meg-22+ M AB": "1_TS-20_23",
        "Times Now - Meg-22+ M AB": "1_TS-24_301",
        "CNN News18 - Meg-22+ M AB": "1_TS-23_302"
    }

    # Remove unnecessay column
    try:
        df.drop("Unnamed: 0", axis=1, inplace=True)
    except:
        print("file error")

    # Convert the 'Date' column to datetime format
    df['Date'] = pd.to_datetime(df['Date'])

    # remove the trailing and leading spaces in Time from and Time to columns
    df["Time_From"] = df["Time_From"].str.strip()
    df["Time_To"] = df["Time_To"].str.strip()

    # Create a new column 'filename' with path and YearMonthDay from Date
    df['filename'] = str(portname_dict[channel_name])
    df['filename'] = df['filename'] + '_' + df['Date'].dt.strftime('%Y%m%d')

    # Append hours and minutes from 'Time_From' to 'filename'
    df['filename'] = df['filename'] + \
        df['Time_From'].str.replace(':', '').str[:4]

    # Append '_' and YearMonthDay from 'Date' to 'filename'
    df['filename'] = df['filename'] + "_" + df['Date'].dt.strftime('%Y%m%d')
    df['filename'] = df['filename'] + \
        df['Time_To'].str.replace(':', '').str[:4]

    # Variable for storing 'Time_From' as string
    time_from = df['Time_From'].str.replace(':', '').str[:4]

    # Extract hour from time_from
    hour = time_from.str[0:2]

    # Add new column hour in the df
    df["Hour"] = hour

    # Add new column folder with YearMonthDay from Date '_' hour
    df["folder"] = df['Date'].dt.strftime('%Y%m%d')+"_" + df["Hour"]

    # Prefix 'Logger' to 'filename'
    df['filename'] = str(port_dict[channel_name]) + '\\' + \
        df["folder"] + '\\' + + df['filename'] + ".mp4"

###################################################################################################################################################

# Function to Start the process with language of the channel as input


def arr(lang):

    if language == "English":
        src_path = "../Input Files/Helper/English"
        all_csv = glob.glob(src_path+"/*.csv")
    if language == "Hindi":
        src_path = "../Input Files/Helper/Hindi"
        all_csv = glob.glob(src_path+"/*.csv")

    path = "\\\\10.10.7.222\\Media\\LowRess\\"

    port_dict = {
        "Aaj Tak-HSM15+": str(path) + "1_TS-7_1",
        "ABP News-HSM15+": str(path) + "1_TS-13_203",
        "TV9 Bharatvarsh-HSM15+": str(path) + "1_TS-18_335",
        "India TV-HSM15+": str(path) + "1_TS-14_201",
        "Zee News-HSM15+": str(path) + "1_TS-25_204",
        "Times Now Navbharat-HSM15+": str(path) + "1_TS-16_207",
        "Republic Bharat-HSM15+": str(path) + "1_TS-17_2163",
        "News18 India-HSM15+": str(path) + "1_TS-15_202",
        "Tez-HSM15+": "Logger02Port02",
        "NDTV India-HSM15+": str(path) + "1_TS-19_205",
        "India Today Television - Meg-22+ M AB": str(path) + "1_TS-8_2",
        "Republic TV - Meg-22+ M AB": str(path) + "1_TS-20_23",
        "Times Now - Meg-22+ M AB": str(path) + "1_TS-24_301",
        "CNN News18 - Meg-22+ M AB": str(path) + "1_TS-23_302"
    }

    for top_list in (all_csv):
        df = pd.read_csv(top_list)

        if language == "Hindi":

            if "1" in top_list:
                channel_name = df.columns[-5]
            if "2" in top_list:
                channel_name = df.columns[-4]
            if "3" in top_list:
                channel_name = df.columns[-3]
            if "4" in top_list:
                channel_name = df.columns[-2]
            if "5" in top_list:
                channel_name = df.columns[-1]
        elif language == "English":

            if "1" in top_list:
                channel_name = df.columns[-4]
            if "2" in top_list:
                channel_name = df.columns[-3]
            if "3" in top_list:
                channel_name = df.columns[-2]
            if "4" in top_list:
                channel_name = df.columns[-1]

        print(channel_name)

        # import pdb;pdb.set_trace()
        get_filename(df, channel_name)
        try:
            for index, row in tqdm(df.iterrows()):
                new = str(row)
                text = new  # [4:-91]
                print(text)
                print('..................', row[6:-1])
                text1 = '''
==================================
|           Infromation TV Data Week !            |
==================================

Year >>>>  ''' + str(row['Year']) + '''
Date >>>>  ''' + str(row['Date']).replace(' 00:00:00', '') + '''
Week >>>>  ''' + str(row['Week']) + '''
Day  >>>>  ''' + str(row['Day']) + '''
Time Band >>>> ''' + str(row['Time_From']) + '''--''' + str(row['Time_To']) + '''

==================================
|                             Rating !                              |
==================================

''' + str(row[6:-3].sort_values(ascending=False)).replace('Name: 0, dtype: object', '') + '''

==================================

NOTE: Currently ''' + str(channel_name)+''' Shanpshot is Sharing of This Time Band : ''' + str(row['Time_From']) + '''--''' + str(row['Time_To']) + ''' 
Current Model  : XG BOOST
Current Target : 15+ All
==================================
'''
                # import pdb;pdb.set_trace()
                send_df = pd.DataFrame(row).T.drop('filename', axis=1)
                send_df['Channel_Image_Attachment'] = 'Currently Img of ' + \
                    str(channel_name)
                import plotly.graph_objects as go
                import plotly.io as pio
                fig = go.Figure(data=[go.Table(header=dict(values=list(send_df.columns), line_color='darkslategray', fill_color='lightgreen', align=['center'], font=dict(
                    color='black', size=16, family='Arial')), cells=dict(values=send_df.transpose().values.tolist(), format=[".2s"], line_color='darkslategray', fill_color='white', align=['center']))])

                pio.write_image(fig, channel_name +
                                'MarketShare.png', width=2180, height=400)

                # result = greenAPI.sending.sendMessage('918178139556@c.us',text1) #Nilotpal Number

                result = greenAPI.sending.sendMessage(
                    '120363253506759351@g.us', text1)  # ITGGROUP
                response = greenAPI.sending.sendFileByUpload(
                    "918178139556@c.us", channel_name + 'MarketShare.png', channel_name + 'MarketShare.png', '')

                # send_Whatsapp(text)
                original_file_name = row['filename']
                original_file_name = row['filename']
                files = generate_file_names(original_file_name)

                channel_path = port_dict[channel_name]
                print('....................', channel_name)
                if not os.path.exists(f"../Output_Screen_Grab_TV/{channel_name}"):
                    os.makedirs(f"../Output_Screen_Grab_TV/{channel_name}")
                if channel_name == channel_name:
                    print(']]]]]]]]]]', channel_name, files)
                    output_path = (f"../Output_Screen_Grab_TV/{channel_name}/")
                    for i in files:
                        video_path = i
                        extract_frames(video_path, output_path)

        except:
            pass


################################################################   Process Init  ################################################################
# Loop through the Input files and grab the latest week file for processing
for i in sorted(glob.glob("../Input Files\\TV_Input_Files\\*.xlsx"), key=len):

    week = i.split('-')[-1].replace('.xlsx', '').strip().split("'")[0]
    year = (str(20) + i.split('-')[-1].replace('.xlsx',
            '').strip().split("'")[1]).replace('.', '').strip()
    language = i.split('Master ')[-1].split('_')[1]

    if language == "Hindi":
        data = pd.read_excel(i, sheet_name='VD NCT', skiprows=5)
    elif language == "English":
        data = pd.read_excel(i, sheet_name='NCT VD', skiprows=5)

    if language == "Hindi":
        data = data.iloc[:, :23]
    elif language == "English":
        data = data.iloc[:, :16]

    data = data[data["Year"] == int(year)]
    data = data[data["Week"] == int(week)]

    unique_weeks = data["Week"].unique()

    if language == "Hindi":
        data_refined_only_numbers = data.iloc[:, 7:23]
    elif language == "English":
        data_refined_only_numbers = data.iloc[:, 7:16]

    # Identify the channel columns from data_refined_columns
    channel_columns = [col for col in data_refined_only_numbers.columns]
    print(channel_columns)

    # Convert these columns to numeric type (they are currently object type)
    data[channel_columns] = data[channel_columns].apply(
        pd.to_numeric, errors='coerce')

    # Create a new dataframe with the sum of each channel
    channel_sums = data[channel_columns].sum().sort_values(ascending=False)

    # Select the first 6 columns
    first_six_columns = data.iloc[:, :6]

    # Select the top channels based on language
    if language == "Hindi":
        num_top_channels = 5
        top_channels = channel_sums.index[:num_top_channels].tolist()

    elif language == "English":

        english_channels = ["India Today Television - Meg-22+ M AB",
                            "Republic TV - Meg-22+ M AB", "CNN News18 - Meg-22+ M AB", "Times Now - Meg-22+ M AB"]

        # Filter the channels based on the defined English channels
        top_channels = [
            channel for channel in english_channels if channel in channel_sums.index]

    # Arrange the selected English channels in descending order
    top_channels_ordered = sorted(
        top_channels, key=lambda channel: channel_sums[channel], reverse=True)

    # Create a new dataframe combining the first six columns and the top English channels
    new_df = pd.concat([first_six_columns, data[top_channels_ordered]], axis=1)

    # Loop through the top English channels and generate CSV files
    for rank, top_channel in enumerate(top_channels_ordered, start=1):

        rank_suffix = 'st' if rank == 1 else 'nd' if rank == 2 else 'rd' if rank == 3 else 'th'

        top_20_rows = new_df.sort_values(
            by=top_channel, ascending=False).head(20)
        if language == "English":
            top_20_rows.to_csv(
                f"../Input Files/Helper/English/{rank}{rank_suffix}{language}.csv")
        if language == "Hindi":
            top_20_rows.to_csv(
                f"../Input Files/Helper/Hindi/{rank}{rank_suffix}{language}.csv")

    arr(language)
