# ==================================================       /     IMPORT LIBRARY    /      =================================================== #
#[Image Processing]
import easyocr
import cv2

#[Data Store]
import sqlite3
import os
import platform

#[Data Transformation]
import pandas as pd
import re
import base64

#[Dashboard]
import streamlit as st
from streamlit_extras.stylable_container import stylable_container


# ==================================================       /     CUSTOMIZATION    /      =================================================== #
# Streamlit Page Configuration
st.set_page_config(
    page_title = "Biz-Card-OCR",
    page_icon= "Images/title_icon.png",
    layout = "centered",
    initial_sidebar_state= "expanded"
    )

# Title
st.title(":blue[BizCardX] :gray[| OCR]")

# Steps to use application
container = st.container()
st.subheader("Effortlessly Extract Business Card Data with OCR")
col1, col2 = st.columns(2)
# Column 1: Illustraion
with col1:
    st.image("Images/steps.png", width=300, use_column_width=True)

# Column 2: Description
with col2:
    custom_css = """
                <style>
                ol {
                    list-style-type: none;
                    padding-left: 0;
                }
                li::marker {
                    content: "✔";
                    color: #007bff;
                    font-size: 20px;
                }
                </style>
                """
    st.markdown(custom_css, unsafe_allow_html=True)

    st.markdown("""
                **Here's how to get started in just a few steps:**
                1. Take a clear picture of the business card and upload it.
                2. BizCardX will automatically extract the data using OCR.
                3. View, Modify, or Delete the extracted info.
                """)


# ==============================================       /     UPLOAD BUSINESS CARD    /      ============================================ #
st.subheader("Upload the Business Card")
# User business card
st.write("Try BizcardX with a simple drag-and-drop.")
uploaded_image = None
uploads = st.file_uploader("Choose an image file", 
                                  type=["png", "jpg", "jpeg"], 
                                  accept_multiple_files=False, 
                                  key="images")
if uploads:
    def save_card(uploads):
        with open(os.path.join("uploaded_cards", uploads.name), "wb") as f:
            f.write(uploads.getbuffer())   
    save_card(uploads)

    # Get Image
    if platform.system() == "Linux":
        uploaded_image = os.getcwd()+ "/" + "uploaded_cards"+ "/"+ uploads.name
    elif platform.system() == "Darwin":   ## Mac os
        uploaded_image = os.getcwd()+ "\/" + "uploaded_cards"+ "\/"+ uploads.name
    if platform.system() == "Windows":
        uploaded_image = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploads.name


# Sample business card
st.write("Don't have a business card? Try one of our sample.")
# Define button labels and corresponding image paths
buttons = [
    (":spiral_calendar_pad: Selva Digitals", "Data/1.png"),
    (":spiral_calendar_pad: Global Insurance", "Data/2.png"),
    (":spiral_calendar_pad: Borcelle Airlines", "Data/3.png"),
    (":spiral_calendar_pad: Family Restaurant", "Data/4.png"),
    (":spiral_calendar_pad: Sun Electricals", "Data/5.png"),
]

# Create a 2x3 grid layout using columns
col1, col2, col3 = st.columns(3)

# Iterate through buttons and create them with grid placement

for button_text, image_path in buttons:
    with (col1 if buttons.index((button_text, image_path)) % 3 == 0 else
        (col2 if buttons.index((button_text, image_path)) % 3 == 1 else col3)):
        if st.button(button_text):
            uploaded_image = image_path


# Connect to SQL DB
connection = sqlite3.connect("business_card.db", check_same_thread=False)
cur = connection.cursor()

# Create table for uploading business card details
cur.execute("""CREATE TABLE IF NOT EXISTS bizcard(
            CompanyName VARCHAR(255),
            Name VARCHAR(255),
            Designation VARCHAR(255),
            PhNumber INT,
            MailID VARCHAR(50),
            Website VARCHAR(255),
            Address VARCHAR(255),
            State VARCHAR(50),
            Pincode INT,
            Image LONGBLOB
            )""")
cur.close()
connection.commit()


def read_text(uploaded_image):
    # Load the image
    img = cv2.imread(uploaded_image)
    # Convert to True color and Gray-scale
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    # Load the OCR language
    reader = easyocr.Reader(["en"], gpu=False)
    results = reader.readtext(img, detail=1, paragraph=False, decoder="beamsearch")
    return img_rgb, results


def binary_image(img_path):
    with open(img_path, "rb") as b:
        image_data = b.read()
    return image_data


def display(image):
    st.image(image, use_column_width= True)


