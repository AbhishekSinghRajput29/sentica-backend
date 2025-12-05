import os, io, re, zipfile, math, json, shutil, calendar
from datetime import datetime
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests, pandas as pd, numpy as np, emoji, seaborn as sns
from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
plt.style.use('dark_background')

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load .env file if exists
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
YOUTUBE_ID_RE = re.compile(r"(?:v=|/)([0-9A-Za-z_-]{11}).*")

def extract_video_id(url: str) -> str | None:
    if not url: return None
    m = YOUTUBE_ID_RE.search(url)
    return m.group(1) if m else None

def fetch_video_info(video_id: str) -> dict:
    if not YOUTUBE_API_KEY:
        return {"title": "", "channel": "", "published_at": "", "view_count": "0", "like_count": "0", "comment_count": "0"}
    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/videos",
            params={"part": "snippet,statistics", "id": video_id, "key": YOUTUBE_API_KEY}, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if data.get("items"):
                sn = data["items"][0]["snippet"]
                st = data["items"][0]["statistics"]
                return {
                    "title": sn.get("title", ""),
                    "channel": sn.get("channelTitle", ""),
                    "published_at": sn.get("publishedAt", ""),
                    "view_count": st.get("viewCount", "0"),
                    "like_count": st.get("likeCount", "0"),
                    "comment_count": st.get("commentCount", "0")
                }
    except Exception as e:
        print("Error fetching info:", e)
    return {"title": "", "channel": "", "published_at": "", "view_count": "0", "like_count": "0", "comment_count": "0"}

def fetch_comments(video_id: str) -> list[dict]:
    """Fetch ALL comments with no limit"""
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY is not set")
    
    comments, token, fetched = [], None, 0
    print(f"Starting to fetch ALL comments for video {video_id}...")
    
    while True:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": YOUTUBE_API_KEY,
            "maxResults": 100,
            "order": "relevance"
        }
        if token:
            params["pageToken"] = token
            
        r = requests.get("https://www.googleapis.com/youtube/v3/commentThreads", params=params, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"YouTube API error: {r.status_code} - {r.text}")
            
        data = r.json()
        items = data.get("items", [])
        
        for it in items:
            sn = it["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": sn.get("authorDisplayName", ""),
                "text": sn.get("textDisplay", "") or "",
                "likes": sn.get("likeCount", 0),
                "published_at": sn.get("publishedAt", "")
            })
        
        fetched += len(items)
        print(f"Fetched {fetched} comments so far...")
        
        token = data.get("nextPageToken")
        if not token:
            break
            
    print(f"Completed fetching {fetched} total comments")
    return comments

