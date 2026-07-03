import urllib.request
import json
import os
import re
from bs4 import BeautifulSoup
import urllib.parse

def fetch_all_posts():
    blog_html_path = "src/pages/blog.html"
    if not os.path.exists(blog_html_path):
        blog_html_path = "../../pages/blog.html"
        
    with open(blog_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    buttons = soup.find_all(class_="blog-read-more")
    urls = []
    for btn in buttons:
        u = btn.get("data-url")
        if u and u not in urls:
            urls.append(u)
            
    print(f"Found {len(urls)} unique blog URLs to fetch...")
    
    posts_db = {}
    
    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] Fetching: {url}")
        
        # Decode URL for displaying properly
        decoded_url = urllib.parse.unquote(url)
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            with urllib.request.urlopen(req, timeout=10) as res:
                html = res.read().decode("utf-8")
                
            post_soup = BeautifulSoup(html, "html.parser")
            
            # Extract Title
            title_el = post_soup.find("h1", class_="entry-title") or post_soup.find("h1")
            title = title_el.get_text().strip() if title_el else "Announcement"
            
            # Extract Date
            date_el = post_soup.find(class_="posted-on") or post_soup.find("time")
            date = date_el.get_text().strip() if date_el else ""
            
            # Extract Content
            content_el = post_soup.find(class_="entry-content") or post_soup.find("article") or post_soup.find("main")
            
            # Clean up content
            content_html = ""
            if content_el:
                # Remove scripts, styles, forms, headers, footers, sidebars, share buttons
                for bad_tag in content_el.find_all(["script", "style", "iframe", "form", "header", "footer", "nav"]):
                    bad_tag.decompose()
                for bad_class in [".sharedaddy", ".jp-relatedposts", ".post-author-bio", ".navigation"]:
                    for item in content_el.select(bad_class):
                        item.decompose()
                
                # Convert links inside to open in new tab
                for link in content_el.find_all("a"):
                    link["target"] = "_blank"
                    link["rel"] = "noopener"
                    
                content_html = str(content_el)
                
            # If content is empty, use a placeholder
            clean_text = BeautifulSoup(content_html, "html.parser").get_text().strip()
            if not clean_text:
                content_html = "<p>Լրացուցիչ տեղեկատվություն հասանելի չէ այս հայտարարության համար:</p>"
                
            # Extract featured image if exists
            img_el = post_soup.find(class_="post-thumbnail")
            img_url = ""
            if img_el and img_el.find("img"):
                img_url = img_el.find("img").get("src", "")
                
            posts_db[url] = {
                "title": title,
                "date": date,
                "content": content_html,
                "image": img_url
            }
            print(f"  Successfully fetched: {len(content_html)} bytes")
            
        except Exception as e:
            print(f"  Error fetching article: {e}")
            # Save a fallback entry so it doesn't break the app
            posts_db[url] = {
                "title": "Հայտարարություն",
                "date": "",
                "content": f"<p>Չհաջողվեց բեռնել հոդվածի բովանդակությունը տվյալների բազայից:</p><p><a href='{url}' target='_blank' rel='noopener'>Բացել օրիգինալ հոդվածը wisef.am կայքում</a></p>",
                "image": ""
            }
            
    # Save database to json file
    output_path = "src/assets/data/blog-posts.json"
    # Ensure folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(posts_db, f, ensure_ascii=False, indent=2)
        
    print(f"Saved all articles to {output_path}!")

if __name__ == "__main__":
    fetch_all_posts()
