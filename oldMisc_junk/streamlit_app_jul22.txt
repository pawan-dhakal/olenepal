import pandas as pd
import json
import streamlit as st
import base64
import requests

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
df = pd.read_json('all_content.json', orient='records')

# Fill NaN values with empty strings
df = df.fillna('')

# Streamlit app
st.title("OLE Nepal Content Browser")

# Navigation buttons in the main dashboard
navigation_options = ["Cards View", "Table View"]
navigation_choice = st.sidebar.radio("Select View", navigation_options, key="navigation_choice")

# Sidebar filters
st.sidebar.header("Search and Filter")

# Search bar in the sidebar
search_query = st.sidebar.text_input("Search subject, title or chapter: ", key="search_query")

# Language selection dropdown
language = st.sidebar.selectbox("Select Language", options=["English", "Nepali"], key="language")

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

# Filter by Grade
grade_options = ["All"] + list(df['grade'].unique())
grade_filter = st.sidebar.selectbox("Select Grade", options=grade_options, index=0, key="grade_filter")
if grade_filter != "All":
    df = df[df['grade'] == grade_filter]

# Filter by Subject
subject_options = ["All"] + list(df['subject'].unique())
subject_filter = st.sidebar.selectbox("Select Subject", options=subject_options, index=0, key="subject_filter")
if subject_filter != "All":
    df = df[df['subject'] == subject_filter]

# Filter by Content Type
content_types = df['type'].unique()
selected_types = st.sidebar.multiselect("Select Content Type", content_types, default=content_types, key="type_select")
if selected_types:
    df = df[df['type'].isin(selected_types)]

# Filter by "Doesn't exist in gradewise"
not_in_gradewise_options = ["All", "Yes", "No"]
not_in_gradewise_filter = st.sidebar.selectbox("Doesn't exist in gradewise", options=not_in_gradewise_options, index=0, key="not_in_gradewise_filter")
if not_in_gradewise_filter != "All":
    df = df[df['not_in_gradewise'] == not_in_gradewise_filter]

# Multi-select for Chapter
chapter_options = list(df['chapter'].unique())
selected_chapters = st.sidebar.multiselect("Select Chapter", options=chapter_options, key="chapters_select")
if selected_chapters:
    df = df[df['chapter'].isin(selected_chapters)]

# Apply search filter
if search_query:
    df = df[df.apply(lambda row: search_query.lower() in str(row['title']).lower() or search_query.lower() in str(row['subject']).lower() or search_query.lower() in str(row['chapter']).lower(), axis=1)]

# Main navigation bar above content cards
st.write("## Navigation Bar")
st.write("Use the filters below to navigate content:")

# Search bar for content cards or table view
search_query = st.text_input("Search within content:", key="search_query_main")

# Layout the filters and search bar in a row
col1, col2 = st.columns([1, 1])

# Filter by Grade
with col1:
    grade_options = ["All"] + list(df['grade'].unique())
    grade_filter = st.selectbox("Select Grade", options=grade_options, index=0, key="grade_filter_main")
    if grade_filter != "All":
        df = df[df['grade'] == grade_filter]

# Filter by Subject
with col2:
    subject_options = ["All"] + list(df['subject'].unique())
    subject_filter = st.selectbox("Select Subject", options=subject_options, index=0, key="subject_filter_main")
    if subject_filter != "All":
        df = df[df['subject'] == subject_filter]

# Filter by Chapter
# Multi-select for Chapter
chapter_options = list(df['chapter'].unique())
selected_chapters = st.multiselect("Select Chapter", options=chapter_options, key="chapters_select_main")
if selected_chapters:
    df = df[df['chapter'].isin(selected_chapters)]

content_types = df['type'].unique()
selected_types = st.multiselect("Select Content Type", content_types, default=content_types, key="type_select_main")
if selected_types:
    df = df[df['type'].isin(selected_types)]

content_sources = df['content_source'].unique()
selected_sources = st.multiselect("Select Content Source", content_sources, default=content_sources, key="source_select_main")
if selected_sources:
    df = df[df['content_source'].isin(selected_sources)]

# Apply search filter
if search_query:
    df = df[df.apply(lambda row: search_query.lower() in str(row['title']).lower() or search_query.lower() in str(row['subject']).lower() or search_query.lower() in str(row['chapter']).lower(), axis=1)]

# View selection buttons
if navigation_choice == "Table View":
    # Display filtered table with specific columns
    st.write("## Filtered Data")
    st.write(f"### Total Activities: {len(df)}")

    # Allow sorting by column
    sort_column = st.selectbox('Sort by', df.columns)
    ascending = st.checkbox('Ascending', True)
    sorted_df = df.sort_values(by=sort_column, ascending=ascending)

    # Display the sorted dataframe
    st.write(sorted_df[['title', 'grade', 'subject', 'chapter', 'content_link']])

    # Add a download button for CSV
    csv_data = sorted_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download data as CSV", data=csv_data, file_name='filtered_data.csv', mime='text/csv')

elif navigation_choice == "Cards View":
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
    st.write("## Content Cards")
    st.write(f"### Total Activities: {len(df)}, Displayed: {end_idx}")
    

    

    # Define icons for different content types
    content_type_icons = {
        'audio': 'audio.png',
        'video': 'video.png',
        'interactive': 'interactive.png',
        'document': 'document.png'
    }

    # Prepare content for each card
    for i in range(0, end_idx, 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < end_idx:
                row = cards.iloc[i + j]
                content_type = row['type']
                icon_path = content_type_icons.get(content_type, '')

                # Generate card content
                card_content = f"""
                    <div class="card">
                        <p><img src="data:image/png;base64,{get_base64_image(icon_path)}" height="25" width="25" alt="Content Type"/><strong> {row['content_source']}</strong></p>
                        <h4>{row['title']}</h4>
                        <p><strong>Grade {row['grade']}, {row['subject']}, {row['chapter']}</strong></p>
                        <p><strong><a href="{row['content_link']}" target="_blank">View Content</a></strong></p>
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
