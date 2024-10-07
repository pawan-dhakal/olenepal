import pandas as pd
import json
import streamlit as st
import base64
import requests

# change to True for offline server
for_offline_use = False 

# Helper function to convert image to base64
@st.cache_data
def get_base64_image(image_path):
    if image_path.startswith('http://') or image_path.startswith('https://'):
        response = requests.get(image_path)
        if response.status_code == 200:
            encoded_string = base64.b64encode(response.content).decode()
            return encoded_string
        else:
            raise FileNotFoundError(f"URL returned status code {response.status_code}: {image_path}")
    else:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string

# Read all content including additional content from the JSON file
if for_offline_use:
    df = pd.read_json('all_content_offline.json', orient='records')
else:
    df = pd.read_json('all_content_online.json', orient='records')

# Fill NaN values with empty strings
df = df.fillna('')


# Define label translations
labels = {
    "title": {"English": "Gradewise Learning 6-10", "Nepali": "कक्षागत सिकाइ ६-१०"},
    "search_filter": {"English": "Search and Filter", "Nepali": "खोज्‍नुहोस् र फिल्टर गर्नुहोस्"},
    "filter_instruction": {"English": "Use the filters below to navigate content", "Nepali": "तलका फिल्टरहरू प्रयोग गरी सामग्री खोज्‍नुहोस्"},
    "search_label": {"English": "Search within content:", "Nepali": "सामग्री खोज्‍नुहोस्:"},
    "select_grade": {"English": "Select Grade", "Nepali": "कक्षा छान्‍नुहोस्"},
    "select_subject": {"English": "Select Subject", "Nepali": "विषय छान्‍नुहोस्"},
    "select_chapter": {"English": "Select Chapter", "Nepali": "पाठ छान्‍नुहोस्"},
    "select_content_type": {"English": "Select Content Type", "Nepali": "सामग्रीको प्रकार छान्‍नुहोस्"},
    "select_content_source": {"English": "Select Content Source", "Nepali": "सामग्रीको स्रोत छान्‍नुहोस्"},
    "select_view_text": {"English": "Select View", "Nepali": "सामग्री हेर्ने तरिका छान्‍नुहोस्"},
    "total_content": {"English": "Total Content", "Nepali": "जम्मा सामग्री"},
    "displayed_label": {"English": "Displayed", "Nepali": "देखाइएको"},
    "download_data": {"English": "Download data as CSV", "Nepali": "CSV को रूपमा डेटा डाउनलोड गर्नुहोस्"},
    "load_more": {"English": "Load more content", "Nepali": "थप सामग्री लोड गर्नुहोस्"},
    "search_btn_text": {"English": "Search", "Nepali": "खोज्‍नुहोस्"},
    "reset_btn_text": {"English": "Reset", "Nepali": "रिसेट गर्नुहोस्"},
    "browse_lang_text": {"English": "Select Language to Browse Content", "Nepali": "सामग्री खोज्‍ने भाषा छान्‍नुहोस्"},
    "card_view_label": {"English": "Card View", "Nepali": "सामग्रीको कार्ड सूची"},
    "table_view_label": {"English": "Table View", "Nepali": "सामग्रीको तालिका सूची"},
    "grade_text_only": {"English": "Grade", "Nepali": "कक्षा"},
    "all_text" : {"English": "All", "Nepali": "सबै"},
    "choose_an_option" : {"English": "Choose an option", "Nepali": "विकल्प छान्‍नुहोस्"},
    "learn_now_text" : {"English": "Learn now >>", "Nepali": "सिकौँ >>"},
}

# Define content type and source translations
content_type_source_labels = {
    "document": {"English":"Document","Nepali":"किताब"},
    "video": {"English":"Video","Nepali":"भिडियो"},
    "audio": {"English":"Audio","Nepali":"अडियो"},
    "interactive": {"English":"Interactive","Nepali":"अन्तर्क्रियात्मक"},
    "Textbook": {"English":"Textbook","Nepali":"पाठ्यपुस्तक"},
    "E-Paath": {"English":"E-Paath","Nepali":"ई-पाठ"},
    "Nepali and English Listening Clips": {"English":"Nepali and English Listening Clips","Nepali":"नेपाली र अंग्रेजी अडियो क्लिपहरू"},
    "Teaching Video": {"English":"Teaching Video","Nepali":"शिक्षण भिडियो"},
    "Phet Simulation": {"English":"Phet Simulation","Nepali":"फेट सिमुलेशन"},
    "Khan Academy Video": {"English":"Khan Academy Video","Nepali":"खान एकेडेमी भिडियो"},
}


# Streamlit app
# Language selection dropdown
language = st.sidebar.selectbox("Select Language (भाषा छान्‍नुहोस्)", options=["English", "Nepali"], key="language")

