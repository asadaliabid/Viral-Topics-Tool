import streamlit as st
import requests
from datetime import datetime, timedelta

# YouTube API Key (Ensure it's set in Streamlit secrets)
if "AIzaSyBY3A2JiFRIBweMIcUv4oPrBNl-tQsUF4g" not in st.secrets:
    st.error("🚨 API Key missing! Add your YouTube API Key in Streamlit secrets.")
    st.stop()

API_KEY = st.secrets["YOUTUBE_API_KEY"]

# API Endpoints
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("📈 YouTube Viral Topics Finder")

# User Inputs
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
user_keywords = st.text_area("Enter Keywords (comma-separated):", placeholder="e.g., Reddit Stories, Cheating Stories, Affair Drama")

# Convert user input into a list of keywords
keywords = [kw.strip() for kw in user_keywords.split(",") if kw.strip()]

if st.button("Fetch Data") and keywords:
    try:
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        for keyword in keywords:
            st.write(f"🔍 Searching for: **{keyword}**")

            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }

            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            if "items" not in data or not data["items"]:
                st.warning(f"No videos found for: {keyword}")
                continue

            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                continue

            # Fetch video statistics
            stats_params = {
                "part": "statistics",
                "id": ",".join(video_ids),
                "key": API_KEY
            }
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"Failed to fetch video statistics for: {keyword}")
                continue

            # Fetch channel statistics
            channel_params = {
                "part": "statistics",
                "id": ",".join(channel_ids),
                "key": API_KEY
            }
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in channel_data or not channel_data["items"]:
                st.warning(f"Failed to fetch channel statistics for: {keyword}")
                continue

            stats = stats_data["items"]
            channels = channel_data["items"]

            # Collect results
            for video, stat, channel in zip(videos, stats, channels):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                thumbnail_url = video["snippet"]["thumbnails"]["medium"]["url"]
                views = int(stat["statistics"].get("viewCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))

                if subs < 3000:  # Only include channels with fewer than 3,000 subscribers
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Thumbnail": thumbnail_url,
                        "Views": views,
                        "Subscribers": subs
                    })

        # Display results
        if all_results:
            st.success(f"✅ Found {len(all_results)} viral videos!")
            for result in all_results:
                st.image(result["Thumbnail"], caption=result["Title"], use_column_width=True)
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**[Watch Video]({result['URL']})**  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}"
                )
                st.write("---")
        else:
            st.warning("No results found for channels with fewer than 3,000 subscribers.")

    except Exception as e:
        st.error(f"🚨 Error: {e}")
