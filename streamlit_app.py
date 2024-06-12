import pandas as pd
import json
import streamlit as st
import altair as alt

# Mapping dictionary to standardize subject names
subject_mapping = {
    "Maths": ["maths", "Maths", "Maths [[गणित]]", "math"],
    "Science and Technology": ["science-and-technology","science and technology", "Science and Technology", "science & technology", "Science and Technology [[विज्ञान तथा प्रविधि]]"],
    "नेपाली": ["नपल", "नेपाली"],
    "English": ["english"],
    "Social Studies and Human Value Education": ["social-studies-and-human-value-education"],
    "Health Physical And Creative Arts": ["health-physical-and-creative-arts"],
    "Social Studies and Life Skills Education": ["social-studies-and-life-skills-education"],
    "Social Studies": ["social-studies"]
}

# Function to standardize subject names
def standardize_subject(subject):
    for standard_subject, variants in subject_mapping.items():
        if subject in variants:
            return standard_subject
    return subject

def load_and_normalize(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Function to normalize each chapter's content
    def normalize_content(chapter_contents, grade, subject, chapter_slug):
        standardized_subject = standardize_subject(subject)
        contents = []
        for content in chapter_contents:
            base_info = {
                'mainid': content.get('id'),
                'title': content.get('title'),
                'type': content.get('type'),
                'grade': grade,
                'subject': standardized_subject,
                'chapter_slug': chapter_slug
            }
            if content['type'] == 'document':
                for file_info in content.get('file_upload', []):
                    content_info = base_info.copy()
                    content_info.update({
                        'file_id': file_info.get('id'),
                        'name': file_info.get('name'),
                        'grade': file_info.get('grade'),
                        'subject': standardized_subject,
                        'chapter_slug': file_info.get('chapter_slug'),
                        'type': file_info.get('type'),
                        'link': 'https://pustakalaya.org' + str(file_info.get('link'))
                    })
                    contents.append(content_info)
            elif content['type'] == 'audio':
                for file_info in content.get('file_upload', []):
                    content_info = base_info.copy()
                    content_info.update({
                        'file_id': file_info.get('id'),
                        'name': file_info.get('name'),
                        'grade': file_info.get('grade'),
                        'subject': standardized_subject,
                        'chapter_slug': file_info.get('chapter_slug'),
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
                    'grade': content.get('grade'),
                    'subject': standardized_subject,
                    'chapter_slug': content.get('chapter_slug'),
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
subjects = st.sidebar.multiselect("Select Subject", options=df['subject'].unique(), default=df['subject'].unique())
types = st.sidebar.multiselect("Select Content Type", options=df['type'].unique(), default=df['type'].unique())

# Filter DataFrame based on selections
filtered_df = df[df['grade'].isin(grades) & df['subject'].isin(subjects) & df['type'].isin(types)]

# Dynamically update chapters based on selected grade and subject
chapters = filtered_df['chapter_slug'].unique()
selected_chapters = st.sidebar.multiselect("Select Chapter", options=chapters, default=chapters)

# Further filter DataFrame based on selected chapters
if selected_chapters:
    filtered_df = filtered_df[filtered_df['chapter_slug'].isin(selected_chapters)]

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
st.dataframe(filtered_df[['title', 'grade', 'subject', 'chapter_slug', 'link']], height=300)

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
                <p><strong>Chapter:</strong> {row['chapter_slug']}</p>
                <p><strong>Type:</strong> {row['type']}</p>
                <p><a href="{row['link']}" target="_blank">View Content</a></p>
            </div>
            """, axis=1).tolist()
        rows.append("".join(row_cards))
    
    # Add responsive styles
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
