import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import isodate
import matplotlib.pyplot as plt
import seaborn as sns

# Define functions
def get_trending_videos(api_key, max_results=200):
    # Build the YouTube service
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    videos = []
    
    # Fetch the most popular videos
    request = youtube.videos().list(
        part='snippet,contentDetails,statistics',
        chart='mostPopular',
        regionCode='US',  
        maxResults=50
    )
    
    while request and len(videos) < max_results:
        response = request.execute()
        for item in response['items']:
            video_details = {
                'video_id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'published_at': item['snippet']['publishedAt'],
                'channel_id': item['snippet']['channelId'],
                'channel_title': item['snippet']['channelTitle'],
                'category_id': item['snippet']['categoryId'],
                'tags': item['snippet'].get('tags', []),
                'duration': item['contentDetails']['duration'],
                'definition': item['contentDetails']['definition'],
                'caption': item['contentDetails'].get('caption', 'false'),
                'view_count': item['statistics'].get('viewCount', 0),
                'like_count': item['statistics'].get('likeCount', 0),
                'dislike_count': item['statistics'].get('dislikeCount', 0),
                'favorite_count': item['statistics'].get('favoriteCount', 0),
                'comment_count': item['statistics'].get('commentCount', 0)
            }
            videos.append(video_details)
        
        # Get the next page token
        request = youtube.videos().list_next(request, response)
    
    return videos[:max_results]

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