# Main navigation sidebar
# Title and sidebar header with language mapping
st.title(labels["title"][language])
st.sidebar.header(labels["search_filter"][language])
st.sidebar.write(labels["filter_instruction"][language])


# Function to parse subject and chapter based on selected language
def parse_language(df, language):
    if language == "English":
        df['subject'] = df['subject'].apply(lambda x: x.split('[')[0].strip())
        df['chapter'] = df['chapter'].apply(lambda x: x.split('[')[0].strip())
    else:
        df['subject'] = df['subject'].apply(lambda x: x.split('[[')[1].split(']]')[0].strip() if '[[' in x else x)
        df['chapter'] = df['chapter'].apply(lambda x: x.split('[[')[1].split(']]')[0].strip() if '[[' in x else x)
    return df

# Apply language parsing
df = parse_language(df, language)

# Translate content types and sources
df['type'] = df['type'].map(lambda x: content_type_source_labels.get(x, {}).get(language, x))
df['content_source'] = df['content_source'].map(lambda x: content_type_source_labels.get(x, {}).get(language, x))


# Search bar for content cards or table view
search_query = st.sidebar.text_input(labels["search_label"][language], key="search_query_sidebar")

# Function to clear search query
def clear_search_query():
    st.session_state["search_query_sidebar"] = ""

col1Side, col2Side = st.sidebar.columns([0.5,0.5])
search_button = col1Side.button(labels["search_btn_text"][language], key="search_btn_sidebar",use_container_width =True, type='primary')
reset_button = col2Side.button(labels["reset_btn_text"][language], key="reset_btn_sidebar",  on_click=clear_search_query,use_container_width =True)

# Apply search filter if search button is clicked
if search_button or search_query:
    df = df[df.apply(lambda row: search_query.lower() in str(row['title']).lower() or search_query.lower() in str(row['subject']).lower() or search_query.lower() in str(row['chapter']).lower(), axis=1)]




grade_options = [labels["all_text"][language]] + list(df['grade'].unique())
selected_grades = st.sidebar.multiselect(labels["select_grade"][language], options=grade_options, key="grade_filter_main",placeholder=labels["choose_an_option"][language])
if selected_grades:
    df = df[df['grade'].isin(selected_grades)]


# Filter by Subject
subject_options = [labels["all_text"][language]] + list(df['subject'].unique())
subject_filter = st.sidebar.selectbox(labels["select_subject"][language], options=subject_options, index=0, key="subject_filter_main", placeholder=labels["choose_an_option"][language])
if subject_filter != labels["all_text"][language]:
    df = df[df['subject'] == subject_filter]

# Filter by Chapter
# Multi-select for Chapter
chapter_options = list(df['chapter'].unique())
selected_chapters = st.sidebar.multiselect(labels["select_chapter"][language], options=chapter_options, key="chapters_select_main",placeholder=labels["choose_an_option"][language])
if selected_chapters:
    df = df[df['chapter'].isin(selected_chapters)]

content_types = df['type'].unique()
selected_types = st.sidebar.multiselect(labels["select_content_type"][language], content_types, default=content_types, key="type_select_main",placeholder=labels["choose_an_option"][language])
if selected_types:
    df = df[df['type'].isin(selected_types)]

content_sources = df['content_source'].unique()
selected_sources = st.sidebar.multiselect(labels["select_content_source"][language], content_sources, default=content_sources, key="source_select_main",placeholder=labels["choose_an_option"][language])
if selected_sources:
    df = df[df['content_source'].isin(selected_sources)]


# selection of view
navigation_options = [labels["card_view_label"][language],labels["table_view_label"][language]]
navigation_choice = st.sidebar.radio(labels["select_view_text"][language], navigation_options, key="navigation_choice")

# MAIN SEARCH BAR
search_query1 = st.text_input(labels["search_label"][language], key="search_query_main1")

# Function to clear search query
def clear_search_query_main():
    st.session_state["search_query_main1"] = ""

col1, col2 = st.columns([0.75, 0.25])
search_button1 = col1.button(labels["search_btn_text"][language], key="search_btn_main",use_container_width =True,type='primary')
reset_button1 = col2.button(labels["reset_btn_text"][language], key="reset_btn_main",  on_click=clear_search_query_main,use_container_width =True)

# Apply search filter if search button is clicked or search query present (hit enter)
if search_button1 or search_query1:
    df = df[df.apply(lambda row: search_query1.lower() in str(row['title']).lower() or search_query1.lower() in str(row['subject']).lower() or search_query1.lower() in str(row['chapter']).lower(), axis=1)]


# View selection buttons
# Define a dictionary for column translations
column_labels = {
    'title': {
        'English': 'Title',
        'Nepali': 'शिर्षक'
    },
    'grade': {
        'English': 'Grade',
        'Nepali': 'कक्षा'
    },
    'subject': {
        'English': 'Subject',
        'Nepali': 'विषय'
    },
    'chapter': {
        'English': 'Chapter',
        'Nepali': 'पाठ'
    },
    'content_link': {
        'English': 'Content Link',
        'Nepali': 'सामग्री लिङ्क'
    }
}

