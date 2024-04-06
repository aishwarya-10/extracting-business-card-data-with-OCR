# BizCardX - Extracting Business Card Data with OCR
This provides a user interface for extracting business card information with easyOCR and Streamlit.

[**Click here to view the app**]() 

[**Project Demo**](https://www.linkedin.com/posts/aishwarya-velmurugan_hi-everyone-im-excited-to-share-my-latest-activity-7181711151318138880-e6ko?utm_source=share&utm_medium=member_desktop)

<br>

# OCR
OCR or Optical Character Recognition is also referred to as text recognition or text extraction. This machine learning-based **easyOCR** technique allows users to extract printed or handwritten text from posters, cards, documents, etc. The text can be words, text lines or paragraphs enabling us to have a digital version of scanned text. This significantly eliminates manual entry. The OCR used here is by [**JAIDED AI**](https://github.com/JaidedAI/EasyOCR?tab=readme-ov-file).

<br>

# Workflow
## Step 1: Prerequisites
Install and Import the following libraries
- Python 3.x (https://www.python.org/downloads/)
- Streamlit (pip install streamlit)
- Streamlit option menu (pip install streamlit-option-menu)
- sqlite3 (pip install db-sqlite3)
- Pandas (pip install pandas)

<br>

## Step 2: Text Detection
- Using easyOCR all the text in the card is detected using the business card image.
```python
reader = easyocr.Reader(["en"], gpu=False)
results = reader.readtext(img, detail=1, paragraph=False, decoder="beamsearch")
```
- The detections are viewed by drawing a bounding box around the text with the text coordinates from the results.

<br>

## Step 3: Text Recognition
- The card details are recognized as a specific field using regular expression Python and stored in a pandas data frame.

<br>

## Step 4: Streamlit Dashboard
- The detected card details are stored in SQL DB for viewing, modifying, and deleting a stored card by the user.
- These functionalities are provided to the user with button input elements by streamlit.
- The web application is deployed for use by others.
