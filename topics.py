import streamlit as st
import requests
from datetime import datetime, timedelta

# YouTube API Key
API_KEY = "AIzaSyDwgcJiR7rBjMpUBc7ykH-36MIHcbdGgAc"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# User Inputs
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
keywords_input = st.text_area("Enter Keywords (comma-separated):", "Reddit Relationship, Affair Stories")
min_subs = st.number_input("Minimum Subscribers:", min_value=0, value=0)
max_subs = st.number_input("Maximum Subscribers:", min_value=0, value=3000)
min_views, max_views = st.slider("Select Video View Range:", 0, 1000000, (1000, 500000))

# Convert keywords input to a list
keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]

if st.button("Fetch Data"):
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        for keyword in keywords:
            st.write(f"Searching for: {keyword}")
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
            video_ids = [v["id"]["videoId"] for v in videos if "id" in v and "videoId" in v["id"]]
            channel_ids = [v["snippet"]["channelId"] for v in videos if "snippet" in v and "channelId" in v["snippet"]]
            
            stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()
            
            if "items" not in stats_data or "items" not in channel_data:
                continue
            
            for video, stat, channel in zip(videos, stats_data["items"], channel_data["items"]):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                views = int(stat["statistics"].get("viewCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))
                
                if min_subs <= subs <= max_subs and min_views <= views <= max_views:
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs
                    })
        
        if all_results:
            st.success(f"Found {len(all_results)} results!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}"
                )
                st.write("---")
        else:
            st.warning("No results found matching your criteria.")
    except Exception as e:
        st.error(f"Error: {e}")
