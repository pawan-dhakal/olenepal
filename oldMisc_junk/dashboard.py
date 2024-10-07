import pandas as pd
import json
import streamlit as st
import altair as alt

# Function to load and normalize data from JSON
def load_and_normalize(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Function to normalize each chapter's content
    def normalize_content(chapter_contents, grade, subject, chapter_slug):
        contents = []
        for content in chapter_contents:
            base_info = {
                'mainid': content.get('id'),
                'title': content.get('title'),
                'type': content.get('type'),
                'grade': grade,
                'subject': subject,
                'chapter_slug': chapter_slug
            }
            if content['type'] in ['document', 'audio']:
                for file_info in content.get('file_upload', []):
                    content_info = base_info.copy()
                    content_info.update({
                        'file_id': file_info.get('id'),
                        'name': file_info.get('name'),
                        'link': 'https://pustakalaya.org' + str(file_info.get('link'))
                    })
                    contents.append(content_info)
            elif content['type'] == 'video':
                content_info = base_info.copy()
                content_info.update({
                    'link': 'https://pustakalaya.org/videos/detail/' + content.get('id')
                })
                contents.append(content_info)
            elif content['type'] == 'interactive':
                content_info = base_info.copy()
                content_info.update({
                    'link': content.get('online_domain') + content.get('link_to_content')
                })
                contents.append(content_info)
        return contents

    # Extracting and normalizing data
    all_contents = []
    for grade, subjects in data.items():
        for subject, chapters in subjects.items():
            for chapter, chapter_contents in chapters.items():
                all_contents.extend(normalize_content(chapter_contents, grade, subject, chapter))
    
    return all_contents

# Load and process all files
file_paths = ['grade6.json', 'grade7.json', 'grade8.json', 'grade9.json', 'grade10.json', 'grade11.json', 'grade12.json']
all_contents = []
for file_path in file_paths:
    all_contents.extend(load_and_normalize(file_path))

# Create DataFrame
df = pd.DataFrame(all_contents)

# Streamlit app
st.title("Educational Content Browser")

# Sidebar filters
st.sidebar.header("Filters")
grades = st.sidebar.multiselect("Select Grade", options=df['grade'].unique(), default=df['grade'].unique())
filtered_df = df[df['grade'].isin(grades)]

subjects = st.sidebar.multiselect("Select Subject", options=filtered_df['subject'].unique(), default=filtered_df['subject'].unique())
filtered_df = filtered_df[filtered_df['subject'].isin(subjects)]

types = st.sidebar.multiselect("Select Content Type", options=filtered_df['type'].unique(), default=filtered_df['type'].unique())
filtered_df = filtered_df[filtered_df['type'].isin(types)]


# Dynamically update chapters based on selected grade and subject
if grades and subjects:
    chapters = st.sidebar.multiselect("Select Chapter", options=filtered_df['chapter_slug'].unique(), default=filtered_df['chapter_slug'].unique())
    filtered_df = filtered_df[filtered_df['chapter_slug'].isin(chapters)]


# Display total count of activities
st.write(f"### Total Activities: {len(filtered_df)}")

# Display filtered table with specific columns
st.write("### Filtered Data")
st.dataframe(filtered_df[['title', 'grade', 'subject', 'chapter_slug', 'link']])

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

# Initialize session state for pagination
if 'start_idx' not in st.session_state:
    st.session_state.start_idx = 0
if 'batch_size' not in st.session_state:
    st.session_state.batch_size = 10

# Function to render content cards
def render_content_cards(df, start_idx, batch_size):
    for _, row in df.iloc[start_idx:start_idx+batch_size].iterrows():
        st.write(
            f"""
            <div style="border: 1px solid #e1e4e8; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                <h4>{row['title']}</h4>
                <p><strong>Grade:</strong> {row['grade']}</p>
                <p><strong>Subject:</strong> {row['subject']}</p>
                <p><strong>Chapter:</strong> {row['chapter_slug']}</p>
                <p><strong>Type:</strong> {row['type']}</p>
                <p><a href="{row['link']}" target="_blank">View Content</a></p>
            </div>
            """,
            unsafe_allow_html=True
        )

# Display content cards with pagination
st.write("### Content Cards")

if st.button('Load More'):
    st.session_state.start_idx += st.session_state.batch_size

render_content_cards(filtered_df, st.session_state.start_idx, st.session_state.batch_size)
