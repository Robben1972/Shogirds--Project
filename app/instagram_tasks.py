import asyncio
from app.utils.db import get_session
from app.models.models import ScheduledPost, User
from instagrapi import Client
from datetime import datetime, timedelta
import os

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

async def upload_to_instagram():
    while True:
        print("Checking for scheduled posts...")
        session = get_session()

        now = datetime.now().replace(second=0, microsecond=0)
        start_time = now
        end_time = now + timedelta(minutes=1)

        scheduled_posts = session.query(ScheduledPost).filter(
            ScheduledPost.time >= start_time,
            ScheduledPost.time < end_time
        ).all()
        print(scheduled_posts)

        for post in scheduled_posts:
            user = session.query(User).filter_by(user_id=post.user_id).first()
            if not user:
                print(f"User with ID {post.user_id} not found.")
                continue

            cli = Client()
            session_file = os.path.join(SESSIONS_DIR, f"{user.instagram_username}_session.json")

            try:
                if os.path.exists(session_file):
                    cli.load_settings(session_file)
                    cli.login(user.instagram_username, user.instagram_password)
                else:
                    print(f"No session for {user.instagram_username}. Skipping...")
                    continue

                if post.content_type == "post":
                    cli.photo_upload(post.file_path, post.caption)
                elif post.content_type == "reels":
                    cli.video_upload(post.file_path, post.caption)
                elif post.content_type == "story":
                    if post.file_path.endswith('.mp4'):
                        cli.video_upload_to_story(post.file_path, post.caption)
                    else:
                        cli.photo_upload_to_story(post.file_path, post.caption)
                print(f"Uploaded {post.content_type} for {user.instagram_username}")
            except Exception as e:
                print(f"Failed to upload for {user.instagram_username}: {e}")
            finally:
                if os.path.exists(post.file_path):
                    os.remove(post.file_path)
                session.delete(post)

        session.commit()
        session.close()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(upload_to_instagram())
