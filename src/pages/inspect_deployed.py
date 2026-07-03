import urllib.request
import re

urls = {
    "index.html": "https://haykozaq.github.io/wise_website_test/src/pages/index.html",
    "contact.html": "https://haykozaq.github.io/wise_website_test/src/pages/contact.html",
    "about.html": "https://haykozaq.github.io/wise_website_test/src/pages/about.html"
}

for name, url in urls.items():
    print(f"\n--- Deployed content of {name} ---")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
        
        # Search for footer social container
        match = re.search(r'<div class="footer__social">.*?</div>', html, re.DOTALL)
        if match:
            print("FOUND footer__social:")
            print(match.group(0))
        else:
            print("NOT FOUND footer__social")
            
    except Exception as e:
        print(f"Error: {e}")