def convert_duration(duration_str):
    """Converts ISO 8601 duration string to 'MM:SS' format."""
    duration = isodate.parse_duration(duration_str)
    total_sec = duration.total_seconds()
    mins = int(total_sec // 60)
    secs = int(total_sec % 60)
    return f"{mins}:{secs:02d}"

def duration_to_seconds(duration_str):
    """Converts 'MM:SS' format duration string to total seconds."""
    minutes, seconds = map(int, duration_str.split(':'))
    return minutes * 60 + seconds

def get_category_mapping(api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.videoCategories().list(
        part='snippet',
        regionCode='US'
    )
    response = request.execute()
    category_mapping = {}
    for item in response['items']:
        category_id = int(item['id'])
        category_name = item['snippet']['title']
        category_mapping[category_id] = category_name
    return category_mapping
# Streamlit application
st.title("Trending YouTube Videos Analysis")
st.sidebar.header("Introduction")

st.sidebar.write(
    """
    Welcome to the YouTube Trending Videos Analysis project! This application provides insights into the top trending videos on YouTube by analyzing various metrics and performing exploratory data analysis (EDA). 

    **Steps to Use the Application:**
    1. **Enter Your Google YouTube API Key:** 
        - To fetch trending video data, you need to input your YouTube API key.
    2. **Analyze Top Trending Videos:**
        - Fetch data on the most popular videos from YouTube based on various parameters.
        - Analyze video metrics such as view count, like count, and comment count.
    3. **Perform Exploratory Data Analysis (EDA):**
        - Explore data distribution, correlation, and trends.
        - Visualize factors that influence trending status and virality.
        - Assess metrics like video length, description length, and publish time to understand their impact on views and engagement.
    
    **Key Factors Analyzed:**
    - **View Count and Like Count:** Analyze which videos have the highest view and like counts.
    - **Publish Time:** Understand how the time of publishing affects the number of views.
    - **Video Length:** Explore whether the length of a video influences its popularity.
    - **Description Length:** Assess how the length of the video description impacts engagement.
    - **Captions:** Investigate if videos with captions perform better.
    - **Categories:** Compare engagement metrics across different video categories.

    This application will help you gain insights into what makes a video trend and how various factors contribute to its success on YouTube.
    """
)

# API Key Input
st.header("YouTube API Key")
api_key = st.text_input("Enter your YouTube Data API key:")

if api_key:
    st.write("Fetching trending videos...")
    
    # Fetch data
    trending_videos = get_trending_videos(api_key)
    
    # Save to CSV
    filename = 'trending_videos.csv'
    save_to_csv(trending_videos, filename)
    
    st.write(f"Trending videos data saved to `{filename}`.")
    
    # Load and display data
    data = pd.read_csv(filename)
    st.write("Data preview:")
    st.write(data.head())

    # Display data overview
    st.header("Data Overview")
    st.write("**Data Head:**")
    st.write(data.head())
    
    st.write("**Data Info:**")
    st.write(data.info())
    
    st.write("**Correlation Matrix:**")
    st.write(data.corr(numeric_only=True))
    
    st.write("**Max View Count:**")
    max_view_count = data['view_count'].max()
    st.write(f"Max view count is: {max_view_count}")
    
    st.write("**Max Like Count:**")
    max_like_count = data['like_count'].max()
    st.write(f"Max like count is: {max_like_count}")

    # Process and display additional data
    st.write("**Processing Published Date and Time Slot:**")
    data['published_at'] = pd.to_datetime(data['published_at'], utc=True)
    st.write("**First Published Date (UTC to Asia/Kolkata):**")
    data['published_at'] = data['published_at'].dt.tz_convert('Asia/Kolkata')
    st.write(data['published_at'].head(1))
    
    data['week'] = data['published_at'].dt.dayofweek.apply(lambda x: 'Weekend' if x >= 5 else "Weekday")
    data['time_slot'] = data['published_at'].dt.hour.apply(lambda x: 'Morning' if 5 <= x < 12 else ('Noon' if 12 <= x < 17 else 'Night'))
    
    st.write("**Weekday/Weekend and Time Slot Classification:**")
    st.write(data[['week', 'time_slot']].head())

    st.write("**Processing Video Duration:**")
    data['duration'] = data['duration'].apply(convert_duration)
    
    st.write("**Converted Duration:**")
    st.write(data['duration'].head())
    # Add new features: Video Length and Description Length
    st.write("**Categorizing Video Length and Description Length:**")
    
    data['video_length'] = data['duration'].apply(lambda x: 'short' if duration_to_seconds(x) < duration_to_seconds('7:00') else 'long')
    data['description_len'] = data['description'].str.len()
    data['description_type'] = data['description_len'].apply(lambda x: "short" if x <= 300 else ("medium" if 300 < x < 1500 else "long"))
    
    st.write("**Video Length Classification:**")
    st.write(data[['title', 'video_length']].head())
    
    st.write("**Description Length Classification:**")
    st.write(data[['title', 'description_len', 'description_type']].head())

    # Display additional statistics
    st.write("**Additional Statistics:**")
    st.write(data.describe())

    # EDA - Highest views and likes
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.header("Highest Views and Likes")
    max_views = data.loc[data['view_count'].idxmax()]
    max_likes = data.loc[data['like_count'].idxmax()]
    st.write(f"**Highest Views:** Title: {max_views.title}, Views: {max_views.view_count}")
    st.write(f"**Highest Likes:** Title: {max_likes.title}, Likes: {max_likes.like_count}")

    # EDA - Weekday vs Weekend Uploads
    st.header("Weekday vs Weekend Uploads")
    week_distribution = data['week'].value_counts()
    
    fig, axs = plt.subplots(1, 2, figsize=(14, 6))
    
    # Pie chart for week distribution
    axs[0].pie(week_distribution, labels=week_distribution.index, colors=['brown', 'green'], autopct='%1.1f%%')
    axs[0].set_title("Videos Uploaded on Weekdays vs Weekends")
    
    # Bar chart for average views
    avg_views = data.groupby('week')['view_count'].mean().reset_index()
    sns.barplot(x='week', y='view_count', hue='week', data=avg_views, palette=['lightblue', 'lightgreen'], ax=axs[1])
    axs[1].set_title('Average Views of Videos Uploaded on Weekdays vs. Weekends')
    axs[1].set_xlabel('Week')
    axs[1].set_ylabel('Average View Count')
    
    st.pyplot(fig)

    # EDA - Effect on Views with Publish Time Slot
    st.header("Effect on Views with Publish Time Slot")
    plt.figure(figsize=(10, 6))
    sns.barplot(data=data, x='time_slot', y='view_count', hue='time_slot', palette=['green', 'yellow', 'blue'])
    plt.title('Effect on Views with Publish Time Slot')
    plt.xlabel('Time Slot')
    plt.ylabel('View Count')
    st.pyplot()

    # EDA - Video Length vs Views
    st.header("Video Length vs Views")
    plt.figure(figsize=(10, 6))
    sns.barplot(x='video_length', y='view_count', data=data)
    plt.title('Video Length vs Views')
    plt.xlabel('Video Length')
    plt.ylabel('View Count')
    st.pyplot()

    # EDA - Description Length vs Views
    st.header("Description Length vs Views")
    avg_views = data.groupby('description_type')['view_count'].mean()

    plt.figure(figsize=(16, 6))
    plt.subplot(1, 2, 1)
    plt.plot(avg_views.index, avg_views.values, marker='o', linestyle='-', color='skyblue')
    plt.title('Average Views by Description Length (Line Plot)')
    plt.xlabel('Description Length')
    plt.ylabel('Average Views')
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.bar(avg_views.index, avg_views.values, color=['skyblue', 'lightgreen', 'brown'])
    plt.title('Average Views by Description Length (Bar Plot)')
    plt.xlabel('Description Length')
    plt.ylabel('Average Views')

    plt.tight_layout()
    st.pyplot()
    # EDA - Caption Impact
    st.header("Caption Impact on Views")
    caption = data['caption'].value_counts()
    fig, axs = plt.subplots(1, 2, figsize=(14, 6))
    
    axs[0].pie(caption, labels=caption.index, colors=['brown', 'green'], autopct='%1.1f%%')
    axs[0].set_title("Videos with and without Captions")
    
    avg_views = data.groupby('caption')['view_count'].mean().reset_index()
    sns.barplot(x='caption', y='view_count', hue='caption', data=avg_views, palette=['blue', 'green'], ax=axs[1])
    axs[1].set_title('Average Views of Videos with Captions vs. No Captions')
    axs[1].set_xlabel('Caption')
    axs[1].set_ylabel('Average View Count')
    
    st.pyplot(fig)

    # EDA - Category Distribution
    st.header("Trending Videos by Category")
    category_mapping = get_category_mapping(api_key)
    data['category_name'] = data['category_id'].map(category_mapping)

    plt.figure(figsize=(12, 8))
    sns.countplot(y=data['category_name'], order=data['category_name'].value_counts().index, palette='viridis')
    plt.title('Number of Trending Videos by Category')
    plt.xlabel('Number of Videos')
    plt.ylabel('Category')
    st.pyplot()
    # EDA - Average Engagement Metrics by Category
    st.header("Average Engagement Metrics by Category")
    category_engagement = data.groupby('category_name')[['view_count', 'like_count', 'comment_count']].mean().sort_values(by='view_count', ascending=False)
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 10))
    
    sns.barplot(y=category_engagement.index, x=category_engagement['view_count'], ax=axes[0], palette='viridis')
    axes[0].set_title('Average View Count by Category')
    axes[0].set_xlabel('Average View Count')
    axes[0].set_ylabel('Category')
    
    sns.barplot(y=category_engagement.index, x=category_engagement['like_count'], ax=axes[1], palette='viridis')
    axes[1].set_title('Average Like Count by Category')
    axes[1].set_xlabel('Average Like Count')
    axes[1].set_ylabel('')
    
    st.pyplot(fig)

    # EDA - Distribution of Videos by Publish Hour
    st.header("Distribution of Videos by Publish Hour")
    data['publish_hour'] = data['published_at'].dt.hour
    plt.figure(figsize=(12, 6))
    sns.countplot(x='publish_hour', data=data, palette='coolwarm')
    plt.title('Distribution of Videos by Publish Hour')
    plt.xlabel('Publish Hour')
    plt.ylabel('Number of Videos')
    st.pyplot()

else:
    st.write("Please enter your API key to fetch data.")