def transform_data(results, uploaded_image):
    # Get text data from OCR
    card_text = []
    for bbox, text, confidence in results:
        card_text.append(text)

    data = {
        "Company Name": [],
        "Name": [],
        "Designation": [],
        "Ph. Number": [],
        "MailID": [],
        "Website": [],
        "Address": [],
        "State": [],
        "Pincode": [],
        "Image": binary_image(uploaded_image)
    }

    # Recognize card details and store in dict
    for index, i in enumerate(card_text):  
        match = re.search(r"(\w+)\s+(\d{6,7})$", i)
        # Recognize Name
        if index == 0:
            data["Name"].append(i)
        
        # Recognize Designation
        elif index == 1:
            data["Designation"].append(i)

        # Recognize Phone Number
        elif "-" in i:
            data["Ph. Number"].append(i)
        
        # Recognize Mail-ID
        elif "@" in i:
            data["MailID"].append(i)
        
        # Recognize website
        elif re.findall(r"^www", i, flags = re.IGNORECASE):
        # ("WWW" or "www" or "Www") in i:
            data["Website"].append((i[:3].lower()) + "." + i[4:])
        
        # Recognize Pincode
        elif re.findall(r"^\d{6,7}", i):
            data["Pincode"].append(i)

        # Recognize State
        elif match:
            data["State"].append(match.group(1))
            data["Pincode"].append(match.group(2))

        # Recognize address
        elif re.findall(r"\d+\s*\w+", i):
            tokens = i.split(", ")
            if len(tokens) == 3:
                match2 = re.search(r"\w+\s*[,;.]$", i)
                data["State"].append(match2.group())
                data["Address"].append(i)
            elif len(tokens) == 2:
                data["Address"].append(i)
                
        # Recognize Company Name
        else:
            data["Company Name"].append(i)
 
    data["Company Name"] = " ".join(str(j).capitalize() for j in data["Company Name"])
    data["Designation"] = [str(j).title() for j in data["Designation"]]
    data["Ph. Number"] = ", ".join(data["Ph. Number"])
    data["Address"] = ", ".join(data["Address"])   

    # Transform dict to dataframe
    df = pd.DataFrame(data, columns=["Company Name", "Name", "Designation", "Ph. Number", "MailID", "Website", "Address", "State", "Pincode", "Image"])
    return card_text, df


def bounding_box(results, img_rgb):
    # Getting the coordinates
    for i in range(len(results)):
        top_left = tuple(results[i][0][0])
        bottom_right = tuple(results[i][0][2])
        # text = results[i][1]
        # font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Convert to integers (rounding or casting)
        top_left = (int(round(top_left[0])), int(round(top_left[1])))
        bottom_right = (int(round(bottom_right[0])), int(round(bottom_right[1])))

        img = cv2.rectangle(img_rgb,top_left,bottom_right,(0,255,0),3)
        # img = cv2.putText(img, text, top_left, font, 1, (50,200,255), 2, cv2.LINE_AA)
    display(img)


def insert_data():
    # st.session_state.clicked = True
    try:
        connection = sqlite3.connect("business_card.db")
        cur = connection.cursor()
        # Insert business card details
        data_tosql = "INSERT INTO bizcard (CompanyName, Name, Designation, PhNumber, MailID, Website, Address, State, Pincode, Image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

        with st.spinner("Storing data..."):
            for i in range(len(card_df)):
                cur.execute(data_tosql, tuple(card_df.iloc[i]))
        connection.commit()
        st.success("The card details are stored successfully.")

    except Exception as e:
        print(e)
        # st.error(f"An unexpected error occurred: {e}")


if uploaded_image is not None:
    st.success("The business card upload was successful!")
    with st.spinner("Reading text in the image..."):
        img_rgb, results = read_text(uploaded_image)
        card_text, card_df = transform_data(results, uploaded_image)

        col1, col2 = st.columns(2)
        # Column 1: Bounding box on detections
        with col1:
            with st.expander("Preview"):
                bounding_box(results, img_rgb)
        # Column 2: Text Detected
        with col2:
            tabs = st.tabs(["Detected Attributes", "Table"])

            with tabs[0]:
                for i in card_text:
                    st.write(i)
            with tabs[1]:
                st.dataframe(card_df[["Company Name", "Name", "Designation", "Ph. Number", "MailID", "Website", "Address", "State", "Pincode"]].T)

            css = '''
            <style>
                .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
                font-size:1rem;
                }
            </style>
            '''
            st.markdown(css, unsafe_allow_html=True)  

    # Data to SQL DB
    with stylable_container(
        key="blue_button",
        css_styles="""
            button {
                background-color: blue;
                color: black;
                border-radius: 20px;
                background-image: linear-gradient(90deg, #89f7fe 0%, #66a6ff 100%);
            }
            """,
    ):
        to_sql = st.button("Store the Data", key="store", on_click=insert_data)
st.write("")

# =======================================       /     MODIFY AND DELETE    /      ========================================= #
st.subheader("Modify/Delete Business Card")

# Connect to SQL database
try:
    connection = sqlite3.connect("business_card.db")
except:
    print('Database connection could not be established.')


def execute_query(selected_option: str):
    cur = connection.cursor()
    # Card details
    cur.execute(f"""SELECT CompanyName, Name, Designation, PhNumber, MailID, Website, Address, State, Pincode FROM bizcard
                WHERE Name = "{selected_option}" """)
    query_result1 = cur.fetchall()
    column_names = ["Company Name", "Name", "Designation", "Ph. Number", "Mail ID", "Website", "Address", "State", "Pincode"]
    query_df = pd.DataFrame(query_result1, columns= column_names).reset_index(drop=True)

    # Card Image
    cur.execute(f"""SELECT Image FROM bizcard
                WHERE Name = "{selected_option}" """)
    query_result2 = cur.fetchone()
    image_data = query_result2[0]     # The image data in the first element
    encoded_image = base64.b64encode(image_data).decode("utf-8")    # Encode binary data to Base64 string
    data_uri = f"data:image/png;base64,{encoded_image}"     # Construct data URI with Base64 encoded image and PNG mimetype
    
    return query_df, data_uri