# Create a mapping for sorting options to their actual column names
sort_options = {
    column_labels['title'][language]: 'title',
    column_labels['grade'][language]: 'grade',
    column_labels['subject'][language]: 'subject',
    column_labels['chapter'][language]: 'chapter'
}

if navigation_choice == labels["table_view_label"][language]:
    # Display filtered table with specific columns
    st.write(f"### {labels['total_content'][language]}: {len(df)}")

    # Allow sorting by specific columns using displayed labels
    sort_column_label = st.selectbox('Sort by', list(sort_options.keys()))
    ascending = st.checkbox('Ascending', True)

    # Get the actual column name from the selected label
    sort_column = sort_options[sort_column_label]

    # Sort the DataFrame using actual column names
    sorted_df = df.sort_values(by=sort_column, ascending=ascending)

    # Get the displayed column names for the sorted DataFrame
    displayed_columns = [
        column_labels['title'][language],
        column_labels['grade'][language],
        column_labels['subject'][language],
        column_labels['chapter'][language],
        column_labels['content_link'][language]
    ]

    # Create a list of the actual DataFrame column names
    actual_columns = ['title', 'grade', 'subject', 'chapter', 'content_link']

    # Display the sorted DataFrame using the actual column names
    st.write(sorted_df[actual_columns].rename(columns=dict(zip(actual_columns, displayed_columns))))

    # Add a download button for CSV
    #csv_data = sorted_df.to_csv(index=False).encode('utf-8')
    #st.download_button(label="Download data as CSV", data=csv_data, file_name='filtered_data.csv', mime='text/csv')

elif navigation_choice == labels["card_view_label"][language]:
    # Initial number of cards to display
    initial_cards = 30
    load_more_increment = 3

    if "card_limit" not in st.session_state:
        st.session_state.card_limit = initial_cards

    # Function to load more cards
    def load_more_cards():
        st.session_state.card_limit += load_more_increment

    # Display current batch of cards
    end_idx = min(st.session_state.card_limit, len(df))
    cards = df.iloc[:end_idx]
    
    # Display content cards
    #st.write("## Content Cards")
    st.write(f"### {labels['total_content'][language]}: {len(df)}, {labels['displayed_label'][language]}: {end_idx}")

    # Define icons for different content types
    content_type_icons = {
        'audio': 'audio.png',
        'video': 'video.png',
        'interactive': 'interactive.png',
        'document': 'document.png',
        'अडियो': 'audio.png',
        'भिडियो': 'video.png',
        'अन्तर्क्रियात्मक': 'interactive.png',
        'किताब': 'document.png'
    }

    # Prepare content for each card
    for i in range(0, end_idx, 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < end_idx:
                row = cards.iloc[i + j]
                content_type = row['type'].lower()
                # Get the corresponding content type key
                # content_type_key = content_type_translations.get(content_type, None)

                # Get the icon path based on the key
                # icon_path = content_type_icons.get(content_type_key, '') if content_type_key else ''

                icon_path = content_type_icons.get(content_type, '')

                # Generate card content
                card_content = f"""
                    <div class="card">
                        <p><img src="data:image/png;base64,{get_base64_image(icon_path) if icon_path != '' else 'N'}" height="40" width="40" alt="Content Type"/><strong> {row['content_source']}</strong></p>
                        <h5>{row['title']}</h5>
                        <p>{labels["grade_text_only"][language]} {row['grade']}, {row['subject']}, {row['chapter']}</p>
                        <p><a href="{row['content_link']}" target="_blank">{labels["learn_now_text"][language]}</a></p>
                        {'<p><strong>Not in Gradewise</strong></p>' if row.get('not_in_gradewise') == 'Yes' else ''}
                    </div>
                """
                col.markdown(card_content, unsafe_allow_html=True)
    
    # Info line showing loaded content count
    st.write(f"Loaded {end_idx} out of {len(df)} content")
    # Button to load more cards
    load_more_cards()
    if end_idx < len(df):
        if st.button("Load more"):
            load_more_cards()

# Add CSS to style the cards
st.markdown("""
    <style>
    .card {
        border: 1px solid #e6e6e6;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
    }
    .card h4 {
        margin: 0;
    }
    .card p {
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)


# Footer section
# Footer section
footer = """
<style>
.footer {
    position: relative;  
    left: 0;
    bottom: 0;
    width: 100%;
    text-align: center;
    padding: 10px;
    font-size: 14px;
}
</style>
<div class="footer">
    <p>© 2024 Open Learning Exchange Nepal | <a href="https://olenepal.org" target="_blank">olenepal.org</a></p>
</div>
"""

st.markdown(footer, unsafe_allow_html=True)