def clean_text(t: str) -> str:
    t = re.sub(r"http\S+", "", t)
    t = re.sub(r"[@#]\S+", "", t)
    t = re.sub(r"[^A-Za-z0-9\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()

def extract_emojis(text: str) -> list:
    return [c for c in text if c in emoji.EMOJI_DATA]

def analyze_sentiment(text: str) -> tuple[float, float, str]:
    if not text.strip():
        return 0.0, 0.0, "Neutral"
    blob = TextBlob(text)
    p, s = blob.sentiment.polarity, blob.sentiment.subjectivity
    return p, s, "Positive" if p > 0.1 else "Negative" if p < -0.1 else "Neutral"

def safe_dt_naive(dt_str: str) -> str:
    try:
        ts = pd.to_datetime(dt_str, utc=True, errors="coerce")
        if pd.isna(ts):
            return ""
        return ts.tz_localize(None).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ""

def parse_datetime_features(dt_str: str) -> dict:
    try:
        ts = pd.to_datetime(dt_str, utc=True, errors="coerce")
        if pd.isna(ts):
            return {"hour": 0, "day_of_week": 0, "month": 1}
        return {"hour": ts.hour, "day_of_week": ts.dayofweek, "month": ts.month}
    except:
        return {"hour": 0, "day_of_week": 0, "month": 1}

def build_zip():
    """Build comprehensive ZIP file"""
    zip_path = os.path.join(OUTPUT_DIR, "outputs.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in os.listdir(OUTPUT_DIR):
            if f == "outputs.zip":
                continue
            file_path = os.path.join(OUTPUT_DIR, f)
            if os.path.isfile(file_path):
                zf.write(file_path, arcname=f)
    return "outputs.zip"

# ---------------------------- SAVE FUNCTIONS ----------------------------

def save_core_data(df, video_info):
    """Save core data exports"""
    files = []
    
    # JSON export
    df.to_json(os.path.join(OUTPUT_DIR, "analysis.json"), orient="records", indent=2, force_ascii=False)
    files.append("analysis.json")
    
    # CSV export
    df.to_csv(os.path.join(OUTPUT_DIR, "analysis.csv"), index=False)
    files.append("analysis.csv")
    
    # Excel export
    df_excel = df.copy()
    if "published_at" in df_excel:
        df_excel["published_at"] = df_excel["published_at"].apply(safe_dt_naive)
    with pd.ExcelWriter(os.path.join(OUTPUT_DIR, "analysis.xlsx"), engine="openpyxl") as w:
        df_excel.to_excel(w, index=False, sheet_name="comments")
    files.append("analysis.xlsx")
    
    # Text dump
    with open(os.path.join(OUTPUT_DIR, "analysis.txt"), "w", encoding="utf8") as f:
        f.write(f"YouTube Video Analysis\n")
        f.write(f"Title: {video_info.get('title', 'N/A')}\n")
        f.write(f"Channel: {video_info.get('channel', 'N/A')}\n")
        f.write(f"Total Comments: {len(df)}\n\n")
        for _, r in df.iterrows():
            f.write(f"Author: {r['author']}\n")
            f.write(f"Comment: {r['text']}\n")
            f.write(f"Sentiment: {r['sentiment']} (Polarity: {r['polarity']:.2f})\n")
            f.write(f"Likes: {r['likes']}\n")
            f.write(f"Published: {r['published_at']}\n")
            f.write("-" * 50 + "\n")
    files.append("analysis.txt")
    
    # Metadata
    metadata = {
        "video_info": video_info,
        "analysis_date": datetime.now().isoformat(),
        "total_comments": len(df),
        "sentiment_distribution": df["sentiment"].value_counts().to_dict() if not df.empty else {}
    }
    with open(os.path.join(OUTPUT_DIR, "metadata.json"), "w", encoding="utf8") as f:
        json.dump(metadata, f, indent=2)
    files.append("metadata.json")
    
    return files

def save_sentiment_visualizations(df):
    """Save sentiment analysis visualizations"""
    files = []
    if df.empty:
        return files
        
    plt.rcParams.update({
        'figure.facecolor': '#1a1f3a',
        'axes.facecolor': '#1a1f3a',
        'text.color': 'white',
        'axes.labelcolor': 'white',
        'xtick.color': 'white',
        'ytick.color': 'white'
    })
    
    counts = df["sentiment"].value_counts()
    
    # Sentiment bar chart
    if not counts.empty:
        plt.figure(figsize=(10, 6))
        colors = ['#00d4ff', '#ff006e', '#7b2cbf']
        bars = plt.bar(counts.index, counts.values, color=colors[:len(counts)])
        plt.title("Sentiment Distribution", fontsize=16, color='white', pad=20)
        plt.xlabel("Sentiment", fontsize=12)
        plt.ylabel("Count", fontsize=12)
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', color='white')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "sentiment_bar.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("sentiment_bar.png")
    
    # Sentiment pie chart
    if not counts.empty:
        plt.figure(figsize=(8, 8))
        colors = ['#00d4ff', '#ff006e', '#7b2cbf']
        plt.pie(counts.values, labels=counts.index, autopct='%1.1f%%', 
               colors=colors[:len(counts)], startangle=90, textprops={'color': 'white'})
        plt.title("Sentiment Distribution", fontsize=16, color='white', pad=20)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "sentiment_pie.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("sentiment_pie.png")
    
    # Sentiment ratios CSV
    total = counts.sum()
    if total > 0:
        ratios = {
            'positive_percentage': (counts.get('Positive', 0) / total) * 100,
            'negative_percentage': (counts.get('Negative', 0) / total) * 100,
            'neutral_percentage': (counts.get('Neutral', 0) / total) * 100
        }
        pd.DataFrame([ratios]).to_csv(os.path.join(OUTPUT_DIR, "sentiment_ratio.csv"), index=False)
        files.append("sentiment_ratio.csv")
    
    # Polarity histogram
    if 'polarity' in df.columns:
        plt.figure(figsize=(10, 6))
        plt.hist(df['polarity'], bins=30, color='#00d4ff', alpha=0.7, edgecolor='white')
        plt.title("Polarity Distribution", fontsize=16, color='white', pad=20)
        plt.xlabel("Polarity (-1 to 1)", fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.axvline(df['polarity'].mean(), color='#ff006e', linestyle='--', 
                   label=f'Mean: {df["polarity"].mean():.3f}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "avg_polarity_hist.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("avg_polarity_hist.png")
    
    # Subjectivity histogram
    if 'subjectivity' in df.columns:
        plt.figure(figsize=(10, 6))
        plt.hist(df['subjectivity'], bins=30, color='#7b2cbf', alpha=0.7, edgecolor='white')
        plt.title("Subjectivity Distribution", fontsize=16, color='white', pad=20)
        plt.xlabel("Subjectivity (0 to 1)", fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.axvline(df['subjectivity'].mean(), color='#ff006e', linestyle='--', 
                   label=f'Mean: {df["subjectivity"].mean():.3f}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "avg_subjectivity_hist.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("avg_subjectivity_hist.png")
    
    return files

def save_advanced_visualizations(df):
    """Save advanced relationship visualizations"""
    files = []
    if df.empty:
        return files
    
    # 1. Likes vs Sentiment (Box plot)
    if 'likes' in df.columns and 'sentiment' in df.columns:
        plt.figure(figsize=(12, 7))
        sentiment_order = ['Negative', 'Neutral', 'Positive']
        colors = {'Negative': '#ff006e', 'Neutral': '#7b2cbf', 'Positive': '#00d4ff'}
        
        data_to_plot = [df[df['sentiment'] == sent]['likes'].values for sent in sentiment_order if sent in df['sentiment'].values]
        labels_to_plot = [sent for sent in sentiment_order if sent in df['sentiment'].values]
        
        bp = plt.boxplot(data_to_plot, tick_labels=labels_to_plot, patch_artist=True)
        for patch, label in zip(bp['boxes'], labels_to_plot):
            patch.set_facecolor(colors[label])
            patch.set_alpha(0.7)
        
        plt.title("Likes Distribution by Sentiment", fontsize=16, color='white', pad=20)
        plt.xlabel("Sentiment", fontsize=12)
        plt.ylabel("Number of Likes", fontsize=12)
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "likes_vs_sentiment.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("likes_vs_sentiment.png")
        print("Created likes vs sentiment visualization")
    
    # 2. Polarity vs Likes (Scatter plot)
    if 'polarity' in df.columns and 'likes' in df.columns:
        plt.figure(figsize=(12, 7))
        scatter = plt.scatter(df['polarity'], df['likes'], c=df['likes'], 
                             cmap='plasma', alpha=0.6, edgecolors='white', linewidth=0.5)
        plt.colorbar(scatter, label='Likes')
        plt.title("Polarity vs Likes", fontsize=16, color='white', pad=20)
        plt.xlabel("Polarity (-1 to 1)", fontsize=12)
        plt.ylabel("Number of Likes", fontsize=12)
        plt.axvline(0, color='white', linestyle='--', alpha=0.3, label='Neutral')
        plt.legend()
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "polarity_vs_likes.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("polarity_vs_likes.png")
        print("Created polarity vs likes visualization")
    
    # 3. Sentiment vs Comment Length (Box plot)
    if 'length' in df.columns and 'sentiment' in df.columns:
        plt.figure(figsize=(12, 7))
        sentiment_order = ['Negative', 'Neutral', 'Positive']
        colors = {'Negative': '#ff006e', 'Neutral': '#7b2cbf', 'Positive': '#00d4ff'}
        
        data_to_plot = [df[df['sentiment'] == sent]['length'].values for sent in sentiment_order if sent in df['sentiment'].values]
        labels_to_plot = [sent for sent in sentiment_order if sent in df['sentiment'].values]
        
        bp = plt.boxplot(data_to_plot, tick_labels=labels_to_plot, patch_artist=True)
        for patch, label in zip(bp['boxes'], labels_to_plot):
            patch.set_facecolor(colors[label])
            patch.set_alpha(0.7)
        
        plt.title("Comment Length Distribution by Sentiment", fontsize=16, color='white', pad=20)
        plt.xlabel("Sentiment", fontsize=12)
        plt.ylabel("Comment Length (characters)", fontsize=12)
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "sentiment_vs_comment_length.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("sentiment_vs_comment_length.png")
        print("Created sentiment vs comment length visualization")
    
    # 4. Comment Length Distribution (Enhanced histogram)
    if 'length' in df.columns:
        plt.figure(figsize=(12, 7))
        plt.hist(df['length'], bins=50, color='#00d4ff', alpha=0.7, edgecolor='white')
        plt.axvline(df['length'].mean(), color='#ff006e', linestyle='--', linewidth=2,
                   label=f'Mean: {df["length"].mean():.1f}')
        plt.axvline(df['length'].median(), color='#7b2cbf', linestyle='--', linewidth=2,
                   label=f'Median: {df["length"].median():.1f}')
        plt.title("Comment Length Distribution", fontsize=16, color='white', pad=20)
        plt.xlabel("Comment Length (characters)", fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.legend()
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "comment_length_distribution.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("comment_length_distribution.png")
        print("Created comment length distribution visualization")
    
    return files

def save_emoji_analysis(df):
    """Save emoji analysis - frequency data and visualizations"""
    files = []
    if df.empty or 'emojis' not in df.columns:
        return files
    
    # Collect all emojis
    all_emojis = []
    for emoji_list in df['emojis']:
        if emoji_list:
            all_emojis.extend(emoji_list)
    
    if not all_emojis:
        print("No emojis found in comments")
        return files
    
    # Emoji frequency analysis
    emoji_freq = Counter(all_emojis).most_common(50)
    if emoji_freq:
        # Save emoji frequency CSV
        emoji_df = pd.DataFrame(emoji_freq, columns=['emoji', 'frequency'])
        emoji_df.to_csv(os.path.join(OUTPUT_DIR, "emoji_frequency.csv"), index=False)
        files.append("emoji_frequency.csv")
        print(f"Saved emoji frequency CSV with {len(emoji_freq)} emojis")
        
        # Create emoji frequency bar chart
        if len(emoji_freq) >= 10:
            plt.figure(figsize=(12, 8))
            top_emojis = emoji_freq[:20]
            emojis, freqs = zip(*top_emojis)
            
            plt.barh(range(len(emojis)), freqs, color='#ff006e')
            plt.yticks(range(len(emojis)), emojis, fontsize=16)
            plt.title("Top 20 Most Frequent Emojis", fontsize=16, color='white', pad=20)
            plt.xlabel("Frequency", fontsize=12)
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, "emoji_frequency.png"), 
                       facecolor='#1a1f3a', edgecolor='none', dpi=150)
            plt.close()
            files.append("emoji_frequency.png")
            print("Created emoji frequency chart")
    
    # Create emoji word cloud
    if all_emojis and len(all_emojis) > 0:
        emoji_text = " ".join(all_emojis)
        # Check if we have actual content
        if emoji_text.strip() and len(emoji_text.replace(" ", "")) > 0:
            try:
                # Create a simple frequency-based visualization instead
                from matplotlib import font_manager
                
                wc = WordCloud(
                    width=1200, 
                    height=800, 
                    background_color='#1a1f3a',
                    colormap='plasma',
                    max_words=100,
                    relative_scaling=0.5,
                    min_font_size=20,
                    regexp=r"\S+",  # Match any non-whitespace
                    collocations=False
                ).generate_from_frequencies(dict(Counter(all_emojis)))
                
                plt.figure(figsize=(15, 10))
                plt.imshow(wc, interpolation='bilinear')
                plt.axis('off')
                plt.title("Emoji Word Cloud", fontsize=20, color='white', pad=20)
                plt.tight_layout()
                plt.savefig(os.path.join(OUTPUT_DIR, "emoji_wordcloud.png"), 
                           facecolor='#1a1f3a', edgecolor='none', dpi=150, bbox_inches='tight')
                plt.close()
                files.append("emoji_wordcloud.png")
                print("Created emoji word cloud")
            except Exception as e:
                print(f"Error creating emoji wordcloud: {e}")
                # Create alternative emoji visualization
                try:
                    emoji_counter = Counter(all_emojis)
                    top_15 = emoji_counter.most_common(15)
                    if top_15:
                        emojis_list, counts_list = zip(*top_15)
                        
                        plt.figure(figsize=(12, 8))
                        plt.scatter(range(len(emojis_list)), counts_list, 
                                   s=[c*50 for c in counts_list], 
                                   c=counts_list, cmap='plasma', alpha=0.6)
                        for i, (emoji, count) in enumerate(top_15):
                            plt.annotate(emoji, (i, count), fontsize=20, ha='center', va='center')
                        plt.title("Emoji Usage Bubble Chart", fontsize=16, color='white', pad=20)
                        plt.xlabel("Emoji Rank", fontsize=12)
                        plt.ylabel("Frequency", fontsize=12)
                        plt.tight_layout()
                        plt.savefig(os.path.join(OUTPUT_DIR, "emoji_wordcloud.png"), 
                                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
                        plt.close()
                        files.append("emoji_wordcloud.png")
                        print("Created emoji bubble chart as alternative")
                except Exception as e2:
                    print(f"Could not create emoji visualization: {e2}")
    
    return files

def save_wordclouds(df):
    """Save word cloud visualizations"""
    files = []
    if df.empty:
        return files
        
    stop = set(STOPWORDS)
    
    def create_wordcloud(text, filename, title):
        if not text or not text.strip():
            print(f"Skipping {filename} - no text content")
            return None
        
        words_for_cloud = [word for word in text.split() if len(word) > 1]
        if not words_for_cloud:
            print(f"Skipping {filename} - no meaningful words after cleaning")
            return None
            
        try:
            wc = WordCloud(width=1200, height=800, background_color='#1a1f3a', 
                          stopwords=stop, colormap='plasma', max_words=100).generate(text)
            plt.figure(figsize=(15, 10))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.title(title, fontsize=20, color='white', pad=20)
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, filename), 
                       facecolor='#1a1f3a', edgecolor='none', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Successfully created {filename}")
            return filename
        except ValueError as e:
            print(f"Error creating {filename}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error creating {filename}: {e}")
            return None
    
    # Overall wordcloud
    all_text = " ".join(df["cleaned"].tolist())
    if all_text.strip():
        result = create_wordcloud(all_text, "wordcloud.png", "Overall Word Cloud")
        if result:
            files.append(result)

    
    return files

def save_author_analysis(df):
    """Save author and engagement analysis"""
    files = []
    if df.empty:
        return files
    
    # Top authors by comment count
    top_authors = df['author'].value_counts().head(20)
    if not top_authors.empty:
        top_authors.to_csv(os.path.join(OUTPUT_DIR, "top_authors.csv"))
        files.append("top_authors.csv")
        
        # Top authors chart
        plt.figure(figsize=(12, 8))
        top_authors.head(10).plot(kind='bar', color='#00d4ff')
        plt.title("Top 10 Authors by Comment Count", fontsize=16, color='white', pad=20)
        plt.xlabel("Author", fontsize=12)
        plt.ylabel("Number of Comments", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "top_authors.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("top_authors.png")
    
    # Top liked comments
    top_liked = df.nlargest(20, 'likes')[['author', 'text', 'likes', 'sentiment']]
    if not top_liked.empty:
        top_liked.to_csv(os.path.join(OUTPUT_DIR, "top_liked_comments.csv"), index=False)
        files.append("top_liked_comments.csv")
        
        # Top liked comments chart
        plt.figure(figsize=(12, 8))
        top_10_liked = top_liked.head(10)
        plt.barh(range(len(top_10_liked)), top_10_liked['likes'], color='#7b2cbf')
        plt.yticks(range(len(top_10_liked)), 
                  [f"{row['author'][:15]}..." if len(row['author']) > 15 else row['author'] 
                   for _, row in top_10_liked.iterrows()])
        plt.title("Top 10 Most Liked Comments", fontsize=16, color='white', pad=20)
        plt.xlabel("Likes", fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "top_liked_comments.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("top_liked_comments.png")
    
    # Engagement stats
    engagement_stats = {
        'total_likes': df['likes'].sum(),
        'avg_likes_per_comment': df['likes'].mean(),
        'median_likes': df['likes'].median(),
        'max_likes': df['likes'].max(),
        'comments_with_likes': len(df[df['likes'] > 0]),
        'engagement_rate': len(df[df['likes'] > 0]) / len(df) if len(df) > 0 else 0
    }
    pd.DataFrame([engagement_stats]).to_csv(os.path.join(OUTPUT_DIR, "engagement_stats.csv"), index=False)
    files.append("engagement_stats.csv")
    
    return files

def save_temporal_analysis(df):
    """Save temporal analysis charts"""
    files = []
    if df.empty or 'hour' not in df.columns:
        return files
    
    # Hourly distribution
    hourly_counts = df['hour'].value_counts().sort_index()
    if not hourly_counts.empty:
        plt.figure(figsize=(12, 6))
        plt.bar(hourly_counts.index, hourly_counts.values, color='#00d4ff', alpha=0.7)
        plt.title("Comments by Hour of Day", fontsize=16, color='white', pad=20)
        plt.xlabel("Hour (24-hour format)", fontsize=12)
        plt.ylabel("Number of Comments", fontsize=12)
        plt.xticks(range(0, 24))
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "hourly_distribution.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("hourly_distribution.png")
    
    # Daily distribution
    if 'day_of_week' in df.columns:
        daily_counts = df['day_of_week'].value_counts().sort_index()
        if not daily_counts.empty:
            plt.figure(figsize=(10, 6))
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            plt.bar([days[i] for i in daily_counts.index], daily_counts.values, color='#7b2cbf', alpha=0.7)
            plt.title("Comments by Day of Week", fontsize=16, color='white', pad=20)
            plt.xlabel("Day of Week", fontsize=12)
            plt.ylabel("Number of Comments", fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, "daily_distribution.png"), 
                       facecolor='#1a1f3a', edgecolor='none', dpi=150)
            plt.close()
            files.append("daily_distribution.png")
    
    # Monthly distribution
    if 'month' in df.columns:
        monthly_counts = df['month'].value_counts().sort_index()
        if not monthly_counts.empty:
            plt.figure(figsize=(12, 6))
            month_names = [calendar.month_abbr[i] for i in monthly_counts.index]
            plt.bar(month_names, monthly_counts.values, color='#ff006e', alpha=0.7)
            plt.title("Comments by Month", fontsize=16, color='white', pad=20)
            plt.xlabel("Month", fontsize=12)
            plt.ylabel("Number of Comments", fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, "monthly_distribution.png"), 
                       facecolor='#1a1f3a', edgecolor='none', dpi=150)
            plt.close()
            files.append("monthly_distribution.png")
    
    return files

def save_timeline_analysis(df):
    """Save timeline visualizations"""
    files = []
    if df.empty or 'published_at' not in df.columns:
        return files
    
    # Convert published_at to datetime
    df_time = df.copy()
    df_time['datetime'] = pd.to_datetime(df_time['published_at'], errors='coerce')
    df_time = df_time.dropna(subset=['datetime'])
    
    if df_time.empty:
        return files
    
    df_time = df_time.sort_values('datetime')
    
    # Comment timeline (cumulative)
    plt.figure(figsize=(14, 7))
    df_time['cumulative'] = range(1, len(df_time) + 1)
    plt.plot(df_time['datetime'], df_time['cumulative'], color='#00d4ff', linewidth=2)
    plt.fill_between(df_time['datetime'], df_time['cumulative'], alpha=0.3, color='#00d4ff')
    plt.title("Cumulative Comment Timeline", fontsize=16, color='white', pad=20)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Total Comments", fontsize=12)
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "comment_timeline.png"), 
               facecolor='#1a1f3a', edgecolor='none', dpi=150)
    plt.close()
    files.append("comment_timeline.png")
    
    # Engagement timeline
    if 'likes' in df_time.columns:
        plt.figure(figsize=(14, 7))
        
        # Group by date and sum likes
        df_time['date'] = df_time['datetime'].dt.date
        daily_engagement = df_time.groupby('date').agg({
            'likes': 'sum',
            'text': 'count'
        }).reset_index()
        daily_engagement.columns = ['date', 'total_likes', 'comment_count']
        
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Total Likes', color='#ff006e', fontsize=12)
        ax1.plot(daily_engagement['date'], daily_engagement['total_likes'], 
                color='#ff006e', linewidth=2, label='Likes')
        ax1.tick_params(axis='y', labelcolor='#ff006e')
        ax1.fill_between(daily_engagement['date'], daily_engagement['total_likes'], 
                        alpha=0.3, color='#ff006e')
        
        ax2 = ax1.twinx()
        ax2.set_ylabel('Comment Count', color='#00d4ff', fontsize=12)
        ax2.plot(daily_engagement['date'], daily_engagement['comment_count'], 
                color='#00d4ff', linewidth=2, label='Comments', linestyle='--')
        ax2.tick_params(axis='y', labelcolor='#00d4ff')
        
        plt.title("Engagement Timeline (Likes vs Comments)", fontsize=16, color='white', pad=20)
        fig.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "engagement_timeline.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("engagement_timeline.png")
    
    return files

def save_linguistic_analysis(df):
    """Save linguistic analysis"""
    files = []
    if df.empty:
        return files
    
    # Comment length histogram
    if 'length' in df.columns:
        plt.figure(figsize=(10, 6))
        plt.hist(df['length'], bins=30, color='#00d4ff', alpha=0.7, edgecolor='white')
        plt.title("Comment Length Distribution", fontsize=16, color='white', pad=20)
        plt.xlabel("Characters", fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.axvline(df['length'].mean(), color='#ff006e', linestyle='--', 
                   label=f'Mean: {df["length"].mean():.1f}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "comment_length_hist.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("comment_length_hist.png")
    
    # Word frequency analysis
    all_words = " ".join(df["cleaned"]).split()
    if all_words:
        word_freq = Counter(all_words).most_common(50)
        pd.DataFrame(word_freq, columns=['word', 'frequency']).to_csv(
            os.path.join(OUTPUT_DIR, "word_frequency.csv"), index=False)
        files.append("word_frequency.csv")
        
        # Word frequency chart
        if len(word_freq) >= 20:
            plt.figure(figsize=(12, 8))
            top_20 = word_freq[:20]
            words, freqs = zip(*top_20)
            plt.barh(range(len(words)), freqs, color='#7b2cbf')
            plt.yticks(range(len(words)), words)
            plt.title("Top 20 Most Frequent Words", fontsize=16, color='white', pad=20)
            plt.xlabel("Frequency", fontsize=12)
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, "word_frequency.png"), 
                       facecolor='#1a1f3a', edgecolor='none', dpi=150)
            plt.close()
            files.append("word_frequency.png")
        
        # Bigram analysis
        bigrams = []
        for i in range(len(all_words) - 1):
            bigrams.append(f"{all_words[i]} {all_words[i+1]}")
        
        if bigrams:
            bigram_freq = Counter(bigrams).most_common(30)
            pd.DataFrame(bigram_freq, columns=['bigram', 'frequency']).to_csv(
                os.path.join(OUTPUT_DIR, "bigram_frequency.csv"), index=False)
            files.append("bigram_frequency.csv")
            
            # Bigram frequency chart
            if len(bigram_freq) >= 15:
                plt.figure(figsize=(12, 10))
                top_15 = bigram_freq[:15]
                bigrams_text, freqs = zip(*top_15)
                plt.barh(range(len(bigrams_text)), freqs, color='#ff006e')
                plt.yticks(range(len(bigrams_text)), bigrams_text)
                plt.title("Top 15 Most Frequent Bigrams", fontsize=16, color='white', pad=20)
                plt.xlabel("Frequency", fontsize=12)
                plt.gca().invert_yaxis()
                plt.tight_layout()
                plt.savefig(os.path.join(OUTPUT_DIR, "bigram_frequency.png"), 
                           facecolor='#1a1f3a', edgecolor='none', dpi=150)
                plt.close()
                files.append("bigram_frequency.png")
    
    return files

def save_model_evaluation(df):
    """Save model evaluation metrics with confusion matrix"""
    files = []
    if df.empty or 'sentiment' not in df.columns:
        return files
    
    # Classification metrics
    sentiment_counts = df['sentiment'].value_counts()
    metrics = {
        'total_samples': int(len(df)),
        'positive_count': int(sentiment_counts.get('Positive', 0)),
        'negative_count': int(sentiment_counts.get('Negative', 0)),
        'neutral_count': int(sentiment_counts.get('Neutral', 0)),
        'positive_percentage': float((sentiment_counts.get('Positive', 0) / len(df)) * 100),
        'negative_percentage': float((sentiment_counts.get('Negative', 0) / len(df)) * 100),
        'neutral_percentage': float((sentiment_counts.get('Neutral', 0) / len(df)) * 100),
        'average_polarity': float(df['polarity'].mean()) if 'polarity' in df.columns else 0.0,
        'polarity_std': float(df['polarity'].std()) if 'polarity' in df.columns else 0.0
    }
    
    # Save metrics as JSON
    with open(os.path.join(OUTPUT_DIR, "classification_metrics.json"), 'w') as f:
        json.dump(metrics, f, indent=2)
    files.append("classification_metrics.json")
    
    # Save metrics as CSV
    pd.DataFrame([metrics]).to_csv(os.path.join(OUTPUT_DIR, "classification_metrics.csv"), index=False)
    files.append("classification_metrics.csv")
    
    # Confusion matrix visualization
    if 'polarity' in df.columns:
        plt.figure(figsize=(10, 8))
        
        # Create pseudo confusion matrix based on polarity thresholds
        labels = ['Negative', 'Neutral', 'Positive']
        matrix = np.zeros((3, 3))
        
        for idx, row in df.iterrows():
            # True label based on polarity
            if row['polarity'] > 0.1:
                true_idx = 2  # Positive
            elif row['polarity'] < -0.1:
                true_idx = 0  # Negative
            else:
                true_idx = 1  # Neutral
            
            # Predicted label
            pred_idx = ['Negative', 'Neutral', 'Positive'].index(row['sentiment'])
            matrix[true_idx, pred_idx] += 1
        
        if matrix.sum() > 0:
            sns.heatmap(matrix, annot=True, fmt='g', cmap='Blues', 
                       xticklabels=labels, yticklabels=labels,
                       cbar_kws={'label': 'Count'})
            plt.title("Sentiment Classification Confusion Matrix", fontsize=16, color='white', pad=20)
            plt.xlabel("Predicted Sentiment", fontsize=12)
            plt.ylabel("True Sentiment (based on polarity)", fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix.png"), 
                       facecolor='#1a1f3a', edgecolor='none', dpi=150)
            plt.close()
            files.append("confusion_matrix.png")
            print("Created confusion matrix visualization")
            
            # Normalized confusion matrix
            plt.figure(figsize=(10, 8))
            matrix_normalized = matrix / matrix.sum(axis=1, keepdims=True)
            sns.heatmap(matrix_normalized, annot=True, fmt='.2%', cmap='Greens', 
                       xticklabels=labels, yticklabels=labels,
                       cbar_kws={'label': 'Percentage'})
            plt.title("Normalized Confusion Matrix (by Row)", fontsize=16, color='white', pad=20)
            plt.xlabel("Predicted Sentiment", fontsize=12)
            plt.ylabel("True Sentiment", fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix_normalized.png"), 
                       facecolor='#1a1f3a', edgecolor='none', dpi=150)
            plt.close()
            files.append("confusion_matrix_normalized.png")
            print("Created normalized confusion matrix")
            
            # Precision-focused matrix
            plt.figure(figsize=(10, 8))
            matrix_precision = matrix / matrix.sum(axis=0, keepdims=True)
            sns.heatmap(matrix_precision, annot=True, fmt='.2%', cmap='Purples', 
                       xticklabels=labels, yticklabels=labels,
                       cbar_kws={'label': 'Precision'})
            plt.title("Precision Matrix (by Column)", fontsize=16, color='white', pad=20)
            plt.xlabel("Predicted Sentiment", fontsize=12)
            plt.ylabel("True Sentiment", fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix_precision.png"), 
                       facecolor='#1a1f3a', edgecolor='none', dpi=150)
            plt.close()
            files.append("confusion_matrix_precision.png")
            print("Created precision-focused confusion matrix")
    
    return files

def save_advanced_model_evaluation(df):
    """Save ROC and PR curves"""
    files = []
    if df.empty or 'sentiment' not in df.columns or 'polarity' not in df.columns:
        return files
    
    try:
        from sklearn.preprocessing import label_binarize
        from sklearn.metrics import roc_curve, auc, precision_recall_curve
        
        # Prepare data
        y_true = df['sentiment'].map({'Negative': 0, 'Neutral': 1, 'Positive': 2})
        y_true = y_true.dropna()
        
        if len(y_true) < 10:
            return files
        
        # Use polarity as probability scores
        y_scores = df.loc[y_true.index, 'polarity']
        
        # Binarize labels for multiclass
        y_true_bin = label_binarize(y_true, classes=[0, 1, 2])
        n_classes = y_true_bin.shape[1]
        
        # ROC Curve
        plt.figure(figsize=(10, 8))
        colors = ['#ff006e', '#7b2cbf', '#00d4ff']
        labels = ['Negative', 'Neutral', 'Positive']
        
        for i, color, label in zip(range(n_classes), colors, labels):
            y_score_binary = (y_scores > (i - 1) * 0.6).astype(int)
            fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_score_binary)
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, color=color, linewidth=2, 
                    label=f'{label} (AUC = {roc_auc:.2f})')
        
        plt.plot([0, 1], [0, 1], 'white', linestyle='--', linewidth=1, alpha=0.5)
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title('ROC Curve - Multiclass Sentiment', fontsize=16, color='white', pad=20)
        plt.legend(loc="lower right")
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "roc_curve.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("roc_curve.png")
        
        # PR Curve
        plt.figure(figsize=(10, 8))
        for i, color, label in zip(range(n_classes), colors, labels):
            y_score_binary = (y_scores > (i - 1) * 0.6).astype(int)
            precision, recall, _ = precision_recall_curve(y_true_bin[:, i], y_score_binary)
            plt.plot(recall, precision, color=color, linewidth=2, label=label)
        
        plt.xlabel('Recall', fontsize=12)
        plt.ylabel('Precision', fontsize=12)
        plt.title('Precision-Recall Curve', fontsize=16, color='white', pad=20)
        plt.legend(loc="best")
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "pr_curve.png"), 
                   facecolor='#1a1f3a', edgecolor='none', dpi=150)
        plt.close()
        files.append("pr_curve.png")
        
    except Exception as e:
        print(f"Error creating ROC/PR curves: {e}")
    
    return files