col1, col2 = st.columns(2)
# Column 1: Modify card
with col1:
    with stylable_container(
        key="green_button",
        css_styles="""
            button {
                background-color: green;
                color: black;
                border-radius: 20px;
                background-image: linear-gradient(90deg, #dce35b 0%, #45b649 100%);
            }
            """,
    ):
        modify_sql = st.button("Modify the Data", key="modify")

    if modify_sql or ('modify_status' in st.session_state):
        # To get list of uploaded business card holder name
        cur = connection.cursor()
        cur.execute("SELECT Name FROM bizcard")
        result = cur.fetchall()
        business_cards = {}
        for row in result:
            business_cards[row[0]] = row[0]

        st.session_state.modify_status = True

        selected_card = st.selectbox("Select a Card Holder Name to update", 
                                     list(business_cards.keys()),
                                     index= None,
                                     placeholder="To modify card details...",
                                     key= "S_update")
        if selected_card:
            st.markdown(":orange[Edit any data below]")
            cur.execute(f"""select CompanyName,Name,Designation,PhNumber,MailID,Website,Address,State,Pincode from bizcard WHERE Name="{selected_card}" """)
            result = cur.fetchone()

            # Display all the card details
            CompanyName = st.text_input("CompanyName", result[0])
            Name = st.text_input("Name", result[1])
            Designation = st.text_input("Designation", result[2])
            PhNumber = st.text_input("PhNumber", result[3])
            MailID = st.text_input("MailID", result[4])
            Website = st.text_input("Website", result[5])
            Address = st.text_input("Address", result[6])
            State = st.text_input("State", result[7])
            Pincode = st.text_input("Pincode", result[8])

            with stylable_container(
                key="save_button",
                css_styles="""
                    button {
                        background-color: white;
                        color: green;
                        border-radius: 20px;
                    }
                    """,
            ):
                save_sql = st.button("Update Changes", key="save")

            if save_sql:
                if 'modify_status' in st.session_state:
                    del st.session_state.modify_status
                # Update the information for the selected business card in the database
                cur.execute("""UPDATE bizcard SET CompanyName=?,Name=?,Designation=?,PhNumber=?,MailID=?,Website=?,Address=?,State=?,Pincode=?
                                    WHERE Name=?""", (CompanyName,Name,Designation,PhNumber,MailID,Website,Address,State,Pincode,selected_card))
                connection.commit()
                st.success("Card details updated successfully.")

# Column 2: Delete card
with col2:
    with stylable_container(
    key="red_button",
    css_styles="""
        button {
            background-color: red;
            color: black;
            border-radius: 20px;
            background-image: linear-gradient(90deg, #ff9966 0%, #ff5e62 100%);
        }
        """,
    ):
        delete_sql = st.button("Delete the Data", key="delete")

    if delete_sql or ('delete_status' in st.session_state):
        cur = connection.cursor()
        cur.execute("SELECT Name FROM bizcard")
        result = cur.fetchall()
        business_cards = {}
        for row in result:
            business_cards[row[0]] = row[0]

        st.session_state.delete_status = True

        selected_card = st.selectbox("Select a Card Holder Name to Delete", 
                                     list(business_cards.keys()),
                                     index= None,
                                     placeholder="To delete card details...",
                                     key= "S_delete")
        if selected_card:
            st.write(f"You have selected {selected_card} card to delete")
            st.write("Proceed to delete?")

            with stylable_container(
                key="confirm_button",
                css_styles="""
                    button {
                        background-color: white;
                        color: red;
                        border-radius: 20px;
                    }
                    """,
            ):
                confirm_sql = st.button("Confirm", key="confirm")

            if confirm_sql:
                if 'delete_status' in st.session_state:
                    del st.session_state.delete_status
                cur = connection.cursor()
                cur.execute(f"DELETE FROM bizcard WHERE Name = '{selected_card}' ")
                connection.commit()
                st.success("The business card is deleted successfully.")


# =======================================       /     VIEW DATA    /      ========================================= #
st.write("")

# Define CSS styles for the expander
st.markdown(
        """
        <style>
        .st-emotion-cache-0 p {
            font-size: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
with st.expander("View Business Card Details"):
    connection = sqlite3.connect("business_card.db")
    cur = connection.cursor()
    cur.execute("select CompanyName,Name,Designation,PhNumber,MailID,Website,Address,State,Pincode from bizcard")
    updated_df = pd.DataFrame(cur.fetchall(),columns=["Company Name", "Name", "Designation", "Ph. Number", "Mail ID", "Website", "Address", "State", "Pincode"])
    st.write(updated_df)

# cd Projects\Project_3\git_project3\extracting-business-card-data-with-OCR
# streamlit run biz_card.py