import pandas as pd
import json
import streamlit as st
import altair as alt
import base64
import requests


# Helper function to convert image to base64
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

for_offline_use = False

def extract_content_from_json(file_path, records=[], for_offline_use=False):
    """
    returns appended records list 
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    for grade, subjects in data.items():
        for subject, contents_list in subjects.items():
            for contents_list_no, contents in contents_list.items():
                for content in contents:
                    base_record = {
                        'content_id': content.get('id'),  # main id of the content
                        'title': content.get('title'),
                        'type': content.get('type')
                    }
                    if content.get('type') == 'interactive': 
                        record = base_record.copy()
                        record.update({
                            'grade': content.get('grade'),
                            'subject': content.get('subject'),
                            'chapter': content.get('chapter'),
                            'chapter_slug': content.get('chapter_slug'),
                            'content_link': content.get('offline_domain') + content.get('link_to_content') if for_offline_use else content.get('online_domain') + content.get('link_to_content'),
                            'name': 'NA',  # not in 'interactive' type in json files, but in other types
                            'file_id': 'NA',  # not in 'interactive' type in json files, but in other types
                            'publisher_logo': 'http://172.18.96.1' + str(content.get('publisher_logo')) if for_offline_use else 'https://pustakalaya.org' + str(content.get('publisher_logo')),
                        })
                        records.append(record)
                    elif content.get('type') == 'document' or content.get('type') == 'audio': 
                        for file_info in content.get('file_upload', []):
                            record = base_record.copy()
                            record.update({
                                'grade': file_info.get('grade'),
                                'subject': file_info.get('subject'),
                                'chapter': file_info.get('chapter'),
                                'chapter_slug': file_info.get('chapter_slug'),
                                'name': file_info.get('name'),
                                'file_id': file_info.get('id'),
                                'publisher_logo': 'http://172.18.96.1' + str(file_info.get('publisher_logo')) if for_offline_use else 'https://pustakalaya.org' + str(file_info.get('publisher_logo')),
                                'content_link': 'http://172.18.96.1' + str(file_info.get('link')) if for_offline_use else 'https://pustakalaya.org' + str(file_info.get('link'))
                            })
                            records.append(record)
                    elif content.get('type') == 'video':
                        # Determine the appropriate content source based on the offline/online flag
                        source_key = 'file_upload' if for_offline_use else 'embed_link'
                        base_url = 'http://172.18.96.1' if for_offline_use else ''  # youtube link in embed_link
                        # Loop through the relevant content source and add records
                        for file_info in content.get(source_key, []):
                            record = base_record.copy()
                            record.update({
                                'grade': grade,  # file_info.get('grade'), #KA videos grade in record maybe different to grade specified in content.
                                'subject': file_info.get('subject'),
                                'chapter': file_info.get('chapter'),
                                'chapter_slug': file_info.get('chapter_slug'),
                                'name': file_info.get('name'),
                                'file_id': file_info.get('id'),
                                'content_link': base_url + str(file_info.get('link')),
                                'publisher_logo': 'http://172.18.96.1' + str(content.get('publisher_logo')) if for_offline_use else 'https://pustakalaya.org' + str(content.get('publisher_logo')),
                            })
                            records.append(record)

    return records

# Process all files and concatenate the data
file_paths = ['grade6.json', 'grade7.json', 'grade8.json', 'grade9.json', 'grade10.json', 'grade11.json', 'grade12.json']
all_df = pd.DataFrame()
for file_path in file_paths:
    records = extract_content_from_json(file_path, for_offline_use=for_offline_use, records=[])
    df = pd.DataFrame(records)
    all_df = pd.concat([all_df, df], ignore_index=True)

df = all_df  # redefining as df

# Streamlit app
st.title("OLE Nepal Content Browser")

# Sidebar filters
st.sidebar.header("Filters")

# Language selection dropdown
language = st.sidebar.selectbox("Select Language", options=["English", "Nepali"])

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

# Single-select for Grade
grade = st.sidebar.selectbox("Select Grade", options=["All"] + list(df['grade'].unique()))
if grade != "All":
    filtered_df = df[df['grade'] == grade]
else:
    filtered_df = df.copy()

# Single-select for Subject
subject = st.sidebar.selectbox("Select Subject", options=["All"] + list(filtered_df['subject'].unique()))
if subject != "All":
    filtered_df = filtered_df[filtered_df['subject'] == subject]

# Multi-select for Content Type using checkboxes
st.sidebar.subheader("Select Content Type")
content_types = df['type'].unique()
selected_types = []
for content_type in content_types:
    if st.sidebar.checkbox(content_type, value=True):
        selected_types.append(content_type)
if selected_types:
    filtered_df = filtered_df[filtered_df['type'].isin(selected_types)]

# Multi-select for Chapter
chapters = filtered_df['chapter'].unique()
selected_chapters = st.sidebar.multiselect("Select Chapter", options=chapters, default=chapters)
if selected_chapters:
    filtered_df = filtered_df[filtered_df['chapter'].isin(selected_chapters)]

# Display total count of activities
st.write(f"### Total Activities: {len(filtered_df)}")

# View selection buttons
view = st.selectbox("Select View", options=["Cards", "Table", "Chart"])

if view == "Table":
    # Display filtered table with specific columns
    st.write("### Filtered Data")
    st.markdown("""
    <style>
        .dataframe {
            width: 100%;
            overflow-x: auto;
        }
        @media (max-width: 768px) {
            .dataframe table {
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    st.dataframe(filtered_df[['title', 'grade', 'subject', 'chapter', 'content_link']], height=300)

    # Add a download button
    st.download_button(
        label="Download data as CSV",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name='filtered_data.csv',
        mime='text/csv',
    )

elif view == "Chart":
    # Display Altair chart
    st.write("### Content Distribution by Type")
    chart = alt.Chart(filtered_df).mark_bar().encode(
        x='type',
        y='count()',
        color='type'
    ).properties(
        width=600,
        height=400
    )

    st.altair_chart(chart, use_container_width=True)

elif view == "Cards":
    # Initialize session state for pagination
    if 'start_idx' not in st.session_state:
        st.session_state.start_idx = 0
    if 'batch_size' not in st.session_state:
        st.session_state.batch_size = 9  # Display 9 cards per page (3 rows of 3 cards each)

    # Prepare base64 icons for the different content types
    icons = {
        'interactive': get_base64_image('interactive.png'),
        'document': get_base64_image('document.png'),
        'audio': get_base64_image('audio.png'),
        'video': get_base64_image('video.png')
    }

    
    # Function to render content cards with modal popup
    def render_content_cards(df, start_idx, batch_size):
        rows = []
        grade_text = 'Grade' if language=="English" else 'कक्षा'
        view_content_text = ' View Lesson>>' if language=="English" else ' पाठ हेर्नुहोस्>>'
        # Function for Nepali numeral conversion with language condition
        def convert_to_nepali_numeral(text, language):
            if language == "Nepali":
                nepali_numerals = {
                    "1": "१",
                    "2": "२",
                    "3": "३",
                    "4": "४",
                    "5": "५",
                    "6": "६",
                    "7": "७",
                    "8": "८",
                    "9": "९",
                    "10": "१०",
                    "11": "११",
                    "12": "१२"
                }
                return nepali_numerals.get(text, text)
            else:
                return text
        for i in range(start_idx, min(start_idx + batch_size, len(df)), 3):
            row_cards = df.iloc[i:i+3].apply(lambda row: f"""
                <div class="card">
                    <h4 style="margin-left: 10px; align-items: center;">{row['title']}</h4>
                    <p><strong>{grade_text} {convert_to_nepali_numeral(str(row['grade']), language)}, {row['subject']}, {row['chapter']}</strong></p>
                    <p style="display: flex; align-items: center;">
                        <img src="data:image/png;base64,{icons.get(row['type'], '')}" width="50" height="50" alt="{row['type']} icon"/>
                        <strong style="padding:10px"><a href="{row['content_link']}" target="_blank">{view_content_text}</a></strong>
                    </p>                                        
                    <p style="display: flex; justify-content: center;">
                        <img src="data:image/png;base64,{get_base64_image(row['publisher_logo'])}" height="25" alt="Publisher logo"/>
                    </p>
                </div>
                """, axis=1).tolist()
            rows.append("".join(row_cards))
        
        st.markdown("""
        <style>
        .card {
            border: 1px solid #e1e4e8; 
            border-radius: 5px; 
            padding: 10px; 
            margin: 10px; 
            width: calc(30% - 20px); 
            float: left;
        }
        @media (max-width: 1200px) {
            .card {
                width: calc(40% - 20px);
            }
        }
        @media (max-width: 768px) {
            .card {
                width: 100%;
            }
        }
        #modal-container {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
        }
        #modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            max-width: 80%;
            max-height: 80%;
            overflow: auto;
        }
        #close-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: red;
            color: white;
            border: none;
            padding: 5px 10px;
            cursor: pointer;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<div style='display: flex; flex-wrap: wrap;'>", unsafe_allow_html=True)
        for row in rows:
            st.markdown(row, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        

    # Display content cards with pagination
    st.write("### Content Cards")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.start_idx > 0:
            if st.button('Previous'):
                st.session_state.start_idx = max(0, st.session_state.start_idx - st.session_state.batch_size)
    with col2:
        page_number = st.session_state.start_idx // st.session_state.batch_size + 1
        total_pages = (len(filtered_df) - 1) // st.session_state.batch_size + 1
        st.write(f"Page {page_number} of {total_pages}")
    with col3:
        if st.session_state.start_idx + st.session_state.batch_size < len(filtered_df):
            if st.button('Next'):
                st.session_state.start_idx = min(len(filtered_df) - st.session_state.batch_size, st.session_state.start_idx + st.session_state.batch_size)

    render_content_cards(filtered_df, st.session_state.start_idx, st.session_state.batch_size)