def save_executive_summary(df, video_info, meta):
    """Save executive summary document"""
    files = []
    
    try:
        summary = f"""
EXECUTIVE SUMMARY
YouTube Sentiment Analysis Report

═══════════════════════════════════════════════════════════════════

VIDEO INFORMATION
─────────────────────────────────────────────────────────────────
Title:          {video_info.get('title', 'N/A')}
Channel:        {video_info.get('channel', 'N/A')}
Video ID:       {meta.get('video_id', 'N/A')}
Views:          {video_info.get('view_count', 'N/A')}
Likes:          {video_info.get('like_count', 'N/A')}
Published:      {video_info.get('published_at', 'N/A')}

ANALYSIS OVERVIEW
─────────────────────────────────────────────────────────────────
Analysis Date:  {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}
Total Comments: {meta.get('total_comments', 0):,}
Data Quality:   {'Excellent' if meta.get('total_comments', 0) > 500 else 'Good' if meta.get('total_comments', 0) > 100 else 'Limited'}

SENTIMENT DISTRIBUTION
─────────────────────────────────────────────────────────────────
Positive:       {meta.get('pos', 0):,} comments ({(meta.get('pos', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)
Negative:       {meta.get('neg', 0):,} comments ({(meta.get('neg', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)
Neutral:        {meta.get('neu', 0):,} comments ({(meta.get('neu', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)

SENTIMENT METRICS
─────────────────────────────────────────────────────────────────
Average Polarity:       {meta.get('avg_polarity', 0):.3f}
Polarity Interpretation: {'Strongly Positive' if meta.get('avg_polarity', 0) > 0.3 else 'Positive' if meta.get('avg_polarity', 0) > 0.1 else 'Negative' if meta.get('avg_polarity', 0) < -0.1 else 'Strongly Negative' if meta.get('avg_polarity', 0) < -0.3 else 'Neutral'}
Average Subjectivity:   {meta.get('avg_subjectivity', 0):.3f}
Average Comment Length: {meta.get('avg_comment_length', 0):.1f} characters

ENGAGEMENT ANALYSIS
─────────────────────────────────────────────────────────────────
Total Likes:            {meta.get('total_likes', 0):,}
Avg Likes/Comment:      {(meta.get('total_likes', 0) / max(1, meta.get('total_comments', 1))):.2f}
Engagement Level:       {'Very High' if meta.get('total_comments', 0) > 1000 else 'High' if meta.get('total_comments', 0) > 500 else 'Medium' if meta.get('total_comments', 0) > 100 else 'Low'}

KEY INSIGHTS
─────────────────────────────────────────────────────────────────
• Overall Sentiment: The video received {'predominantly positive' if (meta.get('pos', 0)/max(1, meta.get('total_comments', 1))) > 0.6 else 'mostly positive' if (meta.get('pos', 0)/max(1, meta.get('total_comments', 1))) > 0.5 else 'mixed' if (meta.get('neg', 0)/max(1, meta.get('total_comments', 1))) < 0.4 else 'negative'} feedback

• Audience Engagement: {'Strong community interaction' if meta.get('total_comments', 0) > 500 else 'Moderate engagement' if meta.get('total_comments', 0) > 100 else 'Limited engagement'} with {meta.get('total_comments', 0):,} total comments

• Content Reception: {'High approval' if (meta.get('pos', 0)/max(1, meta.get('total_comments', 1))) > 0.7 else 'Generally well-received' if (meta.get('pos', 0)/max(1, meta.get('total_comments', 1))) > 0.5 else 'Polarizing content' if (meta.get('neg', 0)/max(1, meta.get('total_comments', 1))) > 0.3 else 'Neutral reception'} based on sentiment distribution

RECOMMENDATIONS
─────────────────────────────────────────────────────────────────
{'• Continue this content strategy - audience response is very positive' if (meta.get('pos', 0)/max(1, meta.get('total_comments', 1))) > 0.7 else '• Address negative feedback - consider community concerns' if (meta.get('neg', 0)/max(1, meta.get('total_comments', 1))) > 0.4 else '• Audience is engaged - consider increasing content frequency'}
• Monitor temporal patterns to optimize posting schedule
• Engage with top commenters to build community loyalty

═══════════════════════════════════════════════════════════════════
Generated by SENTICA - Advanced YouTube Sentiment Analysis
Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═══════════════════════════════════════════════════════════════════
"""
        
        with open(os.path.join(OUTPUT_DIR, "executive_summary.docx"), 'w', encoding='utf-8') as f:
            f.write(summary)
        files.append("executive_summary.docx")
        
    except Exception as e:
        print(f"Error creating executive summary: {e}")
    
    return files

