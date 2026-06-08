from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    clerk_id = Column(String, unique=True, index=True) # For Clerk Auth integration
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    stripeCustomerId = Column("stripe_customer_id", String, unique=True)
    stripeSubscriptionId = Column("stripe_subscription_id", String, unique=True)
    stripePriceId = Column("stripe_price_id", String)
    stripeCurrentPeriodEnd = Column("stripe_current_period_end", DateTime)
    plan = Column(String, default="HOBBY")
    searches_count = Column(Integer, default=0)
    last_search_date = Column(DateTime, nullable=True)
    
    products = relationship("Product", back_populates="owner")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    name = Column(String)
    url = Column(String)
    github_url = Column(String, nullable=True)
    description = Column(Text, nullable=True) # Extracted by AI Discovery Agent
    tagline = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    owner = relationship("User", back_populates="products")
    submissions = relationship("Submission", back_populates="product")
    content_plan = relationship("ContentPost", back_populates="product")
    testimonials = relationship("Testimonial", back_populates="product")
    social_leads = relationship("SocialLead", back_populates="product")
    campaign_links = relationship("CampaignLink", back_populates="product")
    icp_profile = relationship("ICPProfile", back_populates="product", uselist=False)
    competitors = relationship("Competitor", back_populates="product")

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    directory_name = Column(String) # e.g., "ProductHunt", "BetaList"
    directory_url = Column(String)
    status = Column(String, default="pending") # pending, submitted, failed, approved
    submission_url = Column(String, nullable=True) # Link to the live listing if available
    
    submitted_at = Column(DateTime, nullable=True)
    last_checked_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    product = relationship("Product", back_populates="submissions")

class ContentPost(Base):
    __tablename__ = "content_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    platform = Column(String) # Twitter, LinkedIn, Reddit, Dev.to
    content = Column(Text)
    status = Column(String, default="draft") # draft, approved, scheduled, posted
    scheduled_for = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    
    # Analytics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    
    product = relationship("Product", back_populates="content_plan")

class Testimonial(Base):
    __tablename__ = "testimonials"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    client_name = Column(String)
    client_role = Column(String) # e.g. "CTO at ScaleCorp"
    client_company = Column(String, nullable=True)
    rating = Column(Integer, default=5)
    review_text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    product = relationship("Product", back_populates="testimonials")

class SocialLead(Base):
    __tablename__ = "social_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    platform = Column(String) # HackerNews, Reddit, Twitter
    thread_title = Column(String)
    source_url = Column(String)
    context_snippet = Column(Text) # The matched user's post expressing pain point
    draft_reply = Column(Text) # The drafted referral response backed by a testimonial
    status = Column(String, default="pending") # pending, approved, posted
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    product = relationship("Product", back_populates="social_leads")
    outreach_sequence = relationship("OutreachSequence", back_populates="lead", uselist=False, cascade="all, delete-orphan")

class CampaignLink(Base):
    __tablename__ = "campaign_links"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    source = Column(String) # e.g., "Reddit_Launch", "BetaList", "Blog_Footer"
    original_url = Column(String) # Where the traffic is ultimately redirected
    
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0) # Tracks signups or purchases
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    product = relationship("Product", back_populates="campaign_links")

class ICPProfile(Base):
    __tablename__ = "icp_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True)
    
    ideal_job_titles = Column(Text) # JSON list of target titles
    top_channels = Column(Text) # JSON list of high ROI platforms
    core_pain_points = Column(Text) # JSON list of major user headaches
    refined_positioning = Column(Text) # dynamically tuned marketing pitch
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    product = relationship("Product", back_populates="icp_profile")

class Competitor(Base):
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    name = Column(String)
    url = Column(String)
    tagline = Column(String, nullable=True)
    listings = Column(Text) # JSON list of directories they are listed on
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    product = relationship("Product", back_populates="competitors")

class OutreachSequence(Base):
    __tablename__ = "outreach_sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("social_leads.id"))
    
    current_step = Column(Integer, default=1)
    status = Column(String, default="active") # active, paused, completed
    
    last_action_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    lead = relationship("SocialLead", back_populates="outreach_sequence")
    steps = relationship("SequenceStep", back_populates="sequence", cascade="all, delete-orphan")

class SequenceStep(Base):
    __tablename__ = "sequence_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(Integer, ForeignKey("outreach_sequences.id"))
    
    step_number = Column(Integer) # 1, 2, 3
    channel = Column(String) # Reddit, Twitter_DM, Email, LinkedIn
    draft_content = Column(Text)
    
    status = Column(String, default="draft") # draft, approved, sent, skipped
    
    scheduled_for = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    
    sequence = relationship("OutreachSequence", back_populates="steps")

class Waitlist(Base):
    __tablename__ = "waitlist"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    
    # Optional fields for better targeting
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    role = Column(String, nullable=True)
    
    # Tracking
    referral_source = Column(String, nullable=True) # Where they came from
    status = Column(String, default="pending") # pending, invited, onboarded
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    invited_at = Column(DateTime, nullable=True)

class SocialCredential(Base):
    __tablename__ = "social_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    platform = Column(String) # "Twitter", "Reddit", "HackerNews"
    username = Column(String)
    password = Column(String) # For MVP auto-login
    session_cookies = Column(Text, nullable=True) # Extracted Playwright cookies
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", backref="social_credentials")
