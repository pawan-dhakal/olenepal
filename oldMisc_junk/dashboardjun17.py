import pandas as pd
import json
import streamlit as st
import altair as alt

for_offline_use = False

def extract_content_from_json(file_path, records=[], for_offline_use=for_offline_use):
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
                        'content_id': content.get('id'), #main id of the content
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
                            'name': 'NA', # not in 'interactive' type in json files, but in other types
                            'file_id': 'NA', # not in 'interactive' type in json files, but in other types
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
                                'content_link': 'http://172.18.96.1' + str(file_info.get('link')) if for_offline_use else 'https://pustakalaya.org' + str(file_info.get('link'))
                            })
                            records.append(record)
                    elif content.get('type') == 'video':
                        source_key = 'file_upload' if for_offline_use else 'embed_link'
                        base_url = 'http://172.18.96.1' if for_offline_use else ''
                        for file_info in content.get(source_key, []):
                            record = base_record.copy()
                            record.update({
                                'grade': file_info.get('grade'),
                                'subject': file_info.get('subject'),
                                'chapter': file_info.get('chapter'),
                                'chapter_slug': file_info.get('chapter_slug'),
                                'name': file_info.get('name'),
                                'file_id': file_info.get('id'),
                                'content_link': base_url + str(file_info.get('link'))
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

df = all_df

# Streamlit app
st.title("OLE Nepal Content Browser")

# Sidebar filters
st.sidebar.header("Filters")

# Multi-select filters for grade, subject, and type
grades = st.sidebar.multiselect("Select Grade", options=df['grade'].unique(), default=df['grade'].unique())
filtered_df = df[df['grade'].isin(grades)]

subjects = st.sidebar.multiselect("Select Subject", options=filtered_df['subject'].unique(), default=filtered_df['subject'].unique())
filtered_df = filtered_df[filtered_df['subject'].isin(subjects)]

types = st.sidebar.multiselect("Select Content Type", options=filtered_df['type'].unique(), default=filtered_df['type'].unique())
filtered_df = filtered_df[filtered_df['type'].isin(types)]

# Dynamic chapter selection based on grade and subject
chapters = filtered_df['chapter'].unique()
selected_chapters = st.sidebar.multiselect("Select Chapter", options=chapters, default=chapters)
filtered_df = filtered_df[filtered_df['chapter'].isin(selected_chapters)]

# Display total count of activities
st.write(f"### Total Activities: {len(filtered_df)}")

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

# Initialize session state for pagination
if 'start_idx' not in st.session_state:
    st.session_state.start_idx = 0
if 'batch_size' not in st.session_state:
    st.session_state.batch_size = 9  # Display 9 cards per page (3 rows of 3 cards each)

# Function to render content cards
def render_content_cards(df, start_idx, batch_size):
    rows = []
    for i in range(start_idx, min(start_idx + batch_size, len(df)), 3):
        row_cards = df.iloc[i:i+3].apply(lambda row: f"""
            <div class="card">
                <h4>{row['title']}</h4>
                <p><strong>Grade:</strong> {row['grade']}</p>
                <p><strong>Subject:</strong> {row['subject']}</p>
                <p><strong>Chapter:</strong> {row['chapter']}</p>
                <p><strong>Type:</strong> {row['type']}</p>
                <p><a href="{row['content_link']}" target="_blank">View Content</a></p>
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
        width: 30%; 
        float: left;
    }
    @media (max-width: 768px) {
        .card {
            width: 100%;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='display: flex; flex-wrap: wrap;'>", unsafe_allow_html=True)
    for row in rows:
        st.markdown(row, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Display content cards with pagination
st.write("### Content Cards")

col1, col2, col3 = st.columns([1, 2, 1])  # Adjust column widths for better layout
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