def create_reports(df, video_info, meta, all_files):
    """Create comprehensive reports"""
    files = []
    
    # PDF Report
    pdf_path = os.path.join(OUTPUT_DIR, "report.pdf")
    with PdfPages(pdf_path) as pdf:
        # Cover page
        plt.figure(figsize=(8.3, 11.7))
        plt.axis("off")
        
        cover_text = f"""
SENTICA — COMPREHENSIVE YOUTUBE ANALYSIS REPORT

VIDEO INFORMATION:
Title: {video_info.get('title', 'N/A')}
Channel: {video_info.get('channel', 'N/A')}
Video ID: {meta.get('video_id', 'N/A')}
View Count: {video_info.get('view_count', 'N/A')}

ANALYSIS SUMMARY:
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Comments Analyzed: {meta.get('total_comments', 0)}

SENTIMENT BREAKDOWN:
Positive: {meta.get('pos', 0)} ({(meta.get('pos', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)
Negative: {meta.get('neg', 0)} ({(meta.get('neg', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)
Neutral: {meta.get('neu', 0)} ({(meta.get('neu', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)

Average Polarity: {meta.get('avg_polarity', 0):.3f}
Generated Files: {len(all_files)} total outputs
        """
        
        plt.text(0.1, 0.9, cover_text, va="top", ha="left", fontsize=11, 
                transform=plt.gca().transAxes, color='white')
        pdf.savefig(facecolor='#1a1f3a')
        plt.close()

        # Add charts to PDF
        image_files = [f for f in all_files if f.lower().endswith('.png')]
        for img_file in image_files:
            img_path = os.path.join(OUTPUT_DIR, img_file)
            if os.path.exists(img_path):
                try:
                    img = plt.imread(img_path)
                    plt.figure(figsize=(8.3, 11.7))
                    plt.imshow(img)
                    plt.axis('off')
                    plt.title(img_file.replace('_', ' ').replace('.png', '').title(), 
                             fontsize=16, color='white', pad=20)
                    plt.tight_layout()
                    pdf.savefig(facecolor='#1a1f3a')
                    plt.close()
                except Exception as e:
                    print(f"Error adding {img_file} to PDF: {e}")
                    continue
    files.append("report.pdf")
    
    # Summary text
    summary_content = f"""
SENTICA - YOUTUBE SENTIMENT ANALYSIS SUMMARY

VIDEO DETAILS:
Title: {video_info.get('title', 'N/A')}
Channel: {video_info.get('channel', 'N/A')}
Video ID: {meta.get('video_id', 'N/A')}
View Count: {video_info.get('view_count', 'N/A')}
Likes: {video_info.get('like_count', 'N/A')}

ANALYSIS OVERVIEW:
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Comments Analyzed: {meta.get('total_comments', 0):,}

SENTIMENT DISTRIBUTION:
Positive Comments: {meta.get('pos', 0):,} ({(meta.get('pos', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)
Negative Comments: {meta.get('neg', 0):,} ({(meta.get('neg', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)
Neutral Comments: {meta.get('neu', 0):,} ({(meta.get('neu', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)

POLARITY ANALYSIS:
Average Polarity Score: {meta.get('avg_polarity', 0):.3f}
(Scale: -1.0 = Very Negative, 0.0 = Neutral, +1.0 = Very Positive)

KEY INSIGHTS:
• Overall sentiment trend: {'Positive' if meta.get('avg_polarity', 0) > 0.1 else 'Negative' if meta.get('avg_polarity', 0) < -0.1 else 'Neutral'}
• Engagement Level: {'High' if meta.get('total_comments', 0) > 1000 else 'Medium' if meta.get('total_comments', 0) > 100 else 'Low'} comment volume
• Community Response: {'Predominantly positive' if (meta.get('pos', 0)/max(1, meta.get('total_comments', 1))) > 0.5 else 'Mixed reactions' if (meta.get('neg', 0)/max(1, meta.get('total_comments', 1))) > 0.3 else 'Largely neutral'}

Generated by SENTICA - Advanced YouTube Sentiment Analysis Tool
    """
    
    with open(os.path.join(OUTPUT_DIR, "summary.txt"), 'w', encoding='utf-8') as f:
        f.write(summary_content)
    files.append("summary.txt")
    
    # HTML Dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SENTICA Dashboard - {video_info.get('title', 'YouTube Analysis')}</title>
        <style>
            body {{
                background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 30%, #2d1b69 60%, #1e1b4b 100%);
                color: white;
                font-family: 'Inter', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }}
            .dashboard {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 2rem;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
            }}
            .title {{
                font-size: 2.5rem;
                background: linear-gradient(45deg, #00d4ff, #7b2cbf);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }}
            .stat-card {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 1.5rem;
                border-radius: 15px;
                text-align: center;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .stat-value {{
                font-size: 2rem;
                font-weight: bold;
                color: #00d4ff;
            }}
            .stat-label {{
                font-size: 0.9rem;
                opacity: 0.8;
                margin-top: 0.5rem;
            }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1 class="title">SENTICA DASHBOARD</h1>
                <h2>{video_info.get('title', 'YouTube Video Analysis')}</h2>
                <p>Channel: {video_info.get('channel', 'N/A')} | Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{meta.get('total_comments', 0)}</div>
                    <div class="stat-label">Total Comments</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{meta.get('pos', 0)}</div>
                    <div class="stat-label">Positive ({(meta.get('pos', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{meta.get('neg', 0)}</div>
                    <div class="stat-label">Negative ({(meta.get('neg', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{meta.get('neu', 0)}</div>
                    <div class="stat-label">Neutral ({(meta.get('neu', 0)/max(1, meta.get('total_comments', 1))*100):.1f}%)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{meta.get('avg_polarity', 0):.3f}</div>
                    <div class="stat-label">Average Polarity</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(os.path.join(OUTPUT_DIR, "dashboard.html"), 'w', encoding='utf-8') as f:
        f.write(html_content)
    files.append("dashboard.html")
    
    return files

# ---------------------------- ROUTES ----------------------------

@app.route("/")
def root():
    return jsonify({"message": "SENTICA Backend Running"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "message": "SENTICA Backend is running"})

@app.route("/outputs/list")
def list_outputs():
    try:
        return jsonify({"files": sorted(os.listdir(OUTPUT_DIR))})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/outputs/file/<path:fn>")
def get_output_file(fn):
    try:
        return send_from_directory(OUTPUT_DIR, fn, as_attachment=False)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route("/outputs/zip")
def download_zip():
    try:
        return send_from_directory(OUTPUT_DIR, build_zip(), as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/outputs/report")
def download_report():
    path = os.path.join(OUTPUT_DIR, "report.pdf")
    if not os.path.exists(path):
        return jsonify({"error": "Report not found"}), 404
    return send_from_directory(OUTPUT_DIR, "report.pdf", as_attachment=True)

@app.route("/analyze_video", methods=["POST"])
def analyze_video():
    try:
        data = request.get_json(silent=True) or {}
        url = data.get("video_url", "").strip()
        
        if not url:
            return jsonify({"error": "Missing video_url"}), 400
            
        vid = extract_video_id(url)
        if not vid:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        # Clear previous outputs
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Fetch video info and ALL comments
        print("Fetching video information...")
        info = fetch_video_info(vid)
        
        print("Starting to fetch ALL comments (no limit)...")
        comments = fetch_comments(vid)
        
        if not comments:
            df = pd.DataFrame()
            meta = {
                "video_id": vid,
                "title": info.get("title", ""),
                "total_comments": 0,
                "pos": 0, "neg": 0, "neu": 0,
                "avg_polarity": 0.0
            }
            outs = save_core_data(df, info)
            outs.extend(create_reports(df, info, meta, outs))
            outs.append(build_zip())
            return jsonify({"message": "No comments found.", "outputs": outs, "summary": meta}), 200
        
        print(f"Processing {len(comments)} comments...")
        
        # Build comprehensive DataFrame
        df = pd.DataFrame(comments)
        df["cleaned"] = df["text"].astype(str).apply(clean_text)
        df["length"] = df["text"].astype(str).apply(len)
        df["emojis"] = df["text"].astype(str).apply(extract_emojis)
        
        # Sentiment analysis
        print("Performing sentiment analysis...")
        sent_results = df["cleaned"].apply(analyze_sentiment)
        df["polarity"] = sent_results.apply(lambda x: x[0])
        df["subjectivity"] = sent_results.apply(lambda x: x[1])
        df["sentiment"] = sent_results.apply(lambda x: x[2])
        
        # Process other fields
        df["likes"] = pd.to_numeric(df["likes"], errors="coerce").fillna(0).astype(int)
        df["published_at"] = df["published_at"].apply(safe_dt_naive)
        
        # Extract temporal features
        print("Extracting temporal features...")
        temporal_features = df["published_at"].apply(
            lambda x: parse_datetime_features(x) if x else {"hour": 0, "day_of_week": 0, "month": 1}
        )
        df["hour"] = [f["hour"] for f in temporal_features]
        df["day_of_week"] = [f["day_of_week"] for f in temporal_features]
        df["month"] = [f["month"] for f in temporal_features]
        
        # Generate ALL outputs with error handling
        print("Generating comprehensive outputs...")
        all_outputs = []
        
        try:
            print("Saving core data exports...")
            all_outputs.extend(save_core_data(df, info))
        except Exception as e:
            print(f"Error saving core data: {e}")
        
        try:
            print("Creating sentiment visualizations...")
            all_outputs.extend(save_sentiment_visualizations(df))
        except Exception as e:
            print(f"Error creating sentiment visualizations: {e}")
        
        try:
            print("Creating advanced relationship visualizations...")
            all_outputs.extend(save_advanced_visualizations(df))
        except Exception as e:
            print(f"Error creating advanced visualizations: {e}")
        
        try:
            print("Generating word clouds...")
            all_outputs.extend(save_wordclouds(df))
        except Exception as e:
            print(f"Error generating word clouds: {e}")
        
        try:
            print("Analyzing emoji usage...")
            all_outputs.extend(save_emoji_analysis(df))
        except Exception as e:
            print(f"Error analyzing emojis: {e}")
        
        try:
            print("Processing author and engagement data...")
            all_outputs.extend(save_author_analysis(df))
        except Exception as e:
            print(f"Error processing author analysis: {e}")
        
        try:
            print("Building temporal analysis...")
            all_outputs.extend(save_temporal_analysis(df))
        except Exception as e:
            print(f"Error building temporal analysis: {e}")
        
        try:
            print("Building timeline visualizations...")
            all_outputs.extend(save_timeline_analysis(df))
        except Exception as e:
            print(f"Error building timeline analysis: {e}")
        
        try:
            print("Computing linguistic analysis...")
            all_outputs.extend(save_linguistic_analysis(df))
        except Exception as e:
            print(f"Error computing linguistic analysis: {e}")
        
        try:
            print("Generating model evaluation with confusion matrices...")
            all_outputs.extend(save_model_evaluation(df))
        except Exception as e:
            print(f"Error generating model evaluation: {e}")
        
        try:
            print("Creating advanced model evaluation...")
            all_outputs.extend(save_advanced_model_evaluation(df))
        except Exception as e:
            print(f"Error creating advanced evaluation: {e}")
        
        # Summary statistics
        counts = df["sentiment"].value_counts()
        meta = {
            "video_id": vid,
            "title": info.get("title", ""),
            "channel": info.get("channel", ""),
            "total_comments": len(df),
            "pos": int(counts.get("Positive", 0)),
            "neg": int(counts.get("Negative", 0)),
            "neu": int(counts.get("Neutral", 0)),
            "avg_polarity": float(df["polarity"].mean()),
            "avg_subjectivity": float(df["subjectivity"].mean()) if 'subjectivity' in df.columns else 0,
            "avg_comment_length": float(df["length"].mean()),
            "total_likes": int(df["likes"].sum())
        }
        
        # Generate reports
        print("Creating comprehensive reports...")
        all_outputs.extend(create_reports(df, info, meta, all_outputs))
        
        # Generate executive summary
        try:
            print("Generating executive summary...")
            all_outputs.extend(save_executive_summary(df, info, meta))
        except Exception as e:
            print(f"Error generating executive summary: {e}")
        
        # Create final ZIP
        all_outputs.append(build_zip())
        
        print(f"Analysis complete! Generated {len(all_outputs)} files")
        
        return jsonify({
            "message": f"Comprehensive analysis complete - analyzed {len(df)} comments",
            "outputs": list(set(all_outputs)),
            "summary": meta
        })
        
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting SENTICA Backend...")
    print("Make sure to set YOUTUBE_API_KEY environment variable")
    # FIXED: Disable auto-reloader to prevent "Failed to fetch" errors
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
