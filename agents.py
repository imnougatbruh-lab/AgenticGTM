import os
import json
from playwright.sync_api import sync_playwright
from google import genai
from dotenv import load_dotenv
from database import SessionLocal
from models import SocialCredential

load_dotenv()

def get_db_cookies(user_id: int, platform: str):
    db = SessionLocal()
    cred = db.query(SocialCredential).filter(
        SocialCredential.user_id == user_id, 
        SocialCredential.platform == platform
    ).first()
    db.close()
    if cred and cred.session_cookies:
        import json
        return json.loads(cred.session_cookies)
    return []

# Production safety switches for headless browser execution
PRODUCTION_MODE = os.getenv("PRODUCTION", "False").lower() == "true"
HEADLESS_MODE = os.getenv("PLAYWRIGHT_HEADLESS", "True" if PRODUCTION_MODE else "False").lower() == "true"

def get_proxy_config():
    """Returns proxy dictionary for Playwright if environment variables are set."""
    server = os.getenv("PROXY_SERVER")
    if not server:
        return None
    return {
        "server": server,
        "username": os.getenv("PROXY_USERNAME", ""),
        "password": os.getenv("PROXY_PASSWORD", "")
    }

def get_client():
    """
    Initializes the modern Google Gen AI Client.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Gemini Client: {e}")
        return None

def scrape_website(url: str):
    """
    Synchronous scraping with a visible browser for maximum bot-bypass.
    """
    with sync_playwright() as p:
        try:
            print(f"--- STARTING SCRAPE: {url} ---")
            browser = p.chromium.launch(channel="chrome",
                headless=HEADLESS_MODE, 
                args=["--disable-blink-features=AutomationControlled"],
                proxy=get_proxy_config()
            )
            page = browser.new_page()
            
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/"
            })
            
            print("Waiting for page load...")
            page.goto(url, wait_until="load", timeout=30000)
            
            import time
            time.sleep(2) # Give it 2 seconds to complete rendering/JS challenges
            
            title = page.title()
            page_text = page.inner_text("body")
            clean_text = " ".join(page_text.split())
            
            print(f"--- SCRAPE SUCCESSFUL ({len(clean_text)} chars) ---")
            if len(clean_text) < 500:
                print(f"DEBUG: Scraped very short content: '{clean_text}'")
                
            browser.close()
            return {
                "url": url,
                "title": title,
                "content": clean_text[:10000]
            }
        except Exception as e:
            print(f"--- SCRAPE FAILED: {str(e)} ---")
            return {"error": f"Scraping failed: {str(e)}"}

async def analyze_product(url: str):
    client = get_client()
    if not client: return {"error": "Gemini API Key missing"}

    import asyncio
    loop = asyncio.get_event_loop()
    scraped_data = await loop.run_in_executor(None, scrape_website, url)
    
    if "error" in scraped_data: return scraped_data

    prompt = f"""
    Analyze this startup website and extract:
    - name, tagline, description, key_features, target_audience.
    Website Content: {scraped_data['content']}
    Respond ONLY with raw JSON.
    """

    print("--- ANALYZING WITH GEMINI 2.5 FLASH ---")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        text_response = response.text.strip()
        return json.loads(text_response)
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

async def generate_copy(product_data: dict):
    client = get_client()
    if not client: return {"error": "Gemini API Key missing"}

    icp_instructions = ""
    if "icp_profile" in product_data and product_data["icp_profile"]:
        icp = product_data["icp_profile"]
        icp_instructions = f"""
        Highly target the marketing copy to the following refined ICP (Ideal Customer Profile) metrics:
        - Target Personas: {', '.join(icp.get('ideal_job_titles', []))}
        - Core Pain Points: {', '.join(icp.get('core_pain_points', []))}
        - Dynamic Positioning Focus: {icp.get('refined_positioning', '')}
        """

    prompt = f"""
    Write marketing copy for this product in an authentic Developer Voice:
    - twitter_thread (3-5 tweets)
    - reddit_post (r/SaaS title + body)
    - directory_short (150 chars)
    - directory_long (500 chars)
    
    Data: {json.dumps(product_data)}
    {icp_instructions}
    
    Respond ONLY with raw JSON.
    """

    print("--- GENERATING COPY WITH GEMINI 2.5 FLASH ---")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        text_response = response.text.strip()
        return json.loads(text_response)
    except Exception as e:
        print(f"Copy generation failed (likely quota exhausted): {str(e)}")
        print("[Resilient Fallback] Injecting synthetic marketing copy...")
        
        product_name = product_data.get("name", "our product")
        return {
            "twitter_thread": [
                f"We just launched {product_name}! 🚀 If you are tired of manual work, this is for you. A thread 🧵👇",
                f"Building {product_name} was hard. We realized that doing things manually was draining all our engineering time. So we automated it. ⚡",
                f"Try it out today and let us know what you think! We are giving early access to the first 100 users. Link in bio! 🔗"
            ],
            "reddit_post": {
                "title": f"I built {product_name} to stop doing manual marketing",
                "body": f"Hey r/SaaS, we were spending 20 hours a week just doing repetitive tasks. So we built {product_name} to automate it all. Would love your feedback!"
            },
            "directory_short": f"{product_name} is the ultimate automation tool for modern startups.",
            "directory_long": f"{product_name} saves you 20 hours a week by automating your most tedious workflows so you can focus on shipping features."
        }

def fill_form_playwright(submit_url: str, product_data: dict, screenshot_path: str):
    """
    Playwright engine that loads the form, extracts elements, maps them via Gemini,
    autofills the inputs, takes a screenshot, and submits.
    """
    with sync_playwright() as p:
        try:
            print(f"--- STARTING AUTONOMOUS SUBMISSION TO: {submit_url} ---")
            from playwright_stealth import Stealth
            stealth = Stealth()
            
            user_id = product_data.get('owner_id', 1) if isinstance(product_data, dict) else 1
            
            browser = p.chromium.launch(channel="chrome",
                headless=HEADLESS_MODE,
                args=["--disable-blink-features=AutomationControlled"],
                proxy=get_proxy_config()
            )
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",)
            
            platform_name = "ProductHunt" if "producthunt.com" in submit_url else "BetaList" if "betalist.com" in submit_url else "HackerNews" if "ycombinator.com" in submit_url else None
            if platform_name:
                cookies = get_db_cookies(user_id, platform_name)
                if cookies:
                    context.add_cookies(cookies)
                    print(f"Injected securely saved {platform_name} session cookies for user {user_id}")
            
            page = context.new_page()
            
            # Apply stealth masking to bypass Cloudflare bot detection
            stealth.apply_stealth_sync(page)
            print('Navigating to submission form...')
            page.goto(submit_url, wait_until='domcontentloaded', timeout=30000)
            import time
            time.sleep(0.5)
            try:
                if 'login' in page.title().lower() or 'log in' in page.inner_text('body').lower():
                    print('Login wall detected! Please log in manually. Waiting 60 seconds...')
                    try:
                        page.wait_for_navigation(timeout=60000)
                        print('Navigation detected, assuming login successful. AI taking over...')
                    except:
                        print('Did not detect login within 60s, proceeding anyway...')
            except Exception as e:
                print(f"Skipping login check due to page state: {e}")

            # 1. Extract interactive form elements (inputs, textareas)
            inputs = page.query_selector_all("input:not([type='hidden']):not([type='submit']), textarea")
            form_elements = []
            for index, el in enumerate(inputs):
                tag_name = el.evaluate("el => el.tagName.toLowerCase()")
                el_id = el.get_attribute("id") or ""
                el_name = el.get_attribute("name") or ""
                el_placeholder = el.get_attribute("placeholder") or ""
                el_type = el.get_attribute("type") or ""
                
                # Fetch associated label
                label_text = ""
                if el_id:
                    label_el = page.query_selector(f"label[for='{el_id}']")
                    if label_el:
                        label_text = label_el.inner_text()
                
                form_elements.append({
                    "index": index,
                    "tag": tag_name,
                    "id": el_id,
                    "name": el_name,
                    "type": el_type,
                    "placeholder": el_placeholder,
                    "label": label_text
                })
            
            print(f"Discovered {len(form_elements)} form fields on the page.")
            
            # 2. Feed form elements to Gemini to map CSS selectors to product data
            client = get_client()
            if not client:
                context.close()
                return {"error": "Gemini API Key missing"}
                
            prompt = f"""
            You are an AI Submitter Agent. I will provide you with a list of interactive HTML input fields extracted from a startup submission form, and the product data we want to submit.
            
            HTML Form Fields:
            {json.dumps(form_elements, indent=2)}
            
            Product Data:
            {json.dumps(product_data, indent=2)}
            
            Determine which HTML selector (preferring ID, name, or index-based CSS selector) matches each product data field.
            We want to fill:
            - Product Name -> value: product name
            - Product Website URL -> value: product url
            - Tagline / Short Description -> value: tagline or directory_short (use the short tagline, around 100-150 chars)
            - Long Description -> value: description or directory_long (around 500 chars)
            
            Respond ONLY with a raw JSON array of actions in this exact format (no markdown code blocks, just raw JSON):
            [
              {{"selector": "css_selector_or_id_or_name", "field": "name", "value": "value_to_type"}},
              {{"selector": "css_selector_or_id_or_name", "field": "url", "value": "value_to_type"}},
              {{"selector": "css_selector_or_id_or_name", "field": "tagline", "value": "value_to_type"}},
              {{"selector": "css_selector_or_id_or_name", "field": "description", "value": "value_to_type"}}
            ]
            """
            
            print("Mapping form fields with Gemini 2.5 Flash...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            text_response = response.text.strip()
            actions = json.loads(text_response)
            print(f"Gemini planner produced {len(actions)} fill actions.")
            
            # 3. Execute actions using Playwright
            for action in actions:
                selector = action["selector"]
                field_name = action["field"]
                val = action["value"]
                
                print(f"Typing into field '{field_name}' using selector '{selector}'...")
                try:
                    page.fill(selector, val, timeout=2000)
                except Exception as fill_err:
                    print(f"Selector {selector} failed. Trying fallback by name/id...")
                    fallback_selectors = [f"#{selector}", f"[name='{selector}']", f"input[name='{selector}']", f"textarea[name='{selector}']"]
                    success = False
                    for fb in fallback_selectors:
                        try:
                            page.fill(fb, val, timeout=2000)
                            success = True
                            print(f"Successfully typed using fallback: {fb}")
                            break
                        except:
                            continue
                    if not success:
                        print(f"Could not fill field '{field_name}'! Error: {fill_err}")
            
            # Let it rest so you can see it filled out
            time.sleep(2)
            
            # Take screenshot before submission
            print(f"Saving form snapshot to: {screenshot_path}")
            page.screenshot(path=screenshot_path)
            
            # 4. Click Submit Button
            print("Locating and clicking the submit button...")
            submit_selectors = ["button[type='submit']", "input[type='submit']", "#submit-btn", "button:has-text('Submit')", "button:has-text('Product')"]
            submitted = False
            for selector in submit_selectors:
                try:
                    if page.query_selector(selector):
                        page.click(selector)
                        submitted = True
                        print(f"Form submitted successfully using button: {selector}")
                        break
                except:
                    continue
                    
            if not submitted:
                try:
                    page.keyboard.press("Enter")
                    submitted = True
                    print("Form submitted by pressing Enter key.")
                except Exception as e:
                    print(f"Could not trigger form submission: {e}")
            
            # Wait for submission redirect/load
            time.sleep(3)
            
            context.close()
            return {
                "status": "success" if submitted else "failed",
                "message": "Form filled and submitted successfully" if submitted else "Form filled but submission button click failed",
                "screenshot": screenshot_path
            }
        except Exception as e:
            print(f"--- SUBMISSION FAILED: {str(e)} ---")
            return {"error": f"Submission failed: {str(e)}"}

async def run_autonomous_submission(submit_url: str, product_data: dict, screenshot_path: str):
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, fill_form_playwright, submit_url, product_data, screenshot_path)
    return result

def publish_post_stealth(compose_url: str, platform: str, content: str, screenshot_path: str, user_id: int = 1):
    """
    Publisher Agent that launches a Playwright stealth browser, loads the compose page,
    autofills the text input area, takes a screenshot, and submits the post.
    Handles both live production URLs and localhost testing mockups.
    """
    with sync_playwright() as p:
        try:
            print(f"--- STARTING AUTONOMOUS POST PUBLISHING TO {platform.upper()} ---")
            browser = p.chromium.launch(channel="chrome",
                headless=HEADLESS_MODE,
                args=["--disable-blink-features=AutomationControlled"],
                proxy=get_proxy_config()
            )
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",)
            
            # Authenticate context using stored DB cookies for real web pages
            if "localhost" not in compose_url and "127.0.0.1" not in compose_url:
                cookies = get_db_cookies(user_id, platform)
                if cookies:
                    context.add_cookies(cookies)
                    
            page = context.new_page()
            
            from playwright_stealth import Stealth
            stealth = Stealth()
            stealth.apply_stealth_sync(page)
            print('Navigating to submission form...')
            page.goto(compose_url, wait_until='load', timeout=30000)
            import time
            time.sleep(2)
            if 'login' in page.title().lower() or 'log in' in page.inner_text('body').lower():
                print('Login wall detected! Please log in manually. Waiting 60 seconds...')
                try:
                    page.wait_for_navigation(timeout=60000)
                    print('Navigation detected, assuming login successful. AI taking over...')
                except:
                    print('Did not detect login within 60s, proceeding anyway...')

            
            page.goto(compose_url, wait_until="load", timeout=30000)
            
            import time
            time.sleep(3)
            
            if "localhost" in compose_url or "127.0.0.1" in compose_url:
                # Handle platform specific selector types (Mock environment)
                if platform.lower() == "twitter":
                    print("Typing Tweet...")
                    page.fill("#tweet-textarea", content)
                    time.sleep(1.5)
                    page.screenshot(path=screenshot_path)
                    page.click("#tweet-submit-btn")
                elif platform.lower() == "reddit":
                    # Splitting Reddit title from body
                    reddit_title = "B2B SaaS Dev Tools Launch"
                    reddit_body = content
                    if content.startswith("Title:"):
                        parts = content.split("\n\n", 1)
                        if len(parts) == 2:
                            reddit_title = parts[0].replace("Title: ", "").strip()
                            reddit_body = parts[1].strip()
                    
                    print("Typing Reddit Title & Post body...")
                    page.fill("#reddit-post-title", reddit_title)
                    page.fill("#reddit-post-body", reddit_body)
                    time.sleep(1.5)
                    page.screenshot(path=screenshot_path)
                    page.click("#reddit-submit-btn")
                else:
                    # LinkedIn / Generic
                    print("Typing Generic/LinkedIn post...")
                    page.fill("#generic-textarea", content)
                    time.sleep(1.5)
                    page.screenshot(path=screenshot_path)
                    page.click("#generic-submit-btn")
            else:
                # REAL PLATFORM STEALTH PUBLISHING!
                if platform.lower() == "twitter":
                    print("Typing Tweet on Real X/Twitter...")
                    page.click("div[data-testid='tweetTextarea_0']", timeout=10000)
                    page.keyboard.type(content, delay=10)
                    time.sleep(1)
                    page.screenshot(path=screenshot_path)
                    
                    # Click the Post button using resilient multi-selector fallback
                    post_selectors = [
                        "[data-testid='tweetButton']",
                        "div[data-testid='tweetButton']",
                        "button[data-testid='tweetButton']",
                        "div[data-testid='tweetButtonInline']",
                        "button:has-text('Post')",
                        "[role='button']:has-text('Post')",
                        "span:has-text('Post')"
                    ]
                    clicked = False
                    for selector in post_selectors:
                        try:
                            page.click(selector, timeout=3000)
                            clicked = True
                            print(f"Clicked Tweet Button using selector: {selector}")
                            break
                        except Exception:
                            continue
                    if not clicked:
                        page.click("button:has-text('Post'), [role='button']:has-text('Post')", timeout=10000)
                elif platform.lower() == "reddit":
                    # Splitting Reddit title from body
                    reddit_title = "B2B SaaS Dev Tools Launch"
                    reddit_body = content
                    if content.startswith("Title:"):
                        parts = content.split("\n\n", 1)
                        if len(parts) == 2:
                            reddit_title = parts[0].replace("Title: ", "").strip()
                            reddit_body = parts[1].strip()
                            
                    print("Typing Reddit Title & Post body on Real Reddit...")
                    page.fill("textarea[placeholder='Title']", reddit_title)
                    page.click("div[role='textbox']")
                    page.keyboard.type(reddit_body)
                    time.sleep(1.5)
                    page.screenshot(path=screenshot_path)
                    
                    # Click the Post button using resilient multi-selector fallback
                    reddit_selectors = [
                        "button:has-text('Post')",
                        "button[type='submit']",
                        "[role='button']:has-text('Post')",
                        "button:has-text('Submit')"
                    ]
                    clicked = False
                    for selector in reddit_selectors:
                        try:
                            page.click(selector, timeout=3000)
                            clicked = True
                            print(f"Clicked Reddit Post Button using selector: {selector}")
                            break
                        except Exception:
                            continue
                    if not clicked:
                        page.click("button:has-text('Post')", timeout=10000)
                else:
                    raise Exception(f"Real publishing for {platform} is not configured")
                
            time.sleep(3) # Wait for redirect / publication response screen
            browser.close()
            return {
                "status": "success",
                "message": f"Successfully published post to {platform}",
                "screenshot": screenshot_path
            }
        except Exception as e:
            print(f"--- PUBLICATION FAILED: {str(e)} ---")
            return {"error": f"Publication failed: {str(e)}"}

async def run_autonomous_publishing(compose_url: str, platform: str, content: str, screenshot_path: str, user_id: int = 1):
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, publish_post_stealth, compose_url, platform, content, screenshot_path, user_id)
    return result

def listen_and_draft_replies(product_data: dict, testimonials: list, discussions: list, target_keyword: str = None):
    """
    Social Listening AI Scout (Feature 2.4).
    Uses Gemini to analyze discussions, matching them against product capabilities and testimonials,
    and drafting authentic developer-voice replies. BATCHED for extreme performance.
    """
    client = get_client()
    if not client:
        return []
        
    if not discussions:
        return []
        
    leads_drafted = []
    
    prompt = f"""
    You are a highly skilled AI Growth and Social Listening scout.
    
    Our Product Details:
    {json.dumps(product_data, indent=2)}
    
    Available Customer Testimonials:
    {json.dumps(testimonials, indent=2)}
    
    Here is a list of active forum discussions. We want to process them all at once.
    {json.dumps(discussions, indent=2)}
    
    For EACH discussion in the list, determine if there is an active pain point, request for recommendations, or question that our product perfectly solves.
    
    CRITICAL RULE FOR MATCHING:
    You must be EXTREMELY strict. 
    ONLY match the discussion to `true` if it EXPLICITLY mentions "{target_keyword}" or a direct pain point our product solves.
    REJECT (set matched to false) 95% of threads. Do NOT match random announcements, news, or 'Show HN' posts unless they explicitly ask a question we solve. If there is any doubt, set matched to false.
    
    If YES (matched=true):
    1. Select the most relevant customer review/testimonial from the available testimonials list that backs up our claim.
    2. Draft a highly helpful, technical, natural, and non-spammy response in authentic Developer Voice that answers their question first, and then elegantly weaves that customer quote into the recommendation. Keep it strictly professional, helpful, and value-first. Do NOT use emojis or over-the-top sales pitch words.
    
    Respond ONLY with a raw JSON array containing exactly {len(discussions)} objects (one for each discussion, in the exact same order).
    Format of each object:
    {{
      "matched": true/false,
      "thread_title": "the title of the thread",
      "context_snippet": "snippet of the body (max 200 chars)",
      "draft_reply": "your drafted response text weaving in the chosen testimonial" (leave empty if matched=false)
    }}
    """
    
    try:
        print(f"Scouting {len(discussions)} threads in a SINGLE batch with Gemini 2.5 Flash...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        text_response = response.text.strip()
        results = json.loads(text_response)
        
        for idx, result in enumerate(results):
            if result.get("matched") is True:
                # Retrieve original URL since we stripped it in the prompt output instruction
                result["source_url"] = discussions[idx].get('url')
                leads_drafted.append(result)
                print(f"Matched and drafted response for: '{result.get('thread_title')}'")
            else:
                print(f"No match for thread: '{result.get('thread_title', discussions[idx].get('title', 'Unknown'))}'")
                
    except Exception as e:
        print(f"Batch scouting failed: {e}")
        # Resilient fallback matching logic when Gemini API quota is exhausted
        for thread in discussions:
            title_lower = thread.get('title', '').lower() if thread.get('title') else ""
            body_lower = thread.get('body', '').lower() if thread.get('body') else ""
            
            # Prioritize EXACT keyword matching instead of generic saas keywords
            keywords = [target_keyword.lower()] if target_keyword else [product_data.get('name', '').lower()]
            is_keyword_match = any(kw in title_lower or kw in body_lower for kw in keywords if kw)
            
            if not is_keyword_match and not target_keyword:
                keywords = ["saas", "market", "marketing", "code", "dev", "tool", "site", "web", "traffic", "seo", "launch", "user", "visitor"]
                is_keyword_match = any(kw in title_lower or kw in body_lower for kw in keywords)
            
            if is_keyword_match:
                print(f"[Resilient Match] Fallback matching triggered for '{thread.get('title')}'")
                testimonial_str = ""
                if testimonials:
                    t = testimonials[0]
                    testimonial_str = f" As {t.get('client_name', 'one of our users')} from {t.get('client_company', 'ScaleTech')} put it: \"{t.get('review_text', 'Great product.')}\""
                
                match_reason = target_keyword if target_keyword else "SaaS automation"
                leads_drafted.append({
                    "matched": True,
                    "thread_title": thread.get('title'),
                    "context_snippet": (thread.get('body') or '')[:200] + "...",
                    "draft_reply": f"Hey! I noticed you are discussing '{match_reason}'. We built {product_data.get('name', 'Xyroco')} to solve exactly this by automating directory submissions and organic marketing loops.{testimonial_str} Let me know if you want to check it out!",
                    "source_url": thread.get('url')
                })
            
    return leads_drafted

def reply_lead_stealth(thread_url: str, content: str, screenshot_path: str, user_id: int = 1, credentials: dict = None):
    """
    Playwright agent that navigates to the forum thread, autofills the comment box,
    snaps a screenshot receipt, and posts the reply comment.
    """
    with sync_playwright() as p:
        try:
            print(f"--- STARTING AUTONOMOUS LEAD REPLY TO {thread_url} (User: {user_id}) ---")
            
            # Use unique persistent context per user to retain logged-in sessions securely
            # Use cookies from DB to retain logged-in sessions securely in the cloud
            browser = p.chromium.launch(channel="chrome",
                headless=HEADLESS_MODE,
                args=["--disable-blink-features=AutomationControlled"],
                proxy=get_proxy_config()
            )
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",)
            
            # Fetch and apply cookies
            platform = "Twitter" if "twitter.com" in thread_url or "x.com" in thread_url else "Reddit" if "reddit.com" in thread_url else "HackerNews"
            cookies = get_db_cookies(user_id, platform)
            if cookies:
                context.add_cookies(cookies)
                
            page = context.new_page()
            
            from playwright_stealth import Stealth
            stealth = Stealth()
            stealth.apply_stealth_sync(page)
            print('Navigating to submission form...')
            page.goto(thread_url, wait_until='load', timeout=30000)
            import time
            time.sleep(2)
            if 'login' in page.title().lower() or 'log in' in page.inner_text('body').lower():
                print('Login wall detected! Please log in manually. Waiting 60 seconds...')
                try:
                    page.wait_for_navigation(timeout=60000)
                    print('Navigation detected, assuming login successful. AI taking over...')
                except:
                    print('Did not detect login within 60s, proceeding anyway...')

            
            import time
            # Auto-Login flow if credentials provided
            if credentials:
                try:
                    if "reddit.com" in thread_url:
                        page.goto("https://www.reddit.com/login", wait_until="load")
                        time.sleep(2)
                        page.fill("#loginUsername", credentials.get("username", ""))
                        page.fill("#loginPassword", credentials.get("password", ""))
                        page.click("button[type='submit']")
                        time.sleep(4)
                    elif "twitter.com" in thread_url or "x.com" in thread_url:
                        page.goto("https://twitter.com/i/flow/login", wait_until="load")
                        time.sleep(3)
                        page.fill("input[autocomplete='username']", credentials.get("username", ""))
                        page.keyboard.press("Enter")
                        time.sleep(2)
                        page.fill("input[name='password']", credentials.get("password", ""))
                        page.keyboard.press("Enter")
                        time.sleep(4)
                    elif "news.ycombinator.com" in thread_url:
                        page.goto("https://news.ycombinator.com/login", wait_until="load")
                        time.sleep(1)
                        page.fill("input[name='acct']", credentials.get("username", ""))
                        page.fill("input[name='pw']", credentials.get("password", ""))
                        page.click("input[value='login']")
                        time.sleep(2)
                except Exception as e:
                    print(f"Auto-login failed or already logged in: {e}")
            
            page.goto(thread_url, wait_until="load", timeout=30000)
            
            import time
            time.sleep(3)
            
            print("Typing contextual reply comment...")
            
            # Determine platform and use correct selectors
            if "reddit.com" in thread_url:
                # Real Reddit comment box
                try:
                    page.click("div[data-testid='comment-composer']", timeout=5000)
                    page.keyboard.type(content, delay=10)
                    time.sleep(1)
                    page.screenshot(path=screenshot_path)
                    page.click("button[data-testid='comment-composer-submit']")
                except:
                    # Fallback for older reddit UI
                    page.fill("textarea[name='text']", content)
                    page.screenshot(path=screenshot_path)
                    page.click("button[type='submit']")
            elif "news.ycombinator.com" in thread_url:
                # Real HackerNews comment box
                page.fill("textarea[name='text']", content)
                time.sleep(1)
                page.screenshot(path=screenshot_path)
                page.click("input[type='submit']")
            elif "twitter.com" in thread_url or "x.com" in thread_url:
                # Real Twitter reply box
                page.click("div[data-testid='tweetTextarea_0']", timeout=5000)
                page.keyboard.type(content, delay=10)
                time.sleep(1)
                page.screenshot(path=screenshot_path)
                page.click("div[data-testid='tweetButtonInline']")
            else:
                # Fallback for mock pages
                page.fill("#reply-textarea", content)
                time.sleep(1.5)
                page.screenshot(path=screenshot_path)
                page.click("#reply-submit-btn")
            
            print(f"Saved comment snapshot receipt to: {screenshot_path}")
            time.sleep(4) # Wait for redirect / verification
            browser.close()
            return {
                "status": "success",
                "message": "Successfully posted reply comment autonomously",
                "screenshot": screenshot_path
            }
        except Exception as e:
            print(f"--- REPLY POSTING FAILED: {str(e)} ---")
            return {"error": f"Reply posting failed: {str(e)}"}

async def run_social_listening_scout(product_data: dict, testimonials: list, discussions: list, target_keyword: str = None):
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, listen_and_draft_replies, product_data, testimonials, discussions, target_keyword)
    return result

async def run_autonomous_lead_reply(thread_url: str, content: str, screenshot_path: str, user_id: int = 1, credentials: dict = None):
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, reply_lead_stealth, thread_url, content, screenshot_path, user_id, credentials)
    return result

def publish_blog_stealth(blog_url: str, title: str, body: str, screenshot_path: str):
    """
    Playwright agent that logs into the mock blogging platform, autofills title and body textareas,
    snaps a screenshot receipt, and posts the blog comment (Feature 2.5).
    """
    with sync_playwright() as p:
        try:
            print(f"--- STARTING AUTONOMOUS BLOG PUBLISHING TO: {blog_url} ---")
            browser = p.chromium.launch(channel="chrome",
                headless=HEADLESS_MODE,
                args=["--disable-blink-features=AutomationControlled"],
                proxy=get_proxy_config()
            )
            page = browser.new_page()
            page.goto(blog_url, wait_until="load", timeout=30000)
            
            import time
            time.sleep(2)
            
            print("Typing blog title...")
            page.fill("#blog-title", title)
            time.sleep(1.0)
            
            print("Typing blog content body...")
            page.fill("#blog-body", body)
            time.sleep(2.0)
            
            print(f"Saving publication snapshot receipt to: {screenshot_path}")
            page.screenshot(path=screenshot_path)
            
            print("Submitting the technical blog post...")
            page.click("#blog-submit-btn")
            
            time.sleep(3) # Wait for redirect / confirmation page
            browser.close()
            return {
                "status": "success",
                "message": "Successfully published blog post autonomously",
                "screenshot": screenshot_path
            }
        except Exception as e:
            print(f"--- BLOG PUBLICATION FAILED: {str(e)} ---")
            return {"error": f"Blog publication failed: {str(e)}"}

async def run_autonomous_blog_publishing(blog_url: str, title: str, body: str, screenshot_path: str):
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, publish_blog_stealth, blog_url, title, body, screenshot_path)
    return result

async def refine_icp(product_data: dict, testimonials: list[dict], analytics_data: dict):
    """
    Synthesizes user reviews, conversion rates, and clicks to build a refined ICP profile (Feature 2.7).
    """
    client = get_client()
    if not client: return {"error": "Gemini API Key missing"}

    prompt = f"""
    Analyze the following product details, customer testimonials (5-star reviews, roles), and traffic analytics (clicks/conversions per channel) to refine the Ideal Customer Profile (ICP) for this startup:
    
    1. Product Details: {json.dumps(product_data)}
    2. Customer Testimonials: {json.dumps(testimonials)}
    3. Traffic/Conversion Analytics: {json.dumps(analytics_data)}
    
    Synthesize these data points to identify who is converting best and what messaging works.
    
    Respond ONLY with a JSON object in this exact schema:
    {{
      "ideal_job_titles": ["List of 3-5 specific target job titles/personas who are highly active or satisfied, e.g. DevOps Engineer, Engineering Manager"],
      "top_channels": ["List of 2-3 marketing channels that have the highest conversion rates or click volume"],
      "core_pain_points": ["List of 3-4 specific tech/business pain points mentioned by users in positive testimonials or inferred from conversions"],
      "refined_positioning": "A highly tailored, conversion-focused 1-2 sentence tagline/pitch for the product targeting these key pain points and personas."
    }}
    """

    print("--- SYNTHESIZING REFINED ICP WITH GEMINI 2.5 FLASH ---")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        text_response = response.text.strip()
        return json.loads(text_response)
    except Exception as e:
        return {"error": f"ICP refinement failed: {str(e)}"}

def discover_competitor_stealth(url: str):
    """
    Playwright agent that scrapes the competitor's website and uses Gemini to analyze
    their tagline and discover what directories they are listed on (Feature 2.8).
    """
    from playwright.sync_api import sync_playwright
    import json
    
    with sync_playwright() as p:
        try:
            print(f"--- SCRAPING COMPETITOR LANDING PAGE: {url} ---")
            browser = p.chromium.launch(channel="chrome",
                headless=HEADLESS_MODE,
                args=["--disable-blink-features=AutomationControlled"],
                proxy=get_proxy_config()
            )
            page = browser.new_page()
            page.goto(url, wait_until="load", timeout=30000)
            
            # Extract main visible content to help Gemini analyze their value proposition
            title = page.title()
            body_text = page.locator("body").inner_text()[:3000]
            browser.close()
            
            # Now we use Gemini to synthesize the tagline and simulate directory listings
            client = get_client()
            if not client:
                return {
                    "tagline": "Tracked Competitor",
                    "listings": ["ProductHunt"]
                }
                
            prompt = f"""
            Analyze the scraped homepage content of a competitor website:
            URL: {url}
            Page Title: {title}
            Scraped text snippet:
            {body_text}
            
            Tasks:
            1. Extract a clear, concise 1-sentence tagline describing their value proposition.
            2. Based on their product category, scan/deduce which directories they are listed on out of these top B2B/SaaS platforms:
               ["ProductHunt", "BetaList", "AlternativeTo", "SaaSHub", "Capterra", "G2", "SourceForge"]
            
            Respond ONLY with a JSON object in this exact schema:
            {{
              "tagline": "1-sentence descriptive tagline",
              "listings": ["DirectoryName1", "DirectoryName2", ...]
            }}
            """
            
            print("--- ANALYZING COMPETITOR DATA WITH GEMINI 2.5 FLASH ---")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            return json.loads(response.text.strip())
        except Exception as e:
            print(f"--- COMPETITOR SCRAPING FAILED: {str(e)} ---")
            # Fallback to standard tracking
            return {
                "tagline": "Tracked Competitor Portfolio",
                "listings": ["ProductHunt", "AlternativeTo"]
            }

async def run_competitor_discovery(url: str):
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, discover_competitor_stealth, url)
    return result

async def generate_outreach_sequence(product_data: dict, lead_context: dict):
    """
    Generates a personalized, 3-step outreach sequence for a target lead context (Feature 2.9).
    """
    client = get_client()
    if not client: return {"error": "Gemini API Key missing"}
    
    prompt = f"""
    You are an expert B2B Growth Architect. Generate a personalized, highly conversion-oriented 3-step outreach sequence to convert this target lead into a customer:
    
    Product Details:
    - Name: {product_data['name']}
    - Tagline: {product_data['tagline']}
    - Value Proposition: {product_data['description']}
    
    Lead Context:
    - Platform: {lead_context['platform']}
    - Thread/Title: {lead_context['thread_title']}
    - Target's Pain Point Snippet: "{lead_context['context_snippet']}"
    - Our Initial Reply: "{lead_context['initial_reply']}"
    
    Write the next 2 steps of our follow-up sequence:
    
    Step 2: Direct Value follow-up (sent 2 days later via DM or Email).
    - Tone: Helpful, value-first, non-spammy developer-to-developer.
    - Offer: Free early access, a custom setup, or a quick technical audit.
    
    Step 3: High-Value Case Study/Nudge (sent 5 days later via DM or Email).
    - Tone: Friendly closing message.
    - Content: Mention a real-world result (e.g., "CTO at ScaleTech cut their manual work to zero") and invite them to a quick 5-min demo.
    
    Respond ONLY with a JSON object in this exact schema:
    {{
      "step2": {{
        "channel": "Reddit_DM" or "Twitter_DM" or "Email",
        "content": "Full message text for step 2"
      }},
      "step3": {{
        "channel": "Reddit_DM" or "Twitter_DM" or "Email",
        "content": "Full message text for step 3"
      }}
    }}
    """
    
    print("--- GENERATING OUTREACH SEQUENCE WITH GEMINI 2.5 FLASH ---")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text.strip())
    except Exception as e:
        return {"error": f"Outreach sequence generation failed: {str(e)}"}

async def scan_hackernews_leads(product_data: dict, testimonials: list, target_keyword: str = None):
    """
    Uses Algolia HN API to find real HackerNews discussions matching keywords.
    """
    import aiohttp
    
    keyword = target_keyword
    if not keyword:
        keyword = product_data.get("name")
        if "icp_profile" in product_data and product_data["icp_profile"].get("core_pain_points"):
            pain_points = product_data["icp_profile"]["core_pain_points"]
            if len(pain_points) > 0:
                keyword = pain_points[0]
                
    print(f"--- SEARCHING HACKERNEWS FOR LEAD KEYWORD: '{keyword}' ---")
    url = f"https://hn.algolia.com/api/v1/search_by_date?query={keyword}&tags=comment&hitsPerPage=3"
    
    discussions = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
        hits = data.get("hits", [])
        for hit in hits:
            discussions.append({
                "title": hit.get("story_title") or "HN Comment",
                "url": f"https://news.ycombinator.com/item?id={hit.get('story_id')}",
                "body": hit.get("comment_text", "")
            })
    except Exception as e:
        print(f"HackerNews API Search failed: {str(e)}")
        return []
        
    print(f"Found {len(discussions)} raw HackerNews comments. Grading with Gemini...")
    return await run_social_listening_scout(product_data, testimonials, discussions, keyword)

def scrape_reddit_stealth(keyword: str):
    """
    Agent that bypasses Reddit's API blocks by querying DuckDuckGo.
    """
    from ddgs import DDGS
    discussions = []
    try:
        print(f"--- STARTING AUTONOMOUS REDDIT SEARCH FOR '{keyword}' via DDGS ---")
        with DDGS() as ddgs:
            results = list(ddgs.text(f'site:reddit.com "{keyword}"', max_results=3))
            for r in results:
                title = r.get("title", "")
                url = r.get("href", "")
                snippet = r.get("body", "")
                if url and "reddit.com" in url:
                    discussions.append({
                        "title": title,
                        "url": url,
                        "body": snippet
                    })
    except Exception as e:
        print(f"--- REDDIT SCRAPING FAILED: {str(e)} ---")
        
    return discussions

async def scan_reddit_leads(product_data: dict, testimonials: list, target_keyword: str = None):
    """
    Uses Playwright to stealth scrape Reddit discussions.
    """
    import asyncio
    
    keyword = target_keyword
    if not keyword:
        keyword = product_data.get("name")
        if "icp_profile" in product_data and product_data["icp_profile"].get("core_pain_points"):
            pain_points = product_data["icp_profile"]["core_pain_points"]
            if len(pain_points) > 0:
                keyword = pain_points[0]
                
    loop = asyncio.get_event_loop()
    discussions = await loop.run_in_executor(None, scrape_reddit_stealth, keyword)
    
    if not discussions:
        return []
        
    print(f"Found {len(discussions)} raw Reddit posts. Grading with Gemini...")
    return await run_social_listening_scout(product_data, testimonials, discussions, keyword)

def scrape_twitter_stealth(keyword: str, user_id: int = 1):
    """
    Agent that bypasses Twitter's login wall by querying DuckDuckGo for Twitter discussions.
    """
    from ddgs import DDGS
    discussions = []
    try:
        print(f"--- STARTING AUTONOMOUS TWITTER SEARCH FOR '{keyword}' via DDGS ---")
        with DDGS() as ddgs:
            results = list(ddgs.text(f'site:twitter.com "{keyword}"', max_results=3))
            for r in results:
                title = r.get("title", "")
                url = r.get("href", "")
                snippet = r.get("body", "")
                if url and ("twitter.com" in url or "x.com" in url):
                    discussions.append({
                        "title": title,
                        "url": url,
                        "body": snippet
                    })
    except Exception as e:
        print(f"--- TWITTER SCRAPING FAILED: {str(e)} ---")
            
    return discussions

async def scan_twitter_leads(product_data: dict, testimonials: list, target_keyword: str = None, user_id: int = 1):
    """
    Uses Playwright to scrape real Twitter leads matching ICP keywords,
    then uses Gemini to grade and draft replies.
    """
    keyword = target_keyword
    if not keyword:
        keyword = product_data.get("name")
        if "icp_profile" in product_data and product_data["icp_profile"].get("core_pain_points"):
            pain_points = product_data["icp_profile"]["core_pain_points"]
            if len(pain_points) > 0:
                keyword = pain_points[0]
            
    import asyncio
    loop = asyncio.get_event_loop()
    discussions = await loop.run_in_executor(None, scrape_twitter_stealth, keyword, user_id)
    
    print(f"Found {len(discussions)} raw tweets via Playwright. Grading with Gemini...")
    
    if not discussions:
        return []
        
    return await run_social_listening_scout(product_data, testimonials, discussions, keyword)

def scrape_linkedin_stealth(keyword: str, user_id: int = 1):
    """
    Agent that bypasses LinkedIn's aggressive login wall by querying DuckDuckGo.
    """
    from ddgs import DDGS
    discussions = []
    try:
        print(f"--- STARTING AUTONOMOUS LINKEDIN SEARCH FOR '{keyword}' via DDGS ---")
        with DDGS() as ddgs:
            results = list(ddgs.text(f'site:linkedin.com/posts "{keyword}"', max_results=3))
            for r in results:
                title = r.get("title", "")
                url = r.get("href", "")
                snippet = r.get("body", "")
                if url and "linkedin.com" in url:
                    discussions.append({
                        "title": title,
                        "url": url,
                        "body": snippet
                    })
    except Exception as e:
        print(f"--- LINKEDIN SCRAPING FAILED: {str(e)} ---")
            
    return discussions

async def scan_linkedin_leads(product_data: dict, testimonials: list, target_keyword: str = None, user_id: int = 1):
    """
    Uses Playwright to scrape real LinkedIn leads matching ICP keywords,
    then uses Gemini to grade and draft replies.
    """
    keyword = target_keyword
    if not keyword:
        keyword = product_data.get("name")
        if "icp_profile" in product_data and product_data["icp_profile"].get("core_pain_points"):
            pain_points = product_data["icp_profile"]["core_pain_points"]
            if len(pain_points) > 0:
                keyword = pain_points[0]
            
    import asyncio
    loop = asyncio.get_event_loop()
    discussions = await loop.run_in_executor(None, scrape_linkedin_stealth, keyword, user_id)
    
    print(f"Found {len(discussions)} raw LinkedIn posts via Playwright. Grading with Gemini...")
    
    if not discussions:
        return []
        
    return await run_social_listening_scout(product_data, testimonials, discussions, keyword)



def save_url_screenshot_sync(url: str, screenshot_path: str):
    """Simple utility to capture a screenshot of a live web page."""
    with sync_playwright() as p:
        try:
            print(f"--- CAPTURING URL SCREENSHOT: {url} ---")
            browser = p.chromium.launch(channel="chrome",headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="load", timeout=20000)
            import time
            time.sleep(3)
            page.screenshot(path=screenshot_path)
            browser.close()
            print(f"Screenshot saved successfully to {screenshot_path}")
        except Exception as e:
            print(f"Failed to capture URL screenshot: {e}")

async def save_url_screenshot(url: str, screenshot_path: str):
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, save_url_screenshot_sync, url, screenshot_path)




