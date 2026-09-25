import json
import os
from pathlib import Path

import requests

API_URL = "https://api.linkedin.com/rest/posts"
CONTENT_FILE = Path("content.json")


def load_content():
    with CONTENT_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def publish_post(text, author_urn, access_token):
    version = os.getenv("LINKEDIN_VERSION", "202603")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "Linkedin-Version": version,
    }

    payload = {
        "author": author_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"LinkedIn API error {response.status_code}: {response.text}"
        )

    return response.headers.get("x-restli-id")


def main():
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.environ.get("LINKEDIN_AUTHOR_URN")

    if not token or not author_urn:
        raise RuntimeError(
            "Missing LinkedIn secrets."
        )

    data = load_content()

    for post in data.get("posts", []):
        if post.get("published", False):
            continue

        text = post.get("text", "").strip()

        if not text:
            continue

        post_id = publish_post(text, author_urn, token)

        post["published"] = True
        post["linkedin_id"] = post_id

        print(f"Published LinkedIn post: {post_id}")
        break

    with CONTENT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
