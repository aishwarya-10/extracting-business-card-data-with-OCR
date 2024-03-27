# Import Libraries
#[Image Processing]
import easyocr
import cv2

#[Data Store]
import sqlite3

#[Data Transformation]
import pandas as pd
import re
import base64

#[Dashboard]
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

# Streamlit Page Configuration
st.set_page_config(
    page_title = "Biz-Card-OCR",
    page_icon= "Images/title_icon.png",
    layout = "centered",
    initial_sidebar_state= "expanded"
    )

# Title
# st.markdown("# :blue[BizCardX] :gray[Effortlessly Extract Business Card Data with OCR]", unsafe_allow_html=True)
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

st.subheader("Upload the Business Card")
# User business card
st.write("Try BizcardX with a simple drag-and-drop.")
uploaded_image = st.file_uploader("Choose an image file", type=["png", "jpg", "jpeg"])

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
uploaded_image = None
for button_text, image_path in buttons:
    with (col1 if buttons.index((button_text, image_path)) % 3 == 0 else
        (col2 if buttons.index((button_text, image_path)) % 3 == 1 else col3)):
        if st.button(button_text):
            uploaded_image = image_path


# Connect to SQL DB
connection = sqlite3.connect("business_card.db")
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
    # data["Address"] = [", ".join(addr) if isinstance(addr, list) else addr for addr in data["Address"]]
    data["Address"] = ", ".join(data["Address"])   
    # Transform dict to dataframe
    df = pd.DataFrame(data, columns=["Company Name", "Name", "Designation", "Ph. Number", "MailID", "Website", "Address", "State", "Pincode", "Image"])
    return card_text, df


def bounding_box(results, img_rgb):
    # Getting the coordinates
    for i in range(len(results)):
        top_left = tuple(results[i][0][0])
        bottom_right = tuple(results[i][0][2])
        text = results[i][1]
        font = cv2.FONT_HERSHEY_SIMPLEX

        img = cv2.rectangle(img_rgb,top_left,bottom_right,(0,255,0),3)
        # img = cv2.putText(img, text, top_left, font, 1, (50,200,255), 2, cv2.LINE_AA)
    display(img)

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
            to_sql = st.button("Store the Data", key="store")

        if to_sql:
            try:
                # Insert business card details
                data_tosql = "INSERT INTO bizcard (CompanyName, Name, Designation, PhNumber, MailID, Website, Address, State, Pincode, Image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

                for i in range(len(card_df)):
                    cur.execute(data_tosql, tuple(card_df.iloc[i]))
                    connection.commit()
                st.success("The card details are stored successfully.")
            except Exception as e:
                st.error("Error: ", e)

# View, Modify and Delete
# Query the SQL data
st.subheader(":violet[View Business Card Details]")

# Connect to SQL database
try:
    connection = sqlite3.connect("business_card.db")
    cur = connection.cursor()
except:
    print('Database connection could not be established.')

# Initial value for session state
if "selectbox_enabled" not in st.session_state:
    st.session_state["selectbox_enabled"] = False

def execute_query(selected_option: str):
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
    image_data = query_result2[0]     # the image data in the first element
    encoded_image = base64.b64encode(image_data).decode("utf-8")    # Encode binary data to Base64 string
    data_uri = f"data:image/png;base64,{encoded_image}"     # Construct data URI with Base64 encoded image and PNG mimetype
    
    return query_df, data_uri


# To get list of uploaded business card holder name
cur.execute("SELECT Name FROM bizcard")
companies = cur.fetchall()
df = pd.DataFrame(companies, columns= ["Name"])
options = df["Name"].to_list()

# To select a card
selected_option = st.selectbox("Select a Card Holder Name to view",
                               options,
                               index=None,
                               placeholder="To view card details...",
                               key= "view-card")
if selected_option:
    st.session_state["selectbox_enabled"] = True
    query_df, data_uri= execute_query(selected_option)
    col1, col2 = st.columns(2)
    with col1:
            st.dataframe(query_df)
    with col2:
            st.image(data_uri, width= 500)


    # Modify card
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

    if modify_sql:
        # Display all the card details
        CompanyName = st.text_input("CompanyName", query_df.iloc[0, 0])
        Name = st.text_input("Name", query_df.iloc[0, 1])
        Designation = st.text_input("Designation", query_df.iloc[0, 2])
        PhNumber = st.text_input("PhNumber", query_df.iloc[0, 3])
        MailID = st.text_input("MailID", query_df.iloc[0, 4])
        Website = st.text_input("Website", query_df.iloc[0, 5])
        Address = st.text_input("Address", query_df.iloc[0, 6])
        State = st.text_input("State", query_df.iloc[0, 7])
        Pincode = st.text_input("Pincode", query_df.iloc[0, 8])
                             

        if st.button("Update Changes", key="update"):
            # Update the details for the selected business card in the database
            cur.execute("""UPDATE bizcard SET CompanyName=%s,Name=%s,Designation=%s,PhNumber=%s,MailID=%s,Website=%s,Address=%s,State=%s,Pincode=%s
                        WHERE Name=%s""", (CompanyName,Name,Designation,PhNumber,MailID,Website,Address,State,Pincode,selected_option))
            connection.commit()
            st.success("The card details are updated successfully.")

    # Delete card
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

    if delete_sql:
        cur.execute(f"DELETE FROM bizcard WHERE Name = '{selected_option}' ")
        connection.commit()
        st.success("The card details are deleted successfully.")





# cd extracting-business-card-data-with-OCR
# streamlit run biz_card.py