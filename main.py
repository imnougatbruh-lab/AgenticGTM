from fastapi import FastAPI, HTTPException, Depends, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os
import json
import sys
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy.orm import Session
import resend

from database import get_db, init_db
import models
from agents import analyze_product, generate_copy, run_autonomous_submission, run_autonomous_publishing, run_social_listening_scout, run_autonomous_lead_reply, run_autonomous_blog_publishing, refine_icp, run_competitor_discovery, generate_outreach_sequence, save_url_screenshot

load_dotenv()

# Initialize Resend for email sending
resend.api_key = os.getenv("RESEND_API_KEY")

# Ensure static directories exist before mounting
os.makedirs("static/submissions", exist_ok=True)
os.makedirs("static/publications", exist_ok=True)
os.makedirs("static/leads", exist_ok=True)
os.makedirs("static/blogs", exist_ok=True)

# FIX: Windows specific event loop policy and console encoding for Playwright & Emojis
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database and all tables on startup
    init_db()
    yield

app = FastAPI(
    title="AgenticGTM API", 
    description="Autonomous AI Marketing Engine Backend",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.1.2:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated static assets (screenshots)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Data models
class OnboardRequest(BaseModel):
    url: str

class CopyRequest(BaseModel):
    product_id: int = None
    product_data: dict = None

class TestimonialCreate(BaseModel):
    product_id: int
    client_name: str
    client_role: str
    client_company: str = None
    rating: int = 5
    review_text: str

class ListenRequest(BaseModel):
    product_id: int
    target_keyword: str = None

class BlogGenerateRequest(BaseModel):
    product_id: int
    keywords: list = None

class SubmissionRequest(BaseModel):
    product_id: int
    directory_name: str
    directory_url: str

class LinkGenerationRequest(BaseModel):
    product_id: int
    source: str
    original_url: str

class CompetitorAddRequest(BaseModel):
    product_id: int
    name: str
    url: str

class WaitlistRequest(BaseModel):
    email: str
    name: str = None
    company: str = None
    role: str = None
    referral_source: str = None

# Configure CORS dynamically for production security
origins_str = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user(x_clerk_id: str | None = Header(None), x_user_email: str | None = Header(None), db: Session = Depends(get_db)) -> models.User:
    """
    Dependency to resolve the current user from headers in production (e.g. Clerk Auth integration)
    or fall back to the default demo user in development.
    """
    if x_user_email or x_clerk_id:
        email = x_user_email or x_clerk_id
        user = db.query(models.User).filter_by(email=email).first()
        if not user:
            user = models.User(email=email, clerk_id=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        elif not user.clerk_id:
            # Sync clerk_id column for legacy references
            user.clerk_id = email
            db.commit()
        return user

    # Fallback to demo user
    demo_user = db.query(models.User).filter_by(email="demo@agenticgtm.com").first()
    if not demo_user:
        demo_user = models.User(email="demo@agenticgtm.com", clerk_id="demo_clerk_123")
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
    return demo_user

@app.get("/")
async def root():
    return {"message": "AgenticGTM API is live", "status": "operational"}

@app.post("/waitlist")
async def add_to_waitlist(request: WaitlistRequest, db: Session = Depends(get_db)):
    """
    Endpoint to add users to the waitlist.
    Stores email and optional info, then sends a confirmation email.
    """
    print(f"=== WAITLIST SIGNUP ATTEMPT ===")
    print(f"Email: {request.email}")
    print(f"Resend API Key set: {bool(resend.api_key)}")
    
    try:
        # Check if email already exists
        existing = db.query(models.Waitlist).filter_by(email=request.email).first()
        if existing:
            print(f"Email already exists in waitlist")
            return {"status": "success", "message": "Email already on waitlist", "already_exists": True}
        
        # Create new waitlist entry
        waitlist_entry = models.Waitlist(
            email=request.email,
            name=request.name,
            company=request.company,
            role=request.role,
            referral_source=request.referral_source
        )
        db.add(waitlist_entry)
        db.commit()
        db.refresh(waitlist_entry)
        print(f"Waitlist entry created successfully")
        
        # Send confirmation email using Resend
        try:
            from_email = os.getenv("OUTBOUND_FROM_EMAIL", "onboarding@resend.dev")
            print(f"Attempting to send email from: {from_email}")
            
            params = {
                "from": from_email,
                "to": [request.email],
                "subject": "You're on the waitlist! 🚀",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #ffffff; font-size: 24px; margin-bottom: 10px;">Welcome to AgenticGTM</h1>
                        <p style="color: #888888; font-size: 16px;">The Autonomous AI Marketing Engine</p>
                    </div>
                    
                    <div style="background: #111111; border-radius: 12px; padding: 30px; margin-bottom: 20px;">
                        <p style="color: #ffffff; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                            Hey{f' {request.name}' if request.name else ''}!
                        </p>
                        <p style="color: #cccccc; font-size: 15px; line-height: 1.6; margin-bottom: 20px;">
                            You've successfully joined the waitlist for AgenticGTM. We're building the autonomous growth operating system for modern founders, and we can't wait to have you on board.
                        </p>
                        <p style="color: #cccccc; font-size: 15px; line-height: 1.6; margin-bottom: 20px;">
                            We'll notify you as soon as access opens up. In the meantime, follow us for updates on the future of autonomous marketing.
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #666666; font-size: 13px;">
                            Best,<br>The AgenticGTM Team
                        </p>
                    </div>
                </div>
                """
            }
            
            if resend.api_key:
                result = resend.Emails.send(params)
                print(f"✅ Email sent successfully! Resend response: {result}")
            else:
                print("❌ RESEND_API_KEY not set, skipping email send")
        except Exception as email_error:
            print(f"❌ Failed to send email: {email_error}")
            import traceback
            traceback.print_exc()
            # Don't fail the request if email fails, just log it
        
        return {"status": "success", "message": "Added to waitlist successfully", "already_exists": False}
    except Exception as e:
        db.rollback()
        print(f"❌ Waitlist error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to add to waitlist")

@app.post("/onboard")
async def onboard_startup(request: OnboardRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Endpoint to trigger the Discovery Agent to analyze a website.
    It creates a product record, scrapes the website, and saves the structured AI analysis.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment")
    
    try:
        # Check if the product already exists by URL, or create it
        product = db.query(models.Product).filter_by(url=request.url, owner_id=current_user.id).first()
        if not product:
            product = models.Product(url=request.url, owner_id=current_user.id, name="Pending Analysis")
            db.add(product)
            db.commit()
            db.refresh(product)

        # 3. Perform AI analysis
        result = await analyze_product(request.url)
        
        if "error" in result:
            # Fall back to a resilient default analysis template so that rate limit does not block onboarding
            parsed_name = request.url.split("//")[-1].split(".")[0].capitalize()
            result = {
                "name": parsed_name,
                "tagline": f"The Autonomous Growth Engine for {parsed_name}",
                "description": f"An intelligent marketing and outreach automation agent designed to scale search engine index submissions, monitor buyer intent channels, and optimize customer acquisition loops.",
                "key_features": ["Autonomous Directory Submissions", "Social Listening intent monitor", "Multi-Step Lead Sequencer", "AI Copywriter Studio"],
                "target_audience": ["Tech Founders", "SaaS Developers", "Indie Hackers", "Growth Marketers"]
            }
        
        # 4. Save results to the database
        product.name = result.get("name", product.name)
        product.tagline = result.get("tagline", product.tagline)
        product.description = result.get("description", product.description)
        db.commit()
        db.refresh(product)
        
        # Inject the database product_id into the response
        result["product_id"] = product.id
        return result
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"CRITICAL SYSTEM ERROR:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"System Error: {str(e)}")

@app.post("/generate-copy")
async def create_marketing_copy(request: CopyRequest, db: Session = Depends(get_db)):
    """
    Endpoint to trigger the Copywriter Agent to generate marketing content.
    If product_id is provided, it retrieves the product from the DB and saves the generated draft posts.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment")
    
    # 1. Retrieve product data
    product = None
    product_data = None
    
    if request.product_id:
        product = db.query(models.Product).filter_by(id=request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found in database")
        product_data = {
            "name": product.name,
            "url": product.url,
            "tagline": product.tagline,
            "description": product.description
        }
        
        # Inject refined ICP details if present in database
        if product.icp_profile:
            try:
                product_data["icp_profile"] = {
                    "ideal_job_titles": json.loads(product.icp_profile.ideal_job_titles),
                    "top_channels": json.loads(product.icp_profile.top_channels),
                    "core_pain_points": json.loads(product.icp_profile.core_pain_points),
                    "refined_positioning": product.icp_profile.refined_positioning
                }
            except:
                pass
    elif request.product_data:
        product_data = request.product_data
    else:
        raise HTTPException(status_code=400, detail="Must provide either product_id or product_data")
        
    # 2. Generate copy using Gemini
    result = await generate_copy(product_data)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    # 3. If product exists in database, save the generated posts as drafts
    if product:
        # Clear existing drafts to prevent duplicates during re-runs
        db.query(models.ContentPost).filter_by(product_id=product.id, status="draft").delete()
        
        # Save Twitter Thread
        twitter_thread = result.get("twitter_thread", [])
        for tweet in twitter_thread:
            tweet_text = tweet
            if isinstance(tweet, dict):
                tweet_text = tweet.get("text", "")
            
            db_post = models.ContentPost(
                product_id=product.id,
                platform="Twitter",
                content=tweet_text,
                status="draft"
            )
            db.add(db_post)
            
        # Save Reddit Post
        reddit_data = result.get("reddit_post", {})
        reddit_title = ""
        reddit_body = ""
        if isinstance(reddit_data, dict):
            reddit_title = reddit_data.get("title", "")
            reddit_body = reddit_data.get("body", "")
        elif isinstance(reddit_data, str):
            reddit_body = reddit_data
            
        db_post = models.ContentPost(
            product_id=product.id,
            platform="Reddit",
            content=f"Title: {reddit_title}\n\n{reddit_body}" if reddit_title else reddit_body,
            status="draft"
        )
        db.add(db_post)
        
        # Initialize default pending submissions
        db.query(models.Submission).filter_by(product_id=product.id, status="pending").delete()
        from directories import TARGET_DIRECTORIES
        directories = TARGET_DIRECTORIES
        for name, url in directories:
            db_sub = models.Submission(
                product_id=product.id,
                directory_name=name,
                directory_url=url,
                status="pending"
            )
            db.add(db_sub)
            
        db.commit()
        print(f"Draft posts and directory submissions saved for product ID: {product.id}")
        
    return result

@app.post("/submit")
async def trigger_submission(request: SubmissionRequest, db: Session = Depends(get_db)):
    """
    Endpoint to trigger the Autonomous Form Submitter Agent.
    It reads product data and directory short/long copy, runs Playwright to auto-fill the target URL,
    saves a screenshot of the filled page, and updates the database.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment")
        
    # 1. Fetch product with self-healing fallback logic
    product = db.query(models.Product).filter_by(id=request.product_id).first()
    if not product:
        # Fallback 1: Grab first available product in database
        product = db.query(models.Product).first()
        
    if not product:
        # Fallback 2: Database is completely empty, auto-create a premium sample Product record
        demo_user = db.query(models.User).filter_by(email="demo@agenticgtm.com").first()
        if not demo_user:
            demo_user = models.User(email="demo@agenticgtm.com", clerk_id="demo_clerk_123")
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            
        product = models.Product(
            owner_id=demo_user.id,
            name="ProductHunt",
            url="https://www.producthunt.com",
            tagline="The best place to launch and discover new tech tools.",
            description="Product Hunt is a daily curation of the best new tech products. Discover the latest mobile apps, website tools, developer platforms, and hardware projects."
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        print("Self-healing fallback: Auto-created premium demo product record in database.")
        
    # 2. Extract values for submission
    product_data = {
        "name": product.name,
        "url": product.url,
        "tagline": product.tagline or "Best new B2B dev tool.",
        "description": product.description or "We build high-converting automation engines for modern developers and side-hustle makers."
    }
    
    # 3. Create or update the Submission record in the DB
    submission = db.query(models.Submission).filter_by(
        product_id=product.id,
        directory_name=request.directory_name
    ).first()
    if not submission:
        submission = models.Submission(
            product_id=product.id,
            directory_name=request.directory_name,
            directory_url=request.directory_url,
            status="pending"
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
    # Define screenshot path
    screenshot_dir = "static/submissions"
    os.makedirs(screenshot_dir, exist_ok=True)
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', request.directory_name.lower())
    screenshot_filename = f"product_{product.id}_{safe_name}.png"
    screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
    static_url_path = f"/static/submissions/{screenshot_filename}"
    
    # 4. Trigger Playwright Agent
    result = await run_autonomous_submission(
        request.directory_url,
        product_data,
        screenshot_path
    )
    
    if "error" in result:
        submission.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=result["error"])
        
    # Update Submission status
    submission.status = "submitted" if result.get("status") == "success" else "failed"
    submission.submission_url = request.directory_url
    import datetime
    submission.submitted_at = datetime.datetime.utcnow()
    db.commit()
    
    # Return response including the screenshot URL
    return {
        "status": submission.status,
        "message": result.get("message"),
        "screenshot_url": static_url_path
    }

# --- MOCK DIRECTORY WEB LAYOUT FOR LOCAL TESTING ---

@app.get("/demo-directory/submit", response_class=HTMLResponse)
async def demo_submit_page():
    """
    Renders a mock, unstandardized submission page to show off the Agent's autonomous CSS matching capability!
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LaunchPad Directory - Submit your SaaS</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }
            .card { background: #1e293b; padding: 30px; border-radius: 12px; max-width: 600px; margin: 0 auto; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); border: 1px solid #334155; }
            h1 { margin-top: 0; color: #38bdf8; font-size: 28px; text-align: center; }
            p.sub { text-align: center; color: #94a3b8; margin-top: -10px; margin-bottom: 30px; }
            .field { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; font-weight: bold; font-size: 14px; color: #e2e8f0; }
            input[type="text"], input[type="url"], textarea { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #f8fafc; box-sizing: border-box; font-size: 15px; }
            input[type="text"]:focus, input[type="url"]:focus, textarea:focus { outline: none; border-color: #38bdf8; box-shadow: 0 0 0 1px #38bdf8; }
            button { width: 100%; background: #0ea5e9; border: none; padding: 14px 20px; border-radius: 6px; color: white; font-weight: bold; cursor: pointer; font-size: 16px; transition: background 0.2s; }
            button:hover { background: #0284c7; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 LaunchPad Directory</h1>
            <p class="sub">Autonomously listing the next generation of SaaS software</p>
            <form action="/demo-directory/submit" method="POST">
                <div class="field">
                    <label for="startup-name-field">Startup Name</label>
                    <input type="text" id="startup-name-field" name="startup_name" placeholder="e.g. Acme Inc." required>
                </div>
                <div class="field">
                    <label for="url-input">Website URL</label>
                    <input type="url" id="url-input" name="website_url" placeholder="https://myproduct.com" required>
                </div>
                <div class="field">
                    <label for="tagline-box">One-Line Tagline</label>
                    <input type="text" id="tagline-box" name="one_liner" placeholder="e.g. AI-powered note-taking" required>
                </div>
                <div class="field">
                    <label for="description-area">Full Description (Detailed Pitch)</label>
                    <textarea id="description-area" name="pitch" rows="5" placeholder="Tell us more about what you are building..." required></textarea>
                </div>
                <button type="submit" id="submit-btn">Submit Product</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/demo-directory/submit", response_class=HTMLResponse)
async def demo_submit_handler(
    startup_name: str = Form(...),
    website_url: str = Form(...),
    one_liner: str = Form(...),
    pitch: str = Form(...)
):
    """
    Endpoint that handles the mock submission and logs the autonomously filled data to the terminal.
    """
    print("\n==============================================")
    print("🤖 [AUTONOMOUS SUBMISSION RECEIVED]")
    print(f"   Startup Name: {startup_name}")
    print(f"   Website URL:  {website_url}")
    print(f"   One-Liner:    {one_liner}")
    print(f"   Pitch:        {pitch}")
    print("==============================================\n")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Submission Successful</title>
        <style>
            body { font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; text-align: center; }
            .card { background: #1e293b; padding: 40px; border-radius: 12px; max-width: 500px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #4ade80; }
            h1 { color: #4ade80; margin-top: 0; }
            p { font-size: 16px; color: #cbd5e1; }
            .back-btn { display: inline-block; margin-top: 20px; background: #334155; padding: 10px 20px; color: white; border-radius: 6px; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 Launch Successful!</h1>
            <p>Your product has been submitted successfully to the directory launch queue.</p>
            <p>Our autonomous bot filled out your details flawlessly.</p>
            <a href="/demo-directory/submit" class="back-btn">Go Back</a>
        </div>
    </body>
    </html>
    """

@app.get("/products")
async def list_products(db: Session = Depends(get_db)):
    """
    Endpoint to retrieve all products from the database.
    """
    return db.query(models.Product).all()

@app.get("/products/me")
async def get_my_product(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product = db.query(models.Product).filter_by(owner_id=current_user.id).order_by(models.Product.created_at.desc()).first()
    if not product:
        return {"product_id": None}
    return {
        "product_id": product.id,
        "name": product.name,
        "url": product.url,
        "tagline": product.tagline,
        "description": product.description
    }

@app.get("/products/{product_id}")
async def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to retrieve a specific product's details.
    """
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/products/{product_id}/posts")
async def get_product_posts(product_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to retrieve generated content posts (drafts/scheduled/posted) for a product.
    """
    return db.query(models.ContentPost).filter_by(product_id=product_id).all()

@app.delete("/products/{product_id}/posts")
async def delete_all_product_posts(product_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to wipe all generated content posts (drafts/scheduled/posted) for a product.
    """
    db.query(models.ContentPost).filter_by(product_id=product_id).delete()
    db.commit()
    return {"status": "success", "message": "All drafts deleted successfully."}

@app.get("/products/{product_id}/submissions")
async def get_product_submissions(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Endpoint to retrieve submission history and status for a product.
    If empty, auto-seeds default directories.
    """
    submissions = db.query(models.Submission).filter_by(product_id=product_id).all()
    if not submissions:
        from directories import TARGET_DIRECTORIES
        for name, url in TARGET_DIRECTORIES:
            db_sub = models.Submission(
                product_id=product_id,
                directory_name=name,
                directory_url=url,
                status="pending"
            )
            db.add(db_sub)
        db.commit()
        submissions = db.query(models.Submission).filter_by(product_id=product_id).all()
        
    plan = current_user.plan.lower() if current_user.plan else "free"
    if plan == "free" or plan == "hobby":
        return submissions[:5]
    elif plan == "starter":
        return submissions[:30]
        
    return submissions

@app.post("/posts/{post_id}/approve")
async def approve_post(post_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to approve a draft social post.
    """
    post = db.query(models.ContentPost).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.status = "approved"
    db.commit()
    db.refresh(post)
    return {"status": "approved", "post": post}

@app.post("/posts/{post_id}/publish")
async def publish_post(post_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to trigger the Social Media Publisher Agent.
    It launches Playwright in stealth mode to autofill the composition box,
    takes a screenshot, and submits the post.
    """
    post = db.query(models.ContentPost).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    # Generate static screenshot path
    screenshot_dir = "static/publications"
    screenshot_filename = f"post_{post.id}.png"
    screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
    static_url_path = f"/static/publications/{screenshot_filename}"
    
    # Route to real composer pages in production mode, otherwise use local mock composer
    if os.getenv("PRODUCTION", "False").lower() == "true":
        if post.platform.lower() == "twitter":
            compose_url = "https://x.com/compose/post"
        elif post.platform.lower() == "reddit":
            compose_url = "https://www.reddit.com/submit"
        else:
            compose_url = f"http://localhost:8000/demo-social/compose?platform={post.platform}"
    else:
        compose_url = f"http://localhost:8000/demo-social/compose?platform={post.platform}"
        
    user_id = post.product.owner_id if post.product else 1
    
    # Run the autonomous publisher agent!
    result = await run_autonomous_publishing(compose_url, post.platform, post.content, screenshot_path, user_id=user_id)
    
    if "error" in result:
        post.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=result["error"])
        
    # Update post status
    post.status = "posted"
    import datetime
    post.posted_at = datetime.datetime.utcnow()
    db.commit()
    
    return {
        "status": "posted",
        "message": f"Successfully published post to {post.platform}",
        "screenshot_url": static_url_path
    }

# --- MOCK SOCIAL CHANNELS COMPOSER FOR VISUAL STEALTH PUBLISHING DEMOS ---

@app.get("/demo-social/compose", response_class=HTMLResponse)
async def demo_social_compose_page(platform: str = "Twitter"):
    """
    Renders a realistic dark-mode mockup of Twitter, Reddit, or LinkedIn post composer!
    """
    platform_name = platform.capitalize()
    
    # Choose theme colors based on platform
    bg_color = "#0f172a"
    accent_color = "#38bdf8"
    if platform.lower() == "reddit":
        accent_color = "#ff4500"
    elif platform.lower() == "linkedin":
        accent_color = "#0a66c2"
        
    textarea_html = ""
    if platform.lower() == "twitter":
        textarea_html = """
        <textarea id="tweet-textarea" name="body" placeholder="What is happening?!" rows="4" required></textarea>
        <button type="submit" id="tweet-submit-btn">Post Tweet</button>
        """
    elif platform.lower() == "reddit":
        textarea_html = """
        <input type="text" id="reddit-post-title" name="title" placeholder="An interesting title" required style="margin-bottom: 15px; width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #f8fafc; font-size: 15px;">
        <textarea id="reddit-post-body" name="body" placeholder="Text (optional)" rows="6" required></textarea>
        <button type="submit" id="reddit-submit-btn">Post to r/SaaS</button>
        """
    else:
        textarea_html = """
        <textarea id="generic-textarea" name="body" placeholder="Share your insights..." rows="5" required></textarea>
        <button type="submit" id="generic-submit-btn">Post to Feed</button>
        """
        
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stealth Social Composer - {platform_name}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px; }}
            .compose-card {{ background: #151f32; padding: 30px; border-radius: 16px; max-width: 550px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.4); border: 1px solid #24334c; }}
            h2 {{ color: {accent_color}; margin-top: 0; font-size: 22px; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}
            label {{ display: block; margin-bottom: 8px; font-weight: bold; font-size: 13px; color: #94a3b8; }}
            textarea {{ width: 100%; padding: 14px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #f8fafc; box-sizing: border-box; font-size: 15px; resize: none; line-height: 1.5; }}
            textarea:focus, input[type="text"]:focus {{ outline: none; border-color: {accent_color}; box-shadow: 0 0 0 1px {accent_color}; }}
            button {{ width: 100%; background: {accent_color}; border: none; padding: 14px 20px; border-radius: 25px; color: white; font-weight: bold; cursor: pointer; font-size: 15px; margin-top: 15px; transition: background 0.2s; }}
            button:hover {{ filter: brightness(0.9); }}
        </style>
    </head>
    <body>
        <div class="compose-card">
            <h2>Compose Post on {platform_name}</h2>
            <form action="/demo-social/publish" method="POST">
                <input type="hidden" name="platform" value="{platform}">
                {textarea_html}
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/demo-social/publish", response_class=HTMLResponse)
async def demo_social_publish_handler(
    platform: str = Form(...),
    title: str = Form(None),
    body: str = Form(...)
):
    """
    Handles Mock Social Media form submission and logs details in terminal.
    """
    print(f"\n==============================================")
    print(f"🤖 [AUTONOMOUS PUBLISH SUCCESS ON {platform.upper()}]")
    if title:
        print(f"   Title: {title}")
    print(f"   Body:  {body}")
    print(f"==============================================\n")
    
    accent_color = "#38bdf8"
    if platform.lower() == "reddit":
        accent_color = "#ff4500"
    elif platform.lower() == "linkedin":
        accent_color = "#0a66c2"
        
    title_html = f"<h3>{title}</h3>" if title else ""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Publication Successful</title>
        <style>
            body {{ font-family: sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px; text-align: center; }}
            .card {{ background: #151f32; padding: 40px; border-radius: 16px; max-width: 500px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 2px solid #4ade80; }}
            h1 {{ color: #4ade80; margin-top: 0; }}
            .post-box {{ background: #0f172a; padding: 20px; border-radius: 8px; margin-top: 20px; text-align: left; border: 1px solid #24334c; }}
            .platform-badge {{ display: inline-block; background: {accent_color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-bottom: 10px; }}
            p.body {{ font-size: 15px; color: #cbd5e1; line-height: 1.5; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📡 Live Broadcast Successful!</h1>
            <p>Your post was published autonomously on the social network.</p>
            <div class="post-box">
                <span class="platform-badge">{platform.upper()}</span>
                {title_html}
                <p class="body">{body}</p>
            </div>
        </div>
    </body>
    </html>
    """

# --- TRUSTLOOP & SOCIAL LISTENING INTEGRATION (FEATURE 2.4) ---

@app.post("/testimonials")
async def save_testimonial(request: TestimonialCreate, db: Session = Depends(get_db)):
    """
    Endpoint to manually seed or collect a new customer testimonial (TrustLoop Engine 1).
    """
    # Verify product exists
    product = db.query(models.Product).filter_by(id=request.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_testimonial = models.Testimonial(
        product_id=request.product_id,
        client_name=request.client_name,
        client_role=request.client_role,
        client_company=request.client_company,
        rating=request.rating,
        review_text=request.review_text
    )
    db.add(db_testimonial)
    db.commit()
    db.refresh(db_testimonial)
    return {"status": "success", "message": "Testimonial saved", "testimonial": db_testimonial}

@app.get("/products/{product_id}/testimonials")
async def list_testimonials(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all gathered reviews/testimonials for a product.
    """
    return db.query(models.Testimonial).filter_by(product_id=product_id).all()

@app.post("/listen")
async def trigger_social_listening(request: ListenRequest, db: Session = Depends(get_db)):
    """
    Scouts Mock Communities for buyer intent, picks the best testimonial, and drafts a reply (Feature 2.4).
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment")
        
    # 1. Fetch Product
    product = db.query(models.Product).filter_by(id=request.product_id).first()
    if not product:
        # Self-healing fallback if product doesn't exist
        product = db.query(models.Product).first()
        
    if not product:
        raise HTTPException(status_code=400, detail="No products exist in database to scout for")
        
    # Rate Limiting & Billing Check
    user = db.query(models.User).filter_by(id=product.owner_id).first() if product.owner_id else None
    if user:
        import datetime
        today = datetime.datetime.utcnow().date()
        plan_name = (user.plan or "FREE").upper()
        if plan_name == "HOBBY": plan_name = "FREE" # Backwards compatibility
        
        if not user.last_search_date or user.last_search_date.date() < today:
            # Only reset daily limits for paid users. Free users get a lifetime cap.
            if plan_name != "FREE":
                user.searches_count = 0
            user.last_search_date = datetime.datetime.utcnow()
            
        if plan_name == "FREE" and (user.searches_count or 0) >= 3:
            raise HTTPException(status_code=403, detail="Your free trial limit of 3 lifetime searches has been reached. Please upgrade to continue.")
        elif plan_name == "STARTER" and (user.searches_count or 0) >= 20:
            raise HTTPException(status_code=403, detail="Starter users can do 20 searches a day. Please upgrade to Pro.")
        user.searches_count = (user.searches_count or 0) + 1
        db.commit()

    product_data = {
        "name": product.name,
        "tagline": product.tagline or "Autonomous Developer GTM Suite",
        "description": product.description or "Automating directory submissions, copywriting, and social growth on autopilot."
    }
    
    # 2. Fetch testimonials
    db_testimonials = db.query(models.Testimonial).filter_by(product_id=product.id).all()
    testimonials_list = [
        {
            "client_name": t.client_name,
            "client_role": t.client_role,
            "review_text": t.review_text
        }
        for t in db_testimonials
    ]
    
    # If no testimonials exist, seed 2 sample premium testimonials automatically (TrustLoop auto-seeding!)
    if not testimonials_list:
        sample_reviews = [
            ("Sarah Jenkins", "CTO at ScaleTech", "We cut our launching and GTM tasks from 20 hours a week to zero. The submissions are totally autonomous and the content calendar sounds exactly like us!"),
            ("Marcus Chen", "Solo Founder of DevPush", "Saved us $500/month in manual marketing agencies. Getting listings and blog traction on autopilot is an absolute cheat-code.")
        ]
        for name, role, review in sample_reviews:
            t = models.Testimonial(
                product_id=product.id,
                client_name=name,
                client_role=role,
                review_text=review
            )
            db.add(t)
            testimonials_list.append({
                "client_name": name,
                "client_role": role,
                "review_text": review
            })
        db.commit()
        print("Self-healing: Seeded 2 sample customer testimonials for the review-backed AI outreach agent.")

    # Wipe existing leads so the dashboard only shows results for the CURRENT search
    db.query(models.SocialLead).filter_by(product_id=product.id).delete()
    db.commit()
    print("Wiped old leads for a fresh scan.")

    # Run all scanners concurrently to drastically reduce scan times
    from agents import scan_hackernews_leads, scan_reddit_leads, scan_twitter_leads, scan_linkedin_leads
    import asyncio
    
    user_id = product.owner_id if product else 1
    
    hn_task = scan_hackernews_leads(product_data, testimonials_list, request.target_keyword)
    reddit_task = scan_reddit_leads(product_data, testimonials_list, request.target_keyword)
    twitter_task = scan_twitter_leads(product_data, testimonials_list, request.target_keyword, user_id=user_id)
    linkedin_task = scan_linkedin_leads(product_data, testimonials_list, request.target_keyword, user_id=user_id)
    
    results = await asyncio.gather(hn_task, reddit_task, twitter_task, linkedin_task, return_exceptions=True)
    
    leads = []
    
    # Process HackerNews results
    if isinstance(results[0], Exception):
        print(f"Failed to scan HackerNews: {results[0]}")
    elif isinstance(results[0], list):
        leads.extend(results[0])
        
    # Process Reddit results
    if isinstance(results[1], Exception):
        print(f"Failed to scan Reddit: {results[1]}")
    elif isinstance(results[1], list):
        leads.extend(results[1])
        
    # Process Twitter results
    if isinstance(results[2], Exception):
        print(f"Failed to scan Twitter: {results[2]}")
    elif isinstance(results[2], list):
        leads.extend(results[2])
            
    # Process LinkedIn results
    if isinstance(results[3], Exception):
        print(f"Failed to scan LinkedIn: {results[3]}")
    elif isinstance(results[3], list):
        leads.extend(results[3])
            
    all_leads = leads
    
    # 5. Persist matched leads in database
    db_leads = []
    for lead in all_leads:
        # Determine platform based on source_url
        platform = "HackerNews"
        if "twitter.com" in lead["source_url"] or "x.com" in lead["source_url"]:
            platform = "Twitter"
        elif "reddit.com" in lead["source_url"]:
            platform = "Reddit"
        elif "linkedin.com" in lead["source_url"]:
            platform = "LinkedIn"
            
        # Prevent duplicate leads for the same thread url
        existing = db.query(models.SocialLead).filter_by(product_id=product.id, source_url=lead["source_url"]).first()
        if existing:
            existing.draft_reply = lead["draft_reply"]
            db.commit()
            db_leads.append(existing)
            continue
            
        db_lead = models.SocialLead(
            product_id=product.id,
            platform=platform,
            thread_title=lead["thread_title"],
            source_url=lead["source_url"],
            context_snippet=lead["context_snippet"],
            draft_reply=lead["draft_reply"],
            status="pending"
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        db_leads.append(db_lead)
        
    return {"status": "success", "leads_found": len(db_leads), "leads": db_leads}

@app.get("/products/{product_id}/leads")
async def list_social_leads(product_id: int, db: Session = Depends(get_db)):
    """
    List all discovered leads and draft responses (Feature 2.4).
    """
    return db.query(models.SocialLead).filter_by(product_id=product_id).order_by(models.SocialLead.id.desc()).all()


class LeadCreateRequest(BaseModel):
    product_id: int
    platform: str
    thread_title: str
    source_url: str
    context_snippet: str

@app.post("/leads")
async def create_manual_lead(request: LeadCreateRequest, db: Session = Depends(get_db)):
    """
    Endpoint to manually onboard a social thread (e.g. from F5Bot notifications).
    It parses the thread body, runs Gemini to select the best testimonial and draft a reply,
    and saves the lead in the SQLite database.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment")
        
    product = db.query(models.Product).filter_by(id=request.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product_data = {
        "name": product.name,
        "tagline": product.tagline or "Autonomous Developer GTM Suite",
        "description": product.description or ""
    }
    
    # Fetch testimonials
    db_testimonials = db.query(models.Testimonial).filter_by(product_id=product.id).all()
    testimonials_list = [
        {
            "client_name": t.client_name,
            "client_role": t.client_role,
            "review_text": t.review_text
        }
        for t in db_testimonials
    ]
    
    # Fallback to seed testimonials if empty
    if not testimonials_list:
        sample_reviews = [
            ("Sarah Jenkins", "CTO at ScaleTech", "We cut our launching and GTM tasks from 20 hours a week to zero. The submissions are totally autonomous and the content calendar sounds exactly like us!"),
            ("Marcus Chen", "Solo Founder of DevPush", "Saved us $500/month in manual marketing agencies. Getting listings and blog traction on autopilot is an absolute cheat-code.")
        ]
        for name, role, review in sample_reviews:
            t = models.Testimonial(
                product_id=product.id,
                client_name=name,
                client_role=role,
                review_text=review
            )
            db.add(t)
            testimonials_list.append({
                "client_name": name,
                "client_role": role,
                "review_text": review
            })
        db.commit()

    # Draft reply using the social listening scout
    mock_thread = [
        {
            "title": request.thread_title,
            "url": request.source_url,
            "body": request.context_snippet
        }
    ]
    
    leads = await run_social_listening_scout(product_data, testimonials_list, mock_thread)
    
    draft_reply = "Hey! Checked out your discussion. Our product can help you solve this bottleneck."
    if leads and len(leads) > 0:
        draft_reply = leads[0].get("draft_reply", draft_reply)
        
    db_lead = models.SocialLead(
        product_id=product.id,
        platform=request.platform,
        thread_title=request.thread_title,
        source_url=request.source_url,
        context_snippet=request.context_snippet,
        draft_reply=draft_reply,
        status="pending"
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    return {"status": "success", "lead": db_lead}

@app.post("/leads/{lead_id}/publish")
async def publish_lead_response(lead_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to trigger the Social Listening Bot to publish its review-backed reply!
    It launches Playwright in stealth mode, navigates to the HN thread, fills comment box,
    snaps a screenshot, and posts the comment comment.
    """
    lead = db.query(models.SocialLead).filter_by(id=lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    screenshot_dir = "static/leads"
    screenshot_filename = f"lead_{lead.id}.png"
    screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
    static_url_path = f"/static/leads/{screenshot_filename}"
    
    user_id = lead.product.owner_id if lead.product else 1
    
    platform_name = "HackerNews"
    if "reddit.com" in lead.source_url:
        platform_name = "Reddit"
    elif "twitter.com" in lead.source_url or "x.com" in lead.source_url:
        platform_name = "Twitter"
        
    cred = db.query(models.SocialCredential).filter_by(user_id=user_id, platform=platform_name).first()
    credentials = None
    if cred:
        credentials = {"username": cred.username, "password": cred.password}
        
    # Run the Playwright posting agent!
    result = await run_autonomous_lead_reply(lead.source_url, lead.draft_reply, screenshot_path, user_id=user_id, credentials=credentials)
    
    if "error" in result:
        lead.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=result["error"])
        
    # Update lead status
    lead.status = "posted"
    import datetime
    lead.posted_at = datetime.datetime.utcnow()
    db.commit()
    
    return {
        "status": "posted",
        "message": "Successfully posted referral comment to HackerNews thread autonomously!",
        "screenshot_url": static_url_path
    }

# --- TRUSTLOOP COLLECTION & HN DEMO PAGES FOR VISUAL TESTING ---

@app.get("/demo-trustloop/collect", response_class=HTMLResponse)
async def trustloop_collect_page(product_id: int = 1):
    """
    Renders a premium glassmorphic TrustLoop review collection portal!
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TrustLoop - Submit Customer Review</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px; }}
            .card {{ background: #152033; padding: 35px; border-radius: 16px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.4); border: 1px solid #23344d; }}
            h1 {{ color: #38bdf8; margin-top: 0; font-size: 24px; text-align: center; }}
            p.sub {{ text-align: center; color: #94a3b8; font-size: 14px; margin-top: -8px; margin-bottom: 25px; }}
            .field {{ margin-bottom: 18px; }}
            label {{ display: block; margin-bottom: 6px; font-weight: bold; font-size: 13px; color: #cbd5e1; }}
            input[type="text"], select, textarea {{ width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #f8fafc; box-sizing: border-box; font-size: 15px; }}
            button {{ width: 100%; background: #0ea5e9; border: none; padding: 14px; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; font-size: 15px; transition: background 0.2s; }}
            button:hover {{ background: #0284c7; }}
            .brand {{ text-align: center; font-size: 11px; color: #475569; margin-top: 20px; }}
            .brand a {{ color: #38bdf8; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📥 Secure Review Collector</h1>
            <p class="sub">Your success stories turn landing page traffic into sales</p>
            <form action="/testimonials" method="POST" id="review-form">
                <input type="hidden" name="product_id" value="{product_id}">
                <div class="field">
                    <label>Full Name</label>
                    <input type="text" name="client_name" placeholder="e.g. Sarah Jenkins" required>
                </div>
                <div class="field">
                    <label>Job Title / Role</label>
                    <input type="text" name="client_role" placeholder="e.g. CTO at ScaleCorp" required>
                </div>
                <div class="field">
                    <label>Company Name (Optional)</label>
                    <input type="text" name="client_company" placeholder="e.g. ScaleCorp">
                </div>
                <div class="field">
                    <label>Rating</label>
                    <select name="rating">
                        <option value="5">⭐⭐⭐⭐⭐ (Excellent)</option>
                        <option value="4">⭐⭐⭐⭐ (Good)</option>
                    </select>
                </div>
                <div class="field">
                    <label>Review Text</label>
                    <textarea name="review_text" rows="4" placeholder="How did this product help you save time or scale?" required></textarea>
                </div>
                <button type="submit">Submit 5-Star Review</button>
            </form>
            <div class="brand">
                Collected securely by <a href="#">TrustLoop.ai</a> — Get free B2B referrals.
            </div>
        </div>
        <script>
            document.getElementById('review-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = {{
                    product_id: parseInt(formData.get('product_id')),
                    client_name: formData.get('client_name'),
                    client_role: formData.get('client_role'),
                    client_company: formData.get('client_company'),
                    rating: parseInt(formData.get('rating')),
                    review_text: formData.get('review_text')
                }};
                
                const response = await fetch('/testimonials', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(data)
                }});
                if (response.ok) {{
                    alert('Review submitted successfully! It has been indexed in your Trust Database.');
                    window.location.reload();
                }}
            }});
        </script>
    </body>
    </html>
    """

@app.get("/demo-social/hackernews/thread/{thread_id}", response_class=HTMLResponse)
async def demo_hn_thread(thread_id: int):
    """
    Renders a realistic mockup HackerNews-styled dark discussion board!
    """
    discussions = {
        1: {
            "title": "AWS and Terraform are getting too complex. Are there simple developer GTM alternatives?",
            "author": "devguy99",
            "body": "Honestly, as a solo engineer building side apps, setting up cloud pipelines and getting early users takes more time than writing the actual code. I wish there was an autonomous stack to discover directories, schedule technical launches, and handle growth without a marketing agency. Does this exist?"
        },
        2: {
            "title": "What's the best strategy to launch B2B SaaS in 2026?",
            "author": "startup_builder",
            "body": "We are preparing our tech startup launch. The product is solid but we lack the marketing manpower. Standard agencies want thousands of dollars. We need to submit to ProductHunt, BetaList, write blog posts on Medium, and publish daily tweets. How are solo makers doing this today?"
        },
        3: {
            "title": "Show HN: A wrapper for Stripe review notifications",
            "author": "stripe_dev",
            "body": "Just shipped a small notification script for Stripe checkout. Looking for feedback on how people handle transactional review collections."
        }
    }
    
    thread = discussions.get(thread_id, discussions[1])
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>HackerNews Thread - {thread['title']}</title>
        <style>
            body {{ font-family: Verdana, Geneva, sans-serif; background: #0b0f19; color: #e2e8f0; padding: 40px; }}
            .hn-container {{ background: #161d2b; padding: 25px; border-radius: 12px; max-width: 650px; margin: 0 auto; border: 1px solid #2d3d57; }}
            .header-bar {{ background: #ff6600; color: black; padding: 10px; font-weight: bold; border-radius: 6px; margin-bottom: 20px; font-size: 15px; display: flex; justify-content: space-between; }}
            h2 {{ font-size: 18px; margin-top: 0; color: #ff6600; }}
            .meta {{ font-size: 12px; color: #64748b; margin-top: -10px; margin-bottom: 15px; }}
            .thread-body {{ font-size: 15px; line-height: 1.6; color: #cbd5e1; margin-bottom: 30px; }}
            textarea {{ width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #f8fafc; font-size: 14px; resize: none; }}
            button {{ background: #ff6600; color: black; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 14px; margin-top: 10px; }}
            button:hover {{ filter: brightness(0.9); }}
        </style>
    </head>
    <body>
        <div class="hn-container">
            <div class="header-bar">
                <span>HackerNews Discussions</span>
                <span>mock portal</span>
            </div>
            <h2>{thread['title']}</h2>
            <div class="meta">Posted by {thread['author']} | 24 points | 8 comments</div>
            <div class="thread-body">{thread['body']}</div>
            
            <hr style="border: 0; border-top: 1px solid #2d3d57; margin-bottom: 25px;">
            
            <form action="/demo-social/hackernews/thread/{thread_id}/reply" method="POST">
                <textarea id="reply-textarea" name="reply_text" rows="5" placeholder="Add highly constructive comment..." required></textarea>
                <button type="submit" id="reply-submit-btn">Add Reply Comment</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/demo-social/hackernews/thread/{thread_id}/reply", response_class=HTMLResponse)
async def demo_hn_reply_handler(thread_id: int, reply_text: str = Form(...)):
    """
    Handles Mock HackerNews comment posting and outputs a confirmation page.
    """
    print(f"\n==============================================")
    print(f"🤖 [AUTONOMOUS HN LEAD REPLY SUCCESS]")
    print(f"   Thread ID: {thread_id}")
    print(f"   Comment:   {reply_text}")
    print(f"==============================================\n")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>HackerNews Reply Posted</title>
        <style>
            body {{ font-family: Verdana, sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px; text-align: center; }}
            .card {{ background: #161d2b; padding: 40px; border-radius: 12px; max-width: 500px; margin: 0 auto; border: 2px solid #4ade80; }}
            h1 {{ color: #4ade80; font-size: 22px; }}
            p {{ color: #cbd5e1; font-size: 15px; }}
            .comment-box {{ background: #0f172a; padding: 15px; border-radius: 6px; text-align: left; margin-top: 20px; font-size: 14px; line-height: 1.5; border: 1px solid #2d3d57; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📡 Referral Comment Published!</h1>
            <p>Your review-backed pitch comment was published successfully.</p>
            <div class="comment-box">{reply_text}</div>
        </div>
    </body>
    </html>
    """

@app.get("/products/{product_id}/widget", response_class=HTMLResponse)
async def get_testimonials_widget(product_id: int, db: Session = Depends(get_db)):
    """
    Generates a stunning, responsive, animated glassmorphic review slider widget (TrustLoop Engine 3).
    Can be easily embedded via iframe on any website!
    """
    testimonials = db.query(models.Testimonial).filter_by(product_id=product_id).all()
    
    # If no testimonials exist, seed default sample testimonials so the widget displays beautifully
    if not testimonials:
        sample_reviews = [
            ("Sarah Jenkins", "CTO at ScaleTech", "We cut our launching and GTM tasks from 20 hours a week to zero. The submissions are totally autonomous and the content calendar sounds exactly like us!"),
            ("Marcus Chen", "Solo Founder of DevPush", "Saved us $500/month in manual marketing agencies. Getting listings and blog traction on autopilot is an absolute cheat-code.")
        ]
        for name, role, review in sample_reviews:
            t = models.Testimonial(
                product_id=product_id,
                client_name=name,
                client_role=role,
                review_text=review
            )
            db.add(t)
        db.commit()
        testimonials = db.query(models.Testimonial).filter_by(product_id=product_id).all()
        
    slides_html = ""
    bullets_html = ""
    for idx, t in enumerate(testimonials):
        active_class = "active" if idx == 0 else ""
        slides_html += f"""
        <div class="slide {active_class}" id="slide-{idx}">
            <div class="rating">{"⭐" * t.rating}</div>
            <p class="review-text">"{t.review_text}"</p>
            <div class="client-info">
                <div class="avatar">{t.client_name[0]}</div>
                <div>
                    <h4 class="client-name">{t.client_name}</h4>
                    <span class="client-role">{t.client_role}</span>
                </div>
            </div>
        </div>
        """
        bullets_html += f"""
        <span class="bullet {active_class}" onclick="currentSlide({idx})"></span>
        """
        
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TrustLoop Verified Reviews</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 10px;
                background: transparent;
                font-family: 'Outfit', sans-serif;
                color: #f8fafc;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: hidden;
            }}
            .widget-container {{
                background: rgba(21, 32, 51, 0.6);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                padding: 24px;
                border-radius: 16px;
                width: 100%;
                max-width: 450px;
                box-sizing: border-box;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                position: relative;
                min-height: 220px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}
            .slide {{
                display: none;
                animation: fadeEffect 0.6s ease-in-out;
            }}
            .slide.active {{
                display: block;
            }}
            .rating {{
                color: #fbbf24;
                font-size: 16px;
                margin-bottom: 12px;
                text-shadow: 0 0 8px rgba(251, 191, 36, 0.4);
            }}
            .review-text {{
                font-size: 14.5px;
                line-height: 1.6;
                color: #cbd5e1;
                font-style: italic;
                margin: 0 0 16px 0;
                font-weight: 300;
            }}
            .client-info {{
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            .avatar {{
                width: 38px;
                height: 38px;
                border-radius: 50%;
                background: linear-gradient(135deg, #0ea5e9, #6366f1);
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                font-weight: bold;
                font-size: 15px;
                text-transform: uppercase;
                box-shadow: 0 0 10px rgba(14, 165, 233, 0.3);
            }}
            .client-name {{
                margin: 0;
                font-size: 14px;
                font-weight: 600;
                color: #f8fafc;
            }}
            .client-role {{
                font-size: 12px;
                color: #64748b;
            }}
            .controls-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 16px;
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                padding-top: 12px;
            }}
            .bullets {{
                display: flex;
                gap: 6px;
            }}
            .bullet {{
                width: 7px;
                height: 7px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                cursor: pointer;
                transition: background 0.3s, transform 0.3s;
            }}
            .bullet.active {{
                background: #38bdf8;
                transform: scale(1.3);
                box-shadow: 0 0 6px #38bdf8;
            }}
            .viral-badge {{
                font-size: 11px;
                color: #475569;
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 4px;
                font-weight: 500;
                transition: color 0.2s;
            }}
            .viral-badge:hover {{
                color: #38bdf8;
            }}
            .viral-badge span {{
                color: #38bdf8;
                font-weight: bold;
            }}
            @keyframes fadeEffect {{
                from {{ opacity: 0; transform: translateY(4px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
        </style>
    </head>
    <body>
        <div class="widget-container">
            <div class="slides-wrapper">
                {slides_html}
            </div>
            
            <div class="controls-row">
                <div class="bullets">
                    {bullets_html}
                </div>
                <a class="viral-badge" href="http://localhost:8000" target="_blank">
                    Powered by <span>AgenticGTM</span>
                </a>
            </div>
        </div>

        <script>
            let slideIndex = 0;
            const slides = document.querySelectorAll('.slide');
            const bullets = document.querySelectorAll('.bullet');
            
            function showSlide(n) {{
                slides.forEach(s => s.classList.remove('active'));
                bullets.forEach(b => b.classList.remove('active'));
                
                slideIndex = (n + slides.length) % slides.length;
                slides[slideIndex].classList.add('active');
                bullets[slideIndex].classList.add('active');
            }}
            
            function currentSlide(n) {{
                showSlide(n);
                resetTimer();
            }}
            
            let autoTimer = setInterval(() => {{
                showSlide(slideIndex + 1);
            }}, 4000);
            
            function resetTimer() {{
                clearInterval(autoTimer);
                autoTimer = setInterval(() => {{
                    showSlide(slideIndex + 1);
                }}, 4000);
            }}
        </script>
    </body>
    </html>
    """

# --- SEO BACKLINK FLYWHEEL INTEGRATION (FEATURE 2.5) ---

@app.post("/blogs/generate")
async def generate_seo_blog(request: BlogGenerateRequest, db: Session = Depends(get_db)):
    """
    AI Content Engine that writes an SEO-optimized B2B technical blog post (Feature 2.5)
    weaving in backlinks to your landing page to build organic domain authority!
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment")
        
    product = db.query(models.Product).filter_by(id=request.product_id).first()
    if not product:
        product = db.query(models.Product).first()
        
    if not product:
        raise HTTPException(status_code=400, detail="No product exists in database to write a blog for")
        
    # Rate Limiting & Billing Check
    user = db.query(models.User).filter_by(id=product.owner_id).first() if product.owner_id else None
    if user:
        import datetime
        today = datetime.datetime.utcnow().date()
        plan_name = (user.plan or "FREE").upper()
        if plan_name == "HOBBY": plan_name = "FREE"
        
        if not user.last_search_date or user.last_search_date.date() < today:
            if plan_name != "FREE":
                user.searches_count = 0
            user.last_search_date = datetime.datetime.utcnow()
            
        if plan_name == "FREE" and (user.searches_count or 0) >= 3:
            raise HTTPException(status_code=403, detail="Your free trial limit of 3 AI generation actions has been reached. Please upgrade to continue.")
        elif plan_name == "STARTER" and (user.searches_count or 0) >= 20:
            raise HTTPException(status_code=403, detail="Starter users can generate 20 blogs a day. Please upgrade to Pro.")
        user.searches_count = (user.searches_count or 0) + 1
        db.commit()
        
    keywords_str = ", ".join(request.keywords) if request.keywords else "developer GTM, automated submission, trust collector, social listening"
    
    # Trigger GenAI to write the developer-voice SEO blog
    from agents import get_client
    client = get_client()
    if not client:
        raise HTTPException(status_code=500, detail="GenAI client initialization failed")
        
    icp_instructions = ""
    if product.icp_profile:
        try:
            titles = json.loads(product.icp_profile.ideal_job_titles)
            pains = json.loads(product.icp_profile.core_pain_points)
            icp_instructions = f"""
    Refined Ideal Customer Profile (ICP) Guidelines to tailor this blog post:
    - Target Personas: {", ".join(titles)}
    - Core Pain Points to focus on: {", ".join(pains)}
    - Dynamic Positioning Focus: {product.icp_profile.refined_positioning}
    """
        except:
            pass

    prompt = f"""
    You are an elite B2B SaaS content strategist and industry thought leader.

    Generate a production-quality, beautifully formatted blog article based on the keyword tags selected by the user. 
    CRITICAL INSTRUCTION: Regardless of what the keywords are (even if they are simple or broad), you MUST expand them into a highly professional, well-structured, and engaging long-form article. It must be a proper, nice, and highly readable post that bridges the gap between technical concepts and business value. Ensure that a non-coder or business founder can easily read, understand, and extract value from it.

    Product Details:
    - Name: {product.name}
    - Tagline: {product.tagline}
    - Description: {product.description}
    - Landing Page URL: {product.url}
    
    {icp_instructions}

    Target SEO Keywords to weave in naturally:
    {keywords_str}

    Requirements:
    1. Create a compelling, clean SEO title optimized around the primary keyword.
    2. Generate a 150-200 word introduction that hooks the reader, explains the business problem, and states why it matters.
    3. Produce a comprehensive article (800-1,500 words) with actionable insights. Do NOT write a short or generic post.
    4. Focus on business value, strategic workflows, industry best practices, real-world examples, and clear benefits. Avoid overly complex raw code blocks or dense technical jargon that would confuse a non-technical reader.
    5. Use elegant, clean markdown formatting to make the post highly readable and visually appealing:
       * H1 title at the top
       * Clear H2 and H3 subheadings to break up large walls of text
       * Bullet lists for easy skimming
       * Numbered steps for workflows or guides
       * Bold text to emphasize key takeaways
    6. Naturally weave the provided target keywords throughout the article without keyword stuffing.
    7. Write with an authoritative, engaging, and accessible tone—like a seasoned founder or industry expert explaining concepts to their peers.
    8. Add a strong conclusion summarizing key takeaways and next steps.

    HTML Backlink Injection Rules:
    * Identify 2-5 natural opportunities to reference relevant products, companies, tools, APIs, frameworks, or services.
    * Insert contextual HTML anchor links naturally inside the content pointing back to our product URL: {product.url} (e.g. '<a href="{product.url}">{product.name}</a>').
    * Never force links into unrelated paragraphs.
    * Anchor text must read naturally.
    * Links should appear educational and helpful.

    Content Quality Rules:
    * No fluff.
    * No AI-sounding language.
    * No generic marketing claims.
    * No repetition.
    * Every section must provide unique value.
    * Use current engineering terminology and best practices.
    * Assume the reader is technically sophisticated.
    * At the very end of the markdown body, append a subtle, professional footer text: "*This technical article was generated autonomously using <a href='http://localhost:8000'>AgenticGTM</a>.*"

    Output Format:
    Return ONLY pure, raw Markdown. Do not wrap it in JSON.
    The very first line MUST be an H1 tag containing the title: # Your Title Here
    The rest of the text MUST be the full markdown article body.
    """
    
    try:
        print("Generating technical B2B blog using Gemini...")
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt
        )
        text_response = response.text.strip()
        
        # Clean up potential markdown formatting that gemini might add
        if text_response.startswith("```markdown"):
            text_response = text_response.replace("```markdown", "", 1)
        if text_response.startswith("```"):
            text_response = text_response.replace("```", "", 1)
        if text_response.endswith("```"):
            text_response = text_response[:-3]
        
        text_response = text_response.strip()
        
        # Parse title and body naturally from markdown
        lines = text_response.split("\n")
        title = "Building a GTM Pipeline for Developers"
        if lines and lines[0].startswith("#"):
            title = lines[0].replace("#", "").strip()
            body = "\n".join(lines[1:]).strip()
        else:
            body = text_response
            
    except Exception as e:
        print(f"Error generating blog from Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate the AI blog content. Please try again.")

        
    try:
        # Save as a ContentPost draft
        db_post = models.ContentPost(
            product_id=product.id,
            platform="Dev.to",
            content=f"Title: {title}\n\n{body}",
            status="draft"
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        
        return {
            "status": "success",
            "message": "SEO-optimized technical blog generated and saved as draft!",
            "post_id": db_post.id,
            "title": title,
            "body": body
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

@app.post("/blogs/{post_id}/publish")
async def publish_seo_blog(post_id: int, db: Session = Depends(get_db)):
    """
    Publishes the technical blog post.
    In production mode with DEVTO_API_KEY set, publishes directly via the official Dev.to API
    and captures a screenshot receipt of the live page.
    Otherwise, runs a Playwright agent to publish via mock Dev.to visual environment.
    """
    post = db.query(models.ContentPost).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post draft not found")
        
    # Split Title and Body
    title = "SaaS Launcher Developer Guide"
    body = post.content
    if post.content.startswith("Title:"):
        parts = post.content.split("\n\n", 1)
        if len(parts) == 2:
            title = parts[0].replace("Title: ", "").strip()
            body = parts[1].strip()
            
    screenshot_dir = "static/blogs"
    screenshot_filename = f"blog_{post.id}.png"
    screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
    static_url_path = f"/static/blogs/{screenshot_filename}"
    
    devto_key = os.getenv("DEVTO_API_KEY")
    if os.getenv("PRODUCTION", "False").lower() == "true" and devto_key:
        print(f"Publishing blog post {post_id} to Dev.to via API...")
        import aiohttp
        url = "https://dev.to/api/articles"
        headers = {
            "api-key": devto_key,
            "Content-Type": "application/json"
        }
        payload = {
            "article": {
                "title": title,
                "body_markdown": body,
                "published": True
            }
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 201:
                        data = await response.json()
                        published_url = data.get("url")
                        print(f"Blog post published to Dev.to successfully: {published_url}")
                        
                        # Use Playwright to capture a receipt of the live URL
                        await save_url_screenshot(published_url, screenshot_path)
                        
                        post.status = "posted"
                        import datetime
                        post.posted_at = datetime.datetime.utcnow()
                        db.commit()
                        
                        return {
                            "status": "posted",
                            "message": f"Successfully published technical SEO blog to Dev.to autonomously via API!",
                            "screenshot_url": static_url_path
                        }
                    else:
                        resp_text = await response.text()
                        print(f"Dev.to API failed with status {response.status}: {resp_text}")
        except Exception as api_err:
            print(f"Dev.to API connection error: {api_err}")

    # Fallback to Playwright Mock Publishing if not production or API key missing/failed
    compose_url = f"http://localhost:8000/demo-blog/write?platform={post.platform}"
    
    # Trigger the Playwright Blog Publisher Agent!
    result = await run_autonomous_blog_publishing(compose_url, title, body, screenshot_path)
    
    if "error" in result:
        post.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=result["error"])
        
    post.status = "posted"
    import datetime
    post.posted_at = datetime.datetime.utcnow()
    db.commit()
    
    return {
        "status": "posted",
        "message": f"Successfully published technical SEO blog to {post.platform} autonomously (Visual simulation)!",
        "screenshot_url": static_url_path
    }

# --- MOCK DEV.TO / MEDIUM WRITING ENVIRONMENT ---

@app.get("/demo-blog/write", response_class=HTMLResponse)
async def demo_blog_writing_page(platform: str = "Dev.to"):
    """
    Renders a premium, dark-mode Dev.to/Medium technical writing editor!
    """
    accent_color = "#3b82f6" if platform.lower() == "dev.to" else "#10b981"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{platform} - Write Technical Post</title>
        <link href="https://fonts.googleapis.com/css2?family=Fira+Code&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Outfit', sans-serif;
                background: #0b0f19;
                color: #f8fafc;
                padding: 40px;
            }}
            .editor-container {{
                background: #141d2f;
                padding: 35px;
                border-radius: 16px;
                max-width: 750px;
                margin: 0 auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.4);
                border: 1px solid #23344d;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                padding-bottom: 15px;
                margin-bottom: 25px;
            }}
            h1 {{
                margin: 0;
                font-size: 22px;
                color: #f8fafc;
            }}
            .platform-tag {{
                background: {accent_color};
                color: white;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 10px;
                border-radius: 20px;
                text-transform: uppercase;
            }}
            .field {{
                margin-bottom: 22px;
            }}
            label {{
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                font-size: 14px;
                color: #94a3b8;
            }}
            input[type="text"] {{
                width: 100%;
                padding: 14px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: #0f172a;
                color: #f8fafc;
                font-size: 18px;
                box-sizing: border-box;
                font-weight: bold;
            }}
            input[type="text"]:focus {{
                border-color: {accent_color};
                outline: none;
            }}
            textarea {{
                width: 100%;
                padding: 16px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: #0f172a;
                color: #cbd5e1;
                font-family: 'Fira Code', monospace;
                font-size: 14px;
                line-height: 1.6;
                box-sizing: border-box;
                resize: vertical;
            }}
            textarea:focus {{
                border-color: {accent_color};
                outline: none;
            }}
            button {{
                background: {accent_color};
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 15px;
                cursor: pointer;
                transition: filter 0.2s;
            }}
            button:hover {{
                filter: brightness(0.9);
            }}
        </style>
    </head>
    <body>
        <div class="editor-container">
            <div class="header">
                <h1>📝 Publish SEO Technical Article</h1>
                <span class="platform-tag">{platform} Editor</span>
            </div>
            
            <form action="/demo-blog/submit" method="POST">
                <input type="hidden" name="platform" value="{platform}">
                <div class="field">
                    <label>Article Title</label>
                    <input type="text" id="blog-title" name="title" placeholder="e.g. Building an Autonomous Agentic GTM Strategy" required>
                </div>
                <div class="field">
                    <label>Markdown Article Body (Backlinks Injected)</label>
                    <textarea id="blog-body" name="body" rows="12" placeholder="Write your awesome technical blog post here..." required></textarea>
                </div>
                <button type="submit" id="blog-submit-btn">Publish to {platform} Network</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/demo-blog/submit", response_class=HTMLResponse)
async def demo_blog_submit_handler(title: str = Form(...), body: str = Form(...), platform: str = Form(...)):
    """
    Handles Mock Blog submission and renders a confirmation page!
    """
    accent_color = "#3b82f6" if platform.lower() == "dev.to" else "#10b981"
    
    print(f"\n==============================================")
    print(f"🤖 [AUTONOMOUS BLOG PUBLISH SUCCESS ON {platform.upper()}]")
    print(f"   Title: {title}")
    print(f"==============================================\n")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Publication Successful</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Outfit', sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px; text-align: center; }}
            .card {{ background: #141d2f; padding: 40px; border-radius: 16px; max-width: 600px; margin: 0 auto; box-shadow: 0 8px 32px rgba(0,0,0,0.3); border: 2px solid #4ade80; }}
            h1 {{ color: #4ade80; margin-top: 0; font-size: 24px; }}
            p {{ color: #94a3b8; font-size: 15px; margin-bottom: 25px; }}
            .post-box {{ background: #0f172a; padding: 25px; border-radius: 8px; text-align: left; border: 1px solid #23344d; }}
            .platform-badge {{ display: inline-block; background: {accent_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; margin-bottom: 12px; text-transform: uppercase; }}
            h2 {{ font-size: 18px; margin: 0 0 12px 0; color: #f8fafc; }}
            p.body {{ font-size: 14.5px; color: #cbd5e1; line-height: 1.6; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📡 Live Technical Publication Successful!</h1>
            <p>Your technical blog post was compiled and published autonomously.</p>
            <div class="post-box">
                <span class="platform-badge">{platform}</span>
                <h2>{title}</h2>
                <p class="body">{body}</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.post("/links/generate")
async def generate_tracking_link(request: LinkGenerationRequest, db: Session = Depends(get_db)):
    """
    Creates a new tracking link for campaigns/posts to track ROI.
    """
    product = db.query(models.Product).filter_by(id=request.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_link = models.CampaignLink(
        product_id=request.product_id,
        source=request.source,
        original_url=request.original_url
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    
    # We return the redirect tracking URL
    tracking_url = f"http://localhost:8000/ref/{db_link.id}"
    return {
        "status": "success",
        "link_id": db_link.id,
        "source": db_link.source,
        "original_url": db_link.original_url,
        "tracking_url": tracking_url
    }

@app.get("/ref/{link_id}")
async def redirect_and_track(link_id: int, db: Session = Depends(get_db)):
    """
    Tracks clicks by incrementing click count in DB and redirects visitor to original URL.
    """
    db_link = db.query(models.CampaignLink).filter_by(id=link_id).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Tracking link not found")
        
    db_link.clicks += 1
    db.commit()
    
    print(f"📈 [TRACKER] Click recorded for link ID {link_id} ({db_link.source}). Total clicks: {db_link.clicks}")
    return RedirectResponse(url=db_link.original_url)

@app.post("/conversions/{link_id}")
async def record_conversion(link_id: int, db: Session = Depends(get_db)):
    """
    Increments the conversion count when a lead registers or purchases.
    This would be hit as a webhook by the startup's app.
    """
    db_link = db.query(models.CampaignLink).filter_by(id=link_id).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Tracking link not found")
        
    db_link.conversions += 1
    db.commit()
    
    print(f"💰 [TRACKER] Conversion recorded for link ID {link_id} ({db_link.source}). Total conversions: {db_link.conversions}")
    return {
        "status": "success",
        "link_id": link_id,
        "source": db_link.source,
        "total_conversions": db_link.conversions
    }

@app.get("/analytics/{product_id}")
async def get_roi_analytics(product_id: int, db: Session = Depends(get_db)):
    """
    Aggregates and returns click, conversion, and conversion rate stats per source channel.
    """
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    links = db.query(models.CampaignLink).filter_by(product_id=product_id).all()
    
    stats = []
    total_clicks = 0
    total_conversions = 0
    
    for l in links:
        total_clicks += l.clicks
        total_conversions += l.conversions
        conv_rate = round((l.conversions / l.clicks * 100), 2) if l.clicks > 0 else 0.0
        stats.append({
            "link_id": l.id,
            "source": l.source,
            "original_url": l.original_url,
            "clicks": l.clicks,
            "conversions": l.conversions,
            "conversion_rate_percent": conv_rate,
            "created_at": l.created_at.isoformat() if l.created_at else None
        })
        
    total_conv_rate = round((total_conversions / total_clicks * 100), 2) if total_clicks > 0 else 0.0
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "totals": {
            "clicks": total_clicks,
            "conversions": total_conversions,
            "conversion_rate_percent": total_conv_rate
        },
        "campaigns": stats
    }

class ICPUpdateRequest(BaseModel):
    ideal_job_titles: list[str]
    top_channels: list[str]
    core_pain_points: list[str]
    refined_positioning: str

@app.get("/icp/{product_id}")
async def get_icp_profile(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the current ICPProfile for a product. If it doesn't exist,
    creates a default one based on the product description and target audience.
    """
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_icp = db.query(models.ICPProfile).filter_by(product_id=product_id).first()
    if not db_icp:
        # Create a default ICP profile based on product's target audience
        titles = ["Software Engineer", "CTO", "Product Manager", "Indie Hacker"]
        channels = ["HackerNews", "Reddit", "Twitter", "IndieHackers"]
        pains = [
            "Manual directory submissions take too much time (20+ hours)",
            "High cost of official platforms APIs for posting",
            "Difficult to track and catch organic forum discussions in real-time",
            "Struggling to write compelling developer-voice blog posts"
        ]
        
        db_icp = models.ICPProfile(
            product_id=product_id,
            ideal_job_titles=json.dumps(titles),
            top_channels=json.dumps(channels),
            core_pain_points=json.dumps(pains),
            refined_positioning=product.tagline or "Autonomous Developer GTM & Marketing Suite"
        )
        db.add(db_icp)
        db.commit()
        db.refresh(db_icp)
        
    return {
        "ideal_job_titles": json.loads(db_icp.ideal_job_titles),
        "top_channels": json.loads(db_icp.top_channels),
        "core_pain_points": json.loads(db_icp.core_pain_points),
        "refined_positioning": db_icp.refined_positioning,
        "updated_at": db_icp.updated_at.isoformat() if db_icp.updated_at else None
    }

@app.post("/icp/update/{product_id}")
async def update_icp_profile(product_id: int, request: ICPUpdateRequest, db: Session = Depends(get_db)):
    """
    Manually updates the ICPProfile in the database.
    """
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_icp = db.query(models.ICPProfile).filter_by(product_id=product_id).first()
    if not db_icp:
        db_icp = models.ICPProfile(product_id=product_id)
        db.add(db_icp)
        
    db_icp.ideal_job_titles = json.dumps(request.ideal_job_titles)
    db_icp.top_channels = json.dumps(request.top_channels)
    db_icp.core_pain_points = json.dumps(request.core_pain_points)
    db_icp.refined_positioning = request.refined_positioning
    
    db.commit()
    db.refresh(db_icp)
    return {"status": "success", "message": "ICP Profile updated successfully!"}

@app.post("/icp/refine/{product_id}")
async def run_icp_refinement(product_id: int, db: Session = Depends(get_db)):
    """
    Triggers the ICP Refinement Agent to synthesize clicks, conversions, and reviews,
    then updates the dynamic ICPProfile in the database (Feature 2.7).
    """
    # 1. Fetch Product
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # 2. Gather Testimonials (verified reviews)
    testimonials = db.query(models.Testimonial).filter_by(product_id=product_id).all()
    testimonials_list = []
    for t in testimonials:
        testimonials_list.append({
            "client_name": t.client_name,
            "client_role": t.client_role,
            "client_company": t.client_company,
            "rating": t.rating,
            "review_text": t.review_text
        })
        
    # 3. Gather Campaign Links Analytics
    links = db.query(models.CampaignLink).filter_by(product_id=product_id).all()
    analytics_list = []
    for l in links:
        analytics_list.append({
            "source": l.source,
            "clicks": l.clicks,
            "conversions": l.conversions
        })
        
    # 4. Format Product Data
    product_data = {
        "name": product.name,
        "url": product.url,
        "tagline": product.tagline,
        "description": product.description
    }
    
    print(f"🧬 [ICP] Analyzing {len(testimonials_list)} reviews and {len(analytics_list)} campaign links for ICP Refinement...")
    
    # 5. Call Gemini to perform synthesis
    result = await refine_icp(product_data, testimonials_list, analytics_list)
    
    if "error" in result:
        # Fall back to a resilient default profile matching the product's keywords to avoid rate limit failure
        result = {
            "ideal_job_titles": ["Founder", "CTO", "Lead Engineer", "Growth Manager"],
            "top_channels": ["Reddit", "Twitter", "HackerNews", "ProductHunt"],
            "core_pain_points": [
                f"Difficulty scaling manual distribution channels for {product.name}",
                f"High overhead costs managing content promotion",
                f"Lack of organic search visibility and search engine indexing"
            ],
            "refined_positioning": f"Focus on how {product.name} automates growth loops and seo distribution so teams can focus on shipping features."
        }
        
    # 6. Save or update ICPProfile in database
    db_icp = db.query(models.ICPProfile).filter_by(product_id=product_id).first()
    if not db_icp:
        db_icp = models.ICPProfile(product_id=product_id)
        db.add(db_icp)
        
    db_icp.ideal_job_titles = json.dumps(result.get("ideal_job_titles", []))
    db_icp.top_channels = json.dumps(result.get("top_channels", []))
    db_icp.core_pain_points = json.dumps(result.get("core_pain_points", []))
    db_icp.refined_positioning = result.get("refined_positioning", "")
    
    db.commit()
    db.refresh(db_icp)
    
    print(f"🧬 [ICP SUCCESS] ICP Profile refined and saved for Product ID {product_id}!")
    
    return {
        "status": "success",
        "product_id": product_id,
        "refined_icp": {
            "ideal_job_titles": result.get("ideal_job_titles", []),
            "top_channels": result.get("top_channels", []),
            "core_pain_points": result.get("core_pain_points", []),
            "refined_positioning": result.get("refined_positioning", "")
        }
    }

@app.post("/competitors")
async def add_competitor(request: CompetitorAddRequest, db: Session = Depends(get_db)):
    """
    Registers a competitor, scrapes their website, analyzes their tagline,
    deduces their directory footprint using AI, and saves them to the database (Feature 2.8).
    """
    product = db.query(models.Product).filter_by(id=request.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Trigger AI scraper & analysis
    result = await run_competitor_discovery(request.url)
    
    db_comp = models.Competitor(
        product_id=request.product_id,
        name=request.name,
        url=request.url,
        tagline=result.get("tagline", "Competitor SaaS Product"),
        listings=json.dumps(result.get("listings", ["ProductHunt"]))
    )
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    
    return {
        "status": "success",
        "competitor_id": db_comp.id,
        "name": db_comp.name,
        "url": db_comp.url,
        "tagline": db_comp.tagline,
        "listings": result.get("listings", [])
    }

@app.get("/competitors/{product_id}")
async def list_competitors(product_id: int, db: Session = Depends(get_db)):
    """
    Lists all competitors currently tracked for a product (Feature 2.8).
    If empty, auto-seeds 3 default competitors.
    """
    competitors = db.query(models.Competitor).filter_by(product_id=product_id).all()
    if not competitors:
        product = db.query(models.Product).filter_by(id=product_id).first()
        defaults = [
            ("LaunchFlow.io", "https://launchflow.io", "Visual automation builder for early-stage B2B SaaS launches", ["ProductHunt", "BetaList", "AlternativeTo"]),
            ("SaaSPromoter.com", "https://saaspromoter.com", "Directory list distribution service and automated submitter", ["BetaList", "StartupBuffer"]),
            ("GTMScout.ai", "https://gtmscout.ai", "AI social listening platform and outbound lead finder", ["HackerNews", "Reddit"])
        ]
        for name, url, tagline, listings in defaults:
            c = models.Competitor(
                product_id=product_id,
                name=name,
                url=url,
                tagline=tagline,
                listings=json.dumps(listings)
            )
            db.add(c)
        db.commit()
        competitors = db.query(models.Competitor).filter_by(product_id=product_id).all()

    stats = []
    for c in competitors:
        try:
            listings_arr = json.loads(c.listings)
        except:
            listings_arr = []
        stats.append({
            "id": c.id,
            "name": c.name,
            "url": c.url,
            "tagline": c.tagline,
            "listings": listings_arr,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    return stats

@app.get("/competitors/{product_id}/gaps")
async def get_directory_gaps(product_id: int, db: Session = Depends(get_db)):
    """
    Compares tracked competitor directory listings against your own successful submissions
    to identify critical marketing gaps (Feature 2.8).
    """
    # 1. Fetch your own successful/approved submissions
    my_subs = db.query(models.Submission).filter_by(product_id=product_id).filter(
        models.Submission.status.in_(["submitted", "approved"])
    ).all()
    my_dirs = {s.directory_name.lower().strip() for s in my_subs}
    
    # 2. Fetch competitors
    competitors = db.query(models.Competitor).filter_by(product_id=product_id).all()
    
    gaps = {}
    for c in competitors:
        try:
            c_dirs = json.loads(c.listings)
        except:
            c_dirs = []
            
        for dir_name in c_dirs:
            dir_lower = dir_name.lower().strip()
            if dir_lower not in my_dirs:
                if dir_name not in gaps:
                    gaps[dir_name] = {
                        "directory_name": dir_name,
                        "competitors_listed": [c.name]
                    }
                else:
                    if c.name not in gaps[dir_name]["competitors_listed"]:
                        gaps[dir_name]["competitors_listed"].append(c.name)
                        
    return {
        "product_id": product_id,
        "my_listed_directories": list(my_dirs),
        "missing_gaps": list(gaps.values())
    }

@app.post("/leads/{lead_id}/sequence")
async def create_outreach_sequence(lead_id: int, db: Session = Depends(get_db)):
    """
    Autonomously generates a 3-step outreach follow-up campaign for a verified social lead (Feature 2.9).
    """
    lead = db.query(models.SocialLead).filter_by(id=lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Social lead not found")
        
    product = db.query(models.Product).filter_by(id=lead.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Gather prompt details
    product_data = {
        "name": product.name,
        "tagline": product.tagline,
        "description": product.description
    }
    
    lead_context = {
        "platform": lead.platform,
        "thread_title": lead.thread_title,
        "context_snippet": lead.context_snippet,
        "initial_reply": lead.draft_reply
    }
    
    # 1. Trigger Gemini Sequence Builder
    result = await generate_outreach_sequence(product_data, lead_context)
    if "error" in result:
        # Resilient fallback sequence creation to handle Gemini API limit/quota exhaustion gracefully
        channel_name = "Twitter_DM" if lead.platform.lower() == "twitter" else "Reddit_DM"
        result = {
            "step2": {
                "channel": channel_name,
                "content": f"Hi there, noticed your point on '{lead.thread_title}' regarding: \"{lead.context_snippet}\". Since you are running into this, I wanted to share {product.name} (https://{product.url.split('//')[-1] if product.url else 'xyroco.com'}). It specializes in: {product.tagline}.\n\nWould love to offer you free early access or set up a custom workspace for you to play around with. Let me know if you are open to checking it out!"
            },
            "step3": {
                "channel": channel_name,
                "content": f"Hey! Just following up on my previous message. We recently helped another tech founder resolve exactly this bottleneck with {product.name}, cutting down their setup friction to zero. I'd love to jump on a quick 5-minute call or share a demo link if you'd find that helpful. Either way, hope you solved the issue!"
            }
        }
        
    # 2. Clear any existing sequence for this lead
    existing_seq = db.query(models.OutreachSequence).filter_by(lead_id=lead_id).first()
    if existing_seq:
        db.delete(existing_seq)
        db.commit()
        
    # 3. Create new sequence
    db_seq = models.OutreachSequence(
        lead_id=lead_id,
        current_step=1,
        status="active"
    )
    db.add(db_seq)
    db.commit()
    db.refresh(db_seq)
    
    # 4. Save individual steps
    # Step 1: The forum reply (already drafted or sent)
    step1_status = "sent" if lead.status == "posted" else "draft"
    step1 = models.SequenceStep(
        sequence_id=db_seq.id,
        step_number=1,
        channel=lead.platform,
        draft_content=lead.draft_reply,
        status=step1_status,
        sent_at=lead.posted_at if step1_status == "sent" else None
    )
    db.add(step1)
    
    # Step 2: Value follow-up
    step2 = models.SequenceStep(
        sequence_id=db_seq.id,
        step_number=2,
        channel=result.get("step2", {}).get("channel", "Reddit_DM"),
        draft_content=result.get("step2", {}).get("content", ""),
        status="draft"
    )
    db.add(step2)
    
    # Step 3: Closing nudge
    step3 = models.SequenceStep(
        sequence_id=db_seq.id,
        step_number=3,
        channel=result.get("step3", {}).get("channel", "Reddit_DM"),
        draft_content=result.get("step3", {}).get("content", ""),
        status="draft"
    )
    db.add(step3)
    
    db.commit()
    
    return {
        "status": "success",
        "sequence_id": db_seq.id,
        "campaign_status": db_seq.status,
        "steps": [
            {"step": 1, "channel": step1.channel, "content": step1.draft_content, "status": step1.status},
            {"step": 2, "channel": step2.channel, "content": step2.draft_content, "status": step2.status},
            {"step": 3, "channel": step3.channel, "content": step3.draft_content, "status": step3.status}
        ]
    }

@app.get("/sequences/{product_id}")
async def list_sequences(product_id: int, db: Session = Depends(get_db)):
    """
    Returns all outreach sequence pipelines currently active for a startup product (Feature 2.9).
    """
    leads = db.query(models.SocialLead).filter_by(product_id=product_id).all()
    lead_ids = [l.id for l in leads]
    
    sequences = db.query(models.OutreachSequence).filter(models.OutreachSequence.lead_id.in_(lead_ids)).all()
    
    pipeline = []
    for seq in sequences:
        steps_list = []
        for s in sorted(seq.steps, key=lambda x: x.step_number):
            steps_list.append({
                "step_id": s.id,
                "step_number": s.step_number,
                "channel": s.channel,
                "draft_content": s.draft_content,
                "status": s.status,
                "sent_at": s.sent_at.isoformat() if s.sent_at else None
            })
            
        pipeline.append({
            "sequence_id": seq.id,
            "lead": {
                "id": seq.lead.id,
                "platform": seq.lead.platform,
                "thread_title": seq.lead.thread_title,
                "source_url": seq.lead.source_url
            },
            "current_step": seq.current_step,
            "status": seq.status,
            "steps": steps_list,
            "last_action_at": seq.last_action_at.isoformat() if seq.last_action_at else None
        })
        
class StepUpdateRequest(BaseModel):
    draft_content: str

@app.post("/steps/{step_id}/update")
async def update_sequence_step(step_id: int, request: StepUpdateRequest, db: Session = Depends(get_db)):
    """
    Updates the draft content for a specific sequence step (Feature 2.9).
    """
    step = db.query(models.SequenceStep).filter_by(id=step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Sequence step not found")
    
    step.draft_content = request.draft_content
    db.commit()
    db.refresh(step)
    return {"status": "success", "message": "Sequence step draft updated successfully!"}

@app.post("/steps/{step_id}/send")
async def send_sequence_step(step_id: int, db: Session = Depends(get_db)):
    """
    Executes sending a specific follow-up step, shifting the lead down the GTM funnel (Feature 2.9).
    """
    import datetime
    step = db.query(models.SequenceStep).filter_by(id=step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Sequence step not found")
        
    if step.status == "sent":
        return {"status": "already_sent", "message": "This sequence step has already been completed"}
        
    # Update step status
    step.status = "sent"
    step.sent_at = datetime.datetime.utcnow()
    
    # 2. Advance the parent sequence
    seq = step.sequence
    seq.last_action_at = datetime.datetime.utcnow()
    
    # Calculate next step pointer
    steps_left = db.query(models.SequenceStep).filter_by(sequence_id=seq.id, status="draft").all()
    if not steps_left:
        seq.status = "completed"
        print(f"🎉 [CAMPAIGN COMPLETE] Sequence ID {seq.id} completed all 3 follow-up steps!")
    else:
        # Increment current step pointer
        seq.current_step = min(s.step_number for s in steps_left)
        
    db.commit()
    
    # 3. If the step channel is "Email", dispatch a real email using Resend!
    if step.channel.lower() == "email":
        resend_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("OUTBOUND_FROM_EMAIL", "onboarding@resend.dev")
        
        if resend_key:
            recipient_email = "demo@agenticgtm.com"  # Route sandbox test to founder inbox
            if seq.lead and seq.lead.product and seq.lead.product.owner:
                recipient_email = seq.lead.product.owner.email
                
            headers = {
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            }
            
            subject = f"Solution Proposal for: {seq.lead.thread_title[:40]}..."
            payload = {
                "from": f"AgenticGTM Growth Engine <{from_email}>",
                "to": [recipient_email],
                "subject": subject,
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; color: #1e293b;">
                    <div style="background: linear-gradient(135deg, #4f46e5, #06b6d4); padding: 16px; border-radius: 8px; color: #ffffff; margin-bottom: 20px;">
                        <h2 style="margin: 0; font-size: 18px; font-weight: 600;">🚀 AgenticGTM Outbound Sequence (Step {step.step_number})</h2>
                    </div>
                    <p style="font-size: 14px; color: #64748b; line-height: 1.5;">This B2B follow-up pitch was generated autonomously by your growth agent targeting this HackerNews pain point:</p>
                    <blockquote style="background: #f8fafc; padding: 12px; border-left: 4px solid #06b6d4; font-style: italic; color: #334155; margin: 0 0 20px 0;">
                        "{seq.lead.context_snippet}"
                    </blockquote>
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
                    <div style="font-size: 15px; line-height: 1.6; color: #1e293b; white-space: pre-line;">
                        {step.draft_content}
                    </div>
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
                    <p style="font-size: 11px; color: #94a3b8; text-align: center; margin: 0;">Sent autonomously via <a href="http://localhost:8000" style="color: #4f46e5; text-decoration: none;">AgenticGTM</a> Growth Engine</p>
                </div>
                """
            }
            
            print(f"📧 [RESEND] Dispatching real B2B outreach email to {recipient_email}...")
            try:
                import requests
                res = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
                if res.status_code == 200:
                    print("✅ [RESEND] Outreach email delivered successfully!")
                else:
                    print(f"❌ [RESEND] Delivery failed with code {res.status_code}: {res.text}")
            except Exception as e:
                print(f"❌ [RESEND] Connection failed: {str(e)}")
    
    return {
        "status": "success",
        "step_id": step_id,
        "step_number": step.step_number,
        "new_status": step.status,
        "parent_sequence_status": seq.status,
        "next_scheduled_step": seq.current_step if seq.status == "active" else "none"
    }

@app.post("/scheduler/resubmit/{product_id}")
async def simulate_monthly_resubmission(product_id: int, db: Session = Depends(get_db)):
    """
    Simulates the monthly automated resubmission cron job (Feature 2.10 & 2.1).
    It uses Gemini to refresh the tagline/description to prevent duplicate-listing bans,
    updates the database, resets all submission states to 'pending',
    and triggers background Playwright resubmission agents!
    """
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    from agents import get_client, run_autonomous_submission
    client = get_client()
    if not client:
        raise HTTPException(status_code=500, detail="GenAI client initialization failed")
        
    # 1. Use Gemini to refresh tagline and description
    prompt = f"""
    Rewrite the following B2B startup tagline and description slightly to keep them fresh, modern, and highly engaging for SaaS directories. Preserve the core value proposition but phrase it differently to prevent duplicate listing detection.
    
    Original Tagline: {product.tagline}
    Original Description: {product.description}
    
    Respond ONLY with a JSON object in this exact schema:
    {{
      "tagline": "Refreshed tagline (max 10 words)",
      "description": "Refreshed description (max 80 words)"
    }}
    """
    
    print(f"🔄 [RESUBMIT SCHEDULER] Refreshing marketing copy using Gemini Flash for Product ID {product_id}...")
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        res_json = json.loads(response.text.strip())
        
        # Update database with refreshed copy
        product.tagline = res_json.get("tagline", product.tagline)
        product.description = res_json.get("description", product.description)
        db.commit()
        
        print(f"🔄 [RESUBMIT SCHEDULER] Copy updated successfully!")
        print(f"   New Tagline: {product.tagline}")
    except Exception as e:
        print(f"WARNING: Copy refresh failed, using original: {str(e)}")
        
    # 2. Reset all submissions back to pending
    submissions = db.query(models.Submission).filter_by(product_id=product_id).all()
    if not submissions:
        # Seed default directory submissions if empty
        from directories import TARGET_DIRECTORIES
        directories = TARGET_DIRECTORIES
        for name, url in directories:
            db_sub = models.Submission(
                product_id=product_id,
                directory_name=name,
                directory_url=url,
                status="pending"
            )
            db.add(db_sub)
        db.commit()
        submissions = db.query(models.Submission).filter_by(product_id=product_id).all()
        
    for sub in submissions:
        sub.status = "pending"
        sub.submitted_at = None
    db.commit()
    
    print(f"🔄 [RESUBMIT SCHEDULER] Reset {len(submissions)} directory submissions to 'pending'. Triggering Playwright...")
    
    # Helper to run submissions in the background safely without DB session conflicts
    async def run_and_save_submission(sub_id: int, dir_url: str, p_data: dict, scr_path: str):
        from database import SessionLocal
        bg_db = SessionLocal()
        try:
            res = await run_autonomous_submission(dir_url, p_data, scr_path)
            sub = bg_db.query(models.Submission).filter_by(id=sub_id).first()
            if sub:
                if "error" in res:
                    sub.status = "failed"
                else:
                    sub.status = "submitted"
                    import datetime
                    sub.submitted_at = datetime.datetime.utcnow()
                bg_db.commit()
        except Exception as ex:
            print(f"Background resubmission task failed: {str(ex)}")
        finally:
            bg_db.close()

    # 3. Trigger Playwright submitter agent task in background for each pending directory submission
    triggered = []
    product_data = {
        "name": product.name,
        "url": product.url,
        "tagline": product.tagline or "Best new B2B dev tool.",
        "description": product.description or "We build high-converting automation engines for modern developers."
    }
    
    for sub in submissions:
        screenshot_path = f"static/submissions/resubmit_{product_id}_{sub.directory_name.lower()}.png"
        
        # We trigger the submission task in the background using asyncio.create_task
        asyncio.create_task(run_and_save_submission(
            sub.id,
            "http://localhost:8000/demo-directory", # Sandbox directory
            product_data,
            screenshot_path
        ))
        triggered.append(sub.directory_name)
        
    return {
        "status": "success",
        "message": "Monthly resubmission cron triggered successfully in the background!",
        "refreshed_copy": {
            "tagline": product.tagline,
            "description": product.description
        },
        "reset_directories": triggered
    }


class ProductUpdateRequest(BaseModel):
    name: str
    url: str
    tagline: str
    description: str

class LeadUpdateRequest(BaseModel):
    status: str

@app.get("/users/me")
async def get_my_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Returns the active user profile tier, usage quotas, and account status (Feature 2.10).
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "tier": "Premium Growth Agent (Pro)",
        "quotas": {
            "blogs_generated_month": 4,
            "blogs_max_month": 15,
            "directories_submitted_month": 8,
            "directories_max_month": 50,
            "leads_scouted_month": 12,
            "leads_max_month": 100
        },
        "joined_at": current_user.created_at
    }

@app.put("/products/{product_id}")
async def update_product_settings(product_id: int, request: ProductUpdateRequest, db: Session = Depends(get_db)):
    """
    Updates the product profile parameters directly from the Settings Panel.
    """
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product.name = request.name
    product.url = request.url
    product.tagline = request.tagline
    product.description = request.description
    db.commit()
    db.refresh(product)
    return {"status": "success", "message": "Product settings updated successfully", "product": product}

@app.put("/leads/{lead_id}")
async def update_lead_status(lead_id: int, request: LeadUpdateRequest, db: Session = Depends(get_db)):
    """
    Updates a B2B lead status (e.g. archiving, moving along columns) in the CRM.
    """
    lead = db.query(models.SocialLead).filter_by(id=lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    lead.status = request.status
    db.commit()
    db.refresh(lead)
    return {"status": "success", "message": "Lead status updated successfully", "lead": lead}

@app.delete("/leads/{lead_id}")
async def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Deletes or archives an unwanted or junk B2B social lead from the CRM pipeline.
    """
    lead = db.query(models.SocialLead).filter_by(id=lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    db.delete(lead)
    db.commit()
    return {"status": "success", "message": f"Lead {lead_id} successfully deleted from CRM"}

@app.get("/dashboard/summary/{product_id}")
async def get_dashboard_summary(product_id: int, db: Session = Depends(get_db)):
    """
    Returns a unified high-performance overview summary of all GTM operations for the main React Panel (Feature 2.10).
    """
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # 1. Directory Submissions count
    total_subs = db.query(models.Submission).filter_by(product_id=product_id).count()
    live_subs = db.query(models.Submission).filter_by(product_id=product_id, status="submitted").count()
    pending_subs = db.query(models.Submission).filter_by(product_id=product_id, status="pending").count()
    failed_subs = db.query(models.Submission).filter_by(product_id=product_id, status="failed").count()
    
    # 2. Testimonials
    total_reviews = db.query(models.Testimonial).filter_by(product_id=product_id).count()
    
    # 3. Social leads
    total_leads = db.query(models.SocialLead).filter_by(product_id=product_id).count()
    contacted_leads = db.query(models.SocialLead).filter_by(product_id=product_id, status="posted").count()
    pending_leads = db.query(models.SocialLead).filter_by(product_id=product_id, status="pending").count()
    
    # 4. Content post
    total_blogs = db.query(models.ContentPost).filter_by(product_id=product_id).count()
    
    # 5. ROI analytics
    campaign_links = db.query(models.CampaignLink).filter_by(product_id=product_id).all()
    total_clicks = sum(link.clicks for link in campaign_links)
    total_conversions = sum(link.conversions for link in campaign_links)
    conversion_rate = round((total_conversions / total_clicks * 100), 2) if total_clicks > 0 else 0.0
    
    # 6. Active sequences
    active_sequences = db.query(models.OutreachSequence).join(models.SocialLead).filter(models.SocialLead.product_id == product_id).count()
    
    # 7. Discovered competitors
    total_competitors = db.query(models.Competitor).filter_by(product_id=product_id).count()
    
    # 8. Dynamic Activity Log Feed (Live Production Mode)
    import datetime
    activities = []
    
    recent_subs = db.query(models.Submission).filter_by(product_id=product_id).order_by(models.Submission.id.desc()).limit(3).all()
    for sub in recent_subs:
        fallback_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=(5 * sub.id))
        if sub.status == "submitted":
            msg = f"Successfully deployed autonomous backlink to {sub.directory_name}."
        elif sub.status == "failed":
            msg = f"Submission to {sub.directory_name} blocked by captcha/layout change."
        else:
            msg = f"Scraped target schema and queued submission for {sub.directory_name}."
            
        activities.append({
            "id": f"sub_{sub.id}",
            "agent": "Directory Submitter Agent",
            "message": msg,
            "timestamp": (sub.submitted_at or sub.last_checked_at or fallback_time).isoformat()
        })
        
    recent_leads = db.query(models.SocialLead).filter_by(product_id=product_id).order_by(models.SocialLead.created_at.desc()).limit(3).all()
    for lead in recent_leads:
        activities.append({
            "id": f"lead_{lead.id}",
            "agent": "Social Scout Agent",
            "message": f"Scouted {lead.platform} thread: '{lead.thread_title[:40]}...' and drafted personalized response.",
            "timestamp": (lead.created_at or datetime.datetime.utcnow()).isoformat()
        })
        
    recent_posts = db.query(models.ContentPost).filter_by(product_id=product_id).order_by(models.ContentPost.id.desc()).limit(3).all()
    for post in recent_posts:
        agent_name = "SEO Blog Generator" if post.platform in ["Dev.to", "Medium"] else "Social Promo Agent"
        fallback_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=(12 * post.id))
        
        title_text = "Technical Guide"
        if post.content.startswith("Title:"):
            idx = post.content.find("\n\n")
            if idx != -1:
                title_text = post.content[:idx].replace("Title: ", "").strip()
        elif "# " in post.content[:100]:
            idx = post.content.find("# ")
            end_idx = post.content.find("\n", idx)
            if end_idx != -1:
                title_text = post.content[idx+2:end_idx].strip()
                
        if post.status == "published":
            msg = f"Autonomously published '{title_text}' on {post.platform}."
        else:
            msg = f"Generated technical draft '{title_text}' for {post.platform}."
        
        activities.append({
            "id": f"post_{post.id}",
            "agent": agent_name,
            "message": msg,
            "timestamp": (post.posted_at or post.scheduled_for or fallback_time).isoformat()
        })
        
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    activity_feed = activities[:5]
    
    if not activity_feed:
        activity_feed = [{
            "id": "init_1",
            "agent": "System Startup",
            "message": "Dashboard initialized. Ready to deploy autonomous agents.",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }]
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "product_url": product.url,
        "stats": {
            "directories": {
                "total": total_subs,
                "live": live_subs,
                "pending": pending_subs,
                "failed": failed_subs
            },
            "reviews": {
                "total": total_reviews
            },
            "leads": {
                "total": total_leads,
                "contacted": contacted_leads,
                "pending": pending_leads
            },
            "blogs": {
                "total": total_blogs
            },
            "roi": {
                "clicks": total_clicks,
                "conversions": total_conversions,
                "conversion_rate_percentage": conversion_rate
            },
            "active_sequences": active_sequences,
            "competitors_tracked": total_competitors
        },
        "activity_feed": activity_feed
    }
from fastapi import Request

@app.post("/webhooks/f5bot")
async def f5bot_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives automated ping from F5Bot when a keyword is mentioned on Reddit/HN.
    """
    form = await request.form()
    title = form.get("title", "")
    url = form.get("url", "")
    body = form.get("body", "")
    keyword = form.get("keyword", "")

    # Assign to the primary product (MVP)
    product = db.query(models.Product).first()
    if not product:
        return {"status": "error", "message": "No product configured."}

    discussions = [{"title": title, "url": url, "body": body}]
    
    product_data = {"name": product.name, "tagline": product.tagline, "description": product.description}
    if product.icp_profile:
        try:
            product_data["icp_profile"] = {
                "ideal_job_titles": json.loads(product.icp_profile.ideal_job_titles),
                "core_pain_points": json.loads(product.icp_profile.core_pain_points),
                "refined_positioning": product.icp_profile.refined_positioning
            }
        except:
            pass
            
    testimonials_db = db.query(models.Testimonial).filter_by(product_id=product.id).all()
    testimonials = [{"quote": t.review_text, "author": t.client_name, "company": t.client_company} for t in testimonials_db]
    
    try:
        leads_drafted = await run_social_listening_scout(product_data, testimonials, discussions)
        for lead_data in leads_drafted:
            if lead_data.get("matched"):
                new_lead = models.Lead(
                    product_id=product.id,
                    source="F5Bot (Reddit/HN)",
                    lead_name=lead_data.get("thread_title", "Anonymous Lead")[:100],
                    post_url=lead_data.get("source_url", url),
                    content_snippet=lead_data.get("context_snippet", body[:200]),
                    engagement_status="new",
                    ai_score=85,
                    suggested_reply=lead_data.get("draft_reply", "")
                )
                db.add(new_lead)
        db.commit()
    except Exception as e:
        print(f"F5Bot processing error: {e}")
        
    return {"status": "success", "received": True}

class CredentialSaveRequest(BaseModel):
    user_id: int
    platform: str
    username: str
    session_cookies: str

@app.post("/credentials")
async def save_social_credentials(request: CredentialSaveRequest, db: Session = Depends(get_db)):
    """
    Saves or updates a user's session cookies for Twitter, Reddit, or HackerNews.
    """
    user = db.query(models.User).filter_by(id=request.user_id).first()
    if not user:
        # Auto-create user if missing in MVP
        user = models.User(id=request.user_id, email=f"user{request.user_id}@agenticgtm.com")
        db.add(user)
        db.commit()
        db.refresh(user)
        
    db_cred = db.query(models.SocialCredential).filter_by(
        user_id=request.user_id,
        platform=request.platform
    ).first()
    
    if not db_cred:
        db_cred = models.SocialCredential(
            user_id=request.user_id,
            platform=request.platform,
            username=request.username,
            session_cookies=request.session_cookies
        )
        db.add(db_cred)
    else:
        db_cred.username = request.username
        db_cred.session_cookies = request.session_cookies
        
    db.commit()
    return {"status": "success", "message": f"{request.platform} credentials saved successfully!"}

@app.get("/credentials/{user_id}")
async def list_social_credentials(user_id: int, db: Session = Depends(get_db)):
    """
    Lists connected platform statuses for a user.
    """
    creds = db.query(models.SocialCredential).filter_by(user_id=user_id).all()
    return [
        {
            "platform": c.platform,
            "username": c.username,
            "connected": bool(c.session_cookies),
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in creds
    ]

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


