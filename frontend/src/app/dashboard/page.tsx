"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useSession, signOut } from "next-auth/react";

// Types for Sidebar Navigation Menu Items
interface MenuItem {
  id: string;
  name: string;
  icon: React.ReactNode;
}

// Background AI Terminal Logs


import { useRouter } from "next/navigation";

export default function Dashboard() {
  const { data: session, status } = useSession();
  const user = session?.user;
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  const router = useRouter();
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  const [activeTab, setActiveTab] = useState<string>("product");
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [darkMode, setDarkMode] = useState<boolean>(false);
  

  // Product Onboarding Workspace State
  const [onboardUrl, setOnboardUrl] = useState<string>("");
  const [isOnboarding, setIsOnboarding] = useState<boolean>(false);
  const [onboardError, setOnboardError] = useState<string | null>(null);
  const [onboardStep, setOnboardStep] = useState<string>("");
  const [product, setProduct] = useState<any | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState<boolean>(false);
  const [upgradeMessage, setUpgradeMessage] = useState<string>("");
  const [userPlan, setUserPlan] = useState<string>("FREE");

  const authFetch = async (url: string, options: any = {}) => {
    const headers = { ...options.headers };
    if (user?.email) {
      headers["x-clerk-id"] = user.email; // Backend uses this as unique ID
      headers["x-user-email"] = user.email || "";
    }
    return fetch(url, { ...options, headers });
  };

  // Retrieve user's onboarded product on mount or auth state change
  useEffect(() => {
    if (user?.email) {
      authFetch(`${API_URL}/products/me`)
        .then(res => res.json())
        .then(data => {
          if (data && data.product_id) {
            setProduct(data);
            localStorage.setItem("agenticgtm_product", JSON.stringify(data));
          } else {
            setProduct(null);
            localStorage.removeItem("agenticgtm_product");
          }
        })
        .catch(e => console.error("Failed to fetch product", e));
    }
  }, [user?.email]);

  // Sync Dark Mode state with DOM
  useEffect(() => {
    const root = window.document.documentElement;
    if (darkMode) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [darkMode]);

  

  // Persistent product update helper
  const updateProductState = (newProduct: any | null) => {
    setProduct(newProduct);
    if (newProduct) {
      localStorage.setItem("agenticgtm_product", JSON.stringify(newProduct));
    } else {
      localStorage.removeItem("agenticgtm_product");
    }
  };

  // API Trigger: Onboard Startup Landing Page
  const handleOnboard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!onboardUrl.trim()) return;

    setIsOnboarding(true);
    setOnboardError(null);
    setOnboardStep("Launching Playwright stealth browser...");

    // Engaging Notion loading status sub-steps
    const steps = [
      "Reading your website...",
      "Analyzing content...",
      "Gathering data...",
      "Structuring information...",
      "Generating insights...",
      "Finalizing profile..."
    ];

    let currentStep = 0;
    const stepInterval = setInterval(() => {
      if (currentStep < steps.length) {
        setOnboardStep(steps[currentStep]);
        currentStep++;
      }
    }, 2000);

    try {
      const response = await authFetch(`${API_URL}/onboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: onboardUrl.trim() }),
      });

      clearInterval(stepInterval);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to onboard startup.");
      }

      const result = await response.json();
      if (result.status === "error") {
        throw new Error(result.message);
      }

      updateProductState(result);
    } catch (err: any) {
      clearInterval(stepInterval);
      setOnboardError(err.message || "A connection error occurred. Make sure your FastAPI backend is running!");
    } finally {
      setIsOnboarding(false);
      setOnboardStep("");
    }
  };

  // --- SOCIAL LISTENING CRM WORKSPACE STATES ---
  const [leads, setLeads] = useState<any[]>([]);
  const [leadsLoading, setLeadsLoading] = useState<boolean>(false);
  const [scoutLoading, setScoutLoading] = useState<boolean>(false);
  const [targetKeyword, setTargetKeyword] = useState<string>("");
  const [isPublishingLeadId, setIsPublishingLeadId] = useState<number | null>(null);
  
  // F5Bot Manual Alert Modal States
  const [showAddLeadModal, setShowAddLeadModal] = useState<boolean>(false);
  const [newLeadPlatform, setNewLeadPlatform] = useState<string>("HackerNews");
  const [newLeadTitle, setNewLeadTitle] = useState<string>("");
  const [newLeadUrl, setNewLeadUrl] = useState<string>("");
  const [newLeadBody, setNewLeadBody] = useState<string>("");
  const [newLeadLoading, setNewLeadLoading] = useState<boolean>(false);
  const [newLeadError, setNewLeadError] = useState<string | null>(null);

  // Trigger Fetch leads on active social tab
  useEffect(() => {
    if (activeTab === "opportunities" || activeTab === "campaigns" && product) {
      fetchLeads();
    }
  }, [activeTab, product]);

  // API Call: Fetch leads from SQLite Database
  const fetchLeads = async () => {
    if (!product) return;
    setLeadsLoading(true);
    try {
      const response = await authFetch(`${API_URL}/products/${product.product_id}/leads`);
      if (response.ok) {
        const data = await response.json();
        setLeads(data);
      }
    } catch (err) {
      console.error("Failed to load leads list from backend", err);
    } finally {
      setLeadsLoading(false);
    }
  };

  // API Call: Trigger Social Listening Mock Scout
  const handleScoutMock = async () => {
    if (!product) return;
    setScoutLoading(true);
    try {
      const response = await authFetch(`${API_URL}/listen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          product_id: product.product_id,
          target_keyword: targetKeyword || undefined
        }),
      });
      if (response.ok) {
        await fetchLeads();
      } else {
        const errData = await response.json();
        if (response.status === 403) {
          setUpgradeMessage(errData.detail || "Usage limit reached.");
          setShowUpgradeModal(true);
        } else {
          showToast(errData.detail || "Failed to run scout.", "error");
        }
      }
    } catch (err) {
      console.error("Failed to run active mock scout", err);
      alert("Failed to connect to the server.");
    } finally {
      setScoutLoading(false);
    }
  };

  // API Call: Submit F5Bot copy-paste Alert Manually
  const handleManualLeadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!product || !newLeadTitle.trim() || !newLeadBody.trim()) return;

    setNewLeadLoading(true);
    setNewLeadError(null);

    try {
      const response = await authFetch(`${API_URL}/leads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: product.product_id,
          platform: newLeadPlatform,
          thread_title: newLeadTitle.trim(),
          source_url: newLeadUrl.trim() || `https://mock-${newLeadPlatform.toLowerCase()}.com/thread/${Date.now()}`,
          context_snippet: newLeadBody.trim()
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to onboard lead alert.");
      }

      await fetchLeads();
      setShowAddLeadModal(false);
      
      // Reset Form fields
      setNewLeadTitle("");
      setNewLeadUrl("");
      setNewLeadBody("");
    } catch (err: any) {
      setNewLeadError(err.message || "Failed to analyze and save manual lead.");
    } finally {
      setNewLeadLoading(false);
    }
  };

  // API Call: Trigger Playwright Stealth Reply Posting
  const handlePublishLeadReply = async (leadId: number) => {
    setIsPublishingLeadId(leadId);
    try {
      const response = await authFetch(`${API_URL}/leads/${leadId}/publish`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Playwright posting failed.");
      }

      const result = await response.json();
      
      // Update local state to reflect success
      setLeads((prevLeads) =>
        prevLeads.map((lead) =>
          lead.id === leadId
            ? { ...lead, status: "posted", screenshot_url: result.screenshot_url }
            : lead
        )
      );
      
      showToast("Playwright Browser successfully posted the comment referral comment autonomously!", "success");
    } catch (err: any) {
      showToast(`Posting Failed: ${err.message}`, "error");
      setLeads((prevLeads) =>
        prevLeads.map((lead) =>
          lead.id === leadId ? { ...lead, status: "failed" } : lead
        )
      );
    } finally {
      setIsPublishingLeadId(null);
    }
  };

  // --- DIRECTORY SUBMISSIONS & SOCIAL DRAFTS WORKSPACE STATES ---
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [submissionsLoading, setSubmissionsLoading] = useState<boolean>(false);
  const [isSubmittingDirectoryName, setIsSubmittingDirectoryName] = useState<string | null>(null);
  
  const [posts, setPosts] = useState<any[]>([]);
  const [postsLoading, setPostsLoading] = useState<boolean>(false);
  const [isPublishingPostId, setIsPublishingPostId] = useState<number | null>(null);

  // --- SEO BLOG STUDIO STATES ---
  const [keywords, setKeywords] = useState<string[]>([]);
  const [newKeyword, setNewKeyword] = useState<string>("");
  const [isGeneratingBlog, setIsGeneratingBlog] = useState<boolean>(false);
  const [selectedBlog, setSelectedBlog] = useState<any | null>(null);
  const [showDeleteAllModal, setShowDeleteAllModal] = useState<boolean>(false);

  // --- ANALYTICS & METRICS STATES ---
  const [summaryData, setSummaryData] = useState<any | null>(null);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(false);

  // --- UI TOAST NOTIFICATION STATES ---
  const [showNotifications, setShowNotifications] = useState<boolean>(false);
  const [showProfileMenu, setShowProfileMenu] = useState<boolean>(false);
  const isAiRunning = submissionsLoading || postsLoading || isGeneratingBlog || isPublishingPostId !== null || isOnboarding || newLeadLoading || isPublishingLeadId !== null;
  const [toasts, setToasts] = useState<{id: number, message: string, type: 'success'|'error'}[]>([]);
  const showToast = (message: string, type: 'success'|'error' = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, {id, message, type}]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  // Sync state triggers on Tab Change
  useEffect(() => {
    if (activeTab === "campaigns" && product) {
      fetchSubmissions();
      fetchPosts();
    } else if (activeTab === "recommendations" && product) {
      fetchPosts();
    } else if (activeTab === "analytics" && product) {
      fetchSummary();
    }
  }, [activeTab, product]);

  const fetchSummary = async () => {
    if (!product) return;
    setSummaryLoading(true);
    try {
      const response = await authFetch(`${API_URL}/dashboard/summary/${product.product_id}`);
      if (response.ok) {
        const data = await response.json();
        setSummaryData(data);
      }
    } catch (err) {
      console.error("Failed to load dashboard summary", err);
    } finally {
      setSummaryLoading(false);
    }
  };

  const fetchSubmissions = async () => {
    if (!product) return;
    setSubmissionsLoading(true);
    try {
      const response = await authFetch(`${API_URL}/products/${product.product_id}/submissions`);
      if (response.ok) {
        const data = await response.json();
        setSubmissions(data);
      }
    } catch (err) {
      console.error("Failed to load submissions list", err);
    } finally {
      setSubmissionsLoading(false);
    }
  };

  const fetchPosts = async () => {
    if (!product) return;
    setPostsLoading(true);
    try {
      const response = await authFetch(`${API_URL}/products/${product.product_id}/posts`);
      if (response.ok) {
        const data = await response.json();
        setPosts(data);
      }
    } catch (err) {
      console.error("Failed to load generated posts list", err);
    } finally {
      setPostsLoading(false);
    }
  };

  const executeDeleteAllDrafts = async () => {
    if (!product) return;
    try {
      const response = await authFetch(`${API_URL}/products/${product.product_id}/posts`, {
        method: "DELETE"
      });
      if (response.ok) {
        setPosts([]);
        setSelectedBlog(null);
        setShowDeleteAllModal(false);
      }
    } catch (err) {
      console.error("Failed to delete all drafts", err);
    }
  };

  // Triggers Gemini to draft social content and seed the directory list in the DB
  const handleSeedPipeline = async () => {
    if (!product) return;
    setSubmissionsLoading(true);
    setPostsLoading(true);
    try {
      const response = await authFetch(`${API_URL}/generate-copy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: product.product_id }),
      });
      if (response.ok) {
        await fetchSubmissions();
        await fetchPosts();
      }
    } catch (err) {
      console.error("Failed to seed social copy pipeline", err);
    } finally {
      setSubmissionsLoading(false);
      setPostsLoading(false);
    }
  };

  // Playwright Auto-Submitter trigger
  const handleAutoSubmitDirectory = async (name: string, url: string) => {
    if (!product) return;
    setIsSubmittingDirectoryName(name);
    try {
      const response = await authFetch(`${API_URL}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: product.product_id,
          directory_name: name,
          directory_url: url
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Submission agent failed.");
      }

      const result = await response.json();
      
      setSubmissions((prev) =>
        prev.map((sub) =>
          sub.directory_name === name
            ? { ...sub, status: "submitted", screenshot_url: result.screenshot_url }
            : sub
        )
      );
      showToast(`Playwright successfully auto-submitted your startup to ${name}!`, "success");
    } catch (err: any) {
      showToast(`Auto-submission failed: ${err.message}`, "error");
      setSubmissions((prev) =>
        prev.map((sub) =>
          sub.directory_name === name ? { ...sub, status: "failed" } : sub
        )
      );
    } finally {
      setIsSubmittingDirectoryName(null);
    }
  };

  // Manual Social Publishing trigger (Twitter/Reddit drafts)
  const handlePublishSocialPost = async (postId: number) => {
    setIsPublishingPostId(postId);
    try {
      const post = posts.find((p: any) => p.id === postId);
      if (!post) throw new Error("Post not found");
      
      await navigator.clipboard.writeText(post.content);
      showToast(`Copy successful! Opening ${post.platform} to publish.`, "success");
      
      if (post.platform.toLowerCase() === "twitter" || post.platform.toLowerCase() === "x") {
        window.open("https://x.com/compose/post", "_blank");
      } else if (post.platform.toLowerCase() === "reddit") {
        window.open("https://www.reddit.com/submit", "_blank");
      } else {
        window.open("https://www.linkedin.com/feed/", "_blank");
      }
      
      setPosts((prev) =>
        prev.map((p) =>
          p.id === postId
            ? { ...p, status: "posted" }
            : p
        )
      );
    } catch (err: any) {
      showToast(`Failed: ${err.message}`, "error");
    } finally {
      setIsPublishingPostId(null);
    }
  };

  // SEO Blog Generation trigger
  const handleGenerateBlog = async () => {
    if (!product) return;
    setIsGeneratingBlog(true);
    try {
      const response = await authFetch(`${API_URL}/blogs/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: product.product_id,
          keywords: keywords
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 403) {
          setUpgradeMessage(errorData.detail || "Usage limit reached.");
          setShowUpgradeModal(true);
          setIsGeneratingBlog(false);
          return;
        }
        throw new Error(errorData.detail || "AI Blog generation failed.");
      }

      const result = await response.json();
      await fetchPosts(); // Reload posts to update blog list
      
      const newBlog = {
        id: result.post_id,
        platform: "Dev.to",
        content: `Title: ${result.title}\n\n${result.body}`,
        status: "draft"
      };
      setSelectedBlog(newBlog);
    } catch (err: any) {
      showToast(`Blog Generation failed: ${err.message}`, "error");
    } finally {
      setIsGeneratingBlog(false);
    }
  };

  // Manual Blog Publisher trigger
  const handlePublishBlog = async (postId: number, platform: string = "dev.to") => {
    setIsGeneratingBlog(true);
    try {
      const blog = posts.find((p: any) => p.id === postId) || selectedBlog;
      if (!blog) throw new Error("Blog post not found");
      await navigator.clipboard.writeText(blog.content);
      
      if (platform === "linkedin") {
        showToast(`Copy successful! Opening LinkedIn to publish.`, "success");
        window.open("https://www.linkedin.com/post/new", "_blank");
      } else {
        showToast(`Copy successful! Opening Dev.to to publish.`, "success");
        window.open("https://dev.to/new", "_blank");
      }
      
      const prevStatus = blog.status || "draft";
      let newStatus = "posted";
      
      if (platform === "linkedin") {
        newStatus = prevStatus.includes("devto") ? "posted_both" : prevStatus === "posted_both" ? "posted_both" : "posted_linkedin";
      } else {
        newStatus = prevStatus.includes("linkedin") ? "posted_both" : prevStatus === "posted_both" ? "posted_both" : "posted_devto";
      }
      
      // Update local posts list
      setPosts((prev) =>
        prev.map((post) =>
          post.id === postId
            ? { ...post, status: newStatus }
            : post
        )
      );

      if (selectedBlog && selectedBlog.id === postId) {
        setSelectedBlog((prev: any) => ({
          ...prev,
          status: newStatus
        }));
      }
    } catch (err: any) {
      showToast(`Blog Copy failed: ${err.message}`, "error");
    } finally {
      setIsGeneratingBlog(false);
    }
  };

  // Notion-Style SVG Icons (Hand-drawn, lightweight vector elements)
  const icons = {
    product: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
    social: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    ),
    directories: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
    ),
    blogs: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    analytics: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    toggleCollapse: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
      </svg>
    ),
    toggleExpand: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
      </svg>
    ),
    sun: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707m12.728 12.728A9 9 0 115.636 5.636m12.728 12.728L12 12" />
      </svg>
    ),
    moon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>
    ),
    user: (
      <div className="flex items-center justify-center w-6 h-6 text-sm font-semibold rounded-xl bg-zinc-200 dark:bg-white/[0.04] text-zinc-700 dark:text-[#aab1be]">
        TL
      </div>
    )
  };

    const menuItems: MenuItem[] = [
    { id: "product", name: "Startup Overview", icon: icons.product },
    { id: "opportunities", name: "Growth Opportunities", icon: icons.social },
    { id: "campaigns", name: "Launch & Submissions Center", icon: icons.directories },
    { id: "recommendations", name: "AI Recommendations", icon: icons.blogs },
    { id: "analytics", name: "Recent Activity", icon: icons.analytics },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-white text-zinc-800 dark:bg-[#0F1115] dark:text-[#f8f9fa] transition-colors duration-300 ease-out relative">
      


      {/* 1. LEFT SIDEBAR */}
      <aside 
        className={`flex flex-col h-full border-r border-zinc-200/50 dark:border-white/[0.06] bg-[#FAFAFA]/95 dark:bg-[#0A0A0C]/95 backdrop-blur-2xl transition-all duration-400 ease-in-out shadow-[4px_0_32px_rgba(0,0,0,0.02)] relative z-20 ${
          sidebarCollapsed ? "w-[64px]" : "w-[260px]"
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-200/60 dark:border-white/[0.04]">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2  text-sm font-bold tracking-tight text-zinc-900 dark:text-[#f8f9fa]">
              <span className="text-zinc-400">⚡</span> AgenticGTM
            </div>
          )}
          <button 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1 rounded-xl hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-500 dark:text-[#8b919e]"
            title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {sidebarCollapsed ? icons.toggleExpand : icons.toggleCollapse}
          </button>
        </div>

        {/* Sidebar Menu Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {menuItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center text-left w-full gap-3 px-3 py-2.5 text-sm font-medium rounded-[12px] transition-all duration-300 ease-in-out group ${
                  isActive 
                    ? "bg-white dark:bg-[#1A1D24] text-zinc-900 dark:text-white font-semibold shadow-[0_2px_12px_rgba(0,0,0,0.06)] border border-zinc-200/80 dark:border-white/[0.08]" 
                    : "text-zinc-500 dark:text-zinc-400 hover:bg-zinc-200/50 dark:hover:bg-white/[0.04] hover:text-zinc-900 dark:hover:text-zinc-100 border border-transparent"
                }`}
                title={item.name}
              >
                <span className={`shrink-0 ${isActive ? "text-zinc-900 dark:text-[#f8f9fa]" : "text-zinc-400 dark:text-[#6e7583]"}`}>
                  {item.icon}
                </span>
                {!sidebarCollapsed && <span className="truncate leading-none pt-0.5">{item.name}</span>}
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer (User Info & Quotas & Light/Dark Theme Switcher) */}
        <div className="p-4 border-t border-zinc-200/40 dark:border-white/[0.02] space-y-5 bg-[#FAFAFA] dark:bg-[#111318]">
          
          {/* Light/Dark Toggle */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="flex items-center justify-center w-full gap-2 px-3 py-2 text-sm font-medium border border-zinc-200/50 dark:border-white/[0.04] rounded-l-xlg hover:bg-zinc-100 dark:hover:bg-zinc-800/80 transition-all duration-200 ease-out shadow-sm"
          >
            {darkMode ? (
              <>
                {icons.sun}
                {!sidebarCollapsed && <span>Light Mode</span>}
              </>
            ) : (
              <>
                {icons.moon}
                {!sidebarCollapsed && <span>Dark Mode</span>}
              </>
            )}
          </button>

          {/* User Quotas Card (PRO MODE) */}
          {!sidebarCollapsed ? (
            <div className="p-4 space-y-3 rounded-xl bg-white dark:bg-[#171A21] border border-zinc-200/80 dark:border-white/[0.06] text-sm shadow-md transition-all duration-300 hover:shadow-lg">
              <div className="flex items-center gap-2">
                {icons.user}
                <div className="font-semibold text-zinc-900 dark:text-[#f8f9fa] truncate">
                  {user?.email || "Pro User"}
                </div>
              </div>
              <div className="pt-2 border-t border-zinc-100/50 dark:border-white/[0.04] space-y-1 text-[10px] text-zinc-500 dark:text-[#8b919e]">
                <div className="flex justify-between">
                  <span>Directory submissions:</span>
                  <span className="font-medium text-emerald-600 dark:text-emerald-400">{summaryData?.stats?.directories?.total || 0} / ∞</span>
                </div>
                <div className="flex justify-between">
                  <span>AI leads scouted:</span>
                  <span className="font-medium text-emerald-600 dark:text-emerald-400">{summaryData?.stats?.leads?.total || 0} / ∞</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex justify-center p-2 rounded-xl bg-white dark:bg-[#171A21] border border-zinc-200/80 dark:border-white/[0.06] shadow-sm">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-400 to-emerald-600 flex items-center justify-center text-white font-bold text-xs shadow-sm">
                PRO
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* 2. MAIN CONTENT AREA */}
      <main className="flex-1 flex flex-col h-full overflow-y-auto overflow-x-hidden bg-[#FAFAFA] dark:bg-[#050505] relative custom-scrollbar">
        
        {/* Main Content Header */}
        <header className="flex items-center justify-between px-8 py-4 bg-white/80 dark:bg-[#0A0A0C]/80 backdrop-blur-3xl border-b border-zinc-200/50 dark:border-white/[0.06] shadow-[0_4px_32px_rgba(0,0,0,0.02)] z-10 shrink-0 select-none sticky top-0">
          
          <div className="flex items-center gap-4 flex-1">
            {/* Workspace Switcher */}
            <button className="flex items-center gap-2 py-1.5 px-3 hover:bg-zinc-100 dark:hover:bg-zinc-800/50 rounded-l-xlg transition-all duration-200 ease-out border border-transparent hover:border-zinc-200/50 dark:hover:border-zinc-700/50 shadow-[inset_0_1px_2px_rgba(0,0,0,0.01)] hover:shadow-sm">
              <div className="w-6 h-6 rounded-xl bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center shadow-sm">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L2 22H22L12 2Z" fill="currentColor" className="text-white dark:text-black"/>
                </svg>
              </div>
              <span className="text-sm font-medium text-zinc-900 dark:text-[#e4e7ec]">Personal Workspace</span>
              <svg className="w-3.5 h-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Breadcrumb slash */}
            <span className="text-zinc-300 dark:text-zinc-700">/</span>

            {/* Search Bar */}
            <div className="relative max-w-lg w-full flex-1 ml-6">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                placeholder="Search campaigns, audiences, or ask AI..."
                className="w-full pl-10 pr-4 py-2.5 bg-zinc-100/50 dark:bg-[#141417] border border-zinc-200/50 dark:border-white/[0.04] focus:bg-white dark:focus:bg-[#1A1D24] focus:border-zinc-300/80 dark:focus:border-white/[0.12] hover:bg-zinc-100 dark:hover:bg-white/[0.06] rounded-[14px] text-sm focus:outline-none focus:ring-4 focus:ring-zinc-900/5 dark:focus:ring-white/5 transition-all duration-300 ease-out text-zinc-900 dark:text-white placeholder-zinc-400 shadow-[inset_0_1px_2px_rgba(0,0,0,0.02)]"
              />
              <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
                 <kbd className="px-2 py-1 text-[10px] font-medium bg-white dark:bg-white/[0.04] rounded-xl border border-zinc-200/50 dark:border-white/[0.02] text-zinc-400 shadow-sm">⌘K</kbd>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-5 ml-4">
            {/* Soft Status Indicator */}
            <div className="flex items-center gap-2 px-4 py-1.5 bg-white dark:bg-white/[0.03] border border-zinc-200/80 dark:border-white/[0.08] rounded-full shadow-[0_2px_8px_rgba(0,0,0,0.04)] transition-all duration-300 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
              <span className="relative flex h-2 w-2">
                {isAiRunning ? (
                  <>
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </>
                ) : (
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-zinc-400 dark:bg-zinc-500"></span>
                )}
              </span>
              <span className={`text-xs font-medium ${isAiRunning ? 'text-emerald-600 dark:text-emerald-400' : 'text-zinc-500 dark:text-[#8b919e]'}`}>
                {isAiRunning ? 'AI Processing' : 'AI Idle'}
              </span>
            </div>

            {/* Notifications Center */}
            <div className="relative">
              <button onClick={() => setShowNotifications(!showNotifications)} className="p-2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors duration-300 ease-out relative">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                {summaryData?.activity_feed && summaryData.activity_feed.length > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500 border-2 border-white dark:border-[#0A0B0E]"></span>
                )}
              </button>
              
              <AnimatePresence>
                {showNotifications && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 mt-3 w-80 bg-white dark:bg-[#12141A] border border-zinc-200 dark:border-white/[0.06] rounded-2xl shadow-2xl overflow-hidden z-50"
                  >
                    <div className="p-4 border-b border-zinc-100 dark:border-white/[0.04]">
                      <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">Notifications</h3>
                    </div>
                    <div className="max-h-[300px] overflow-y-auto custom-scrollbar divide-y divide-zinc-100 dark:divide-white/[0.02]">
                      {summaryData?.activity_feed?.length > 0 ? (
                        summaryData.activity_feed.slice(0, 5).map((action: any) => (
                          <div key={action.id} className="p-4 hover:bg-zinc-50 dark:hover:bg-white/[0.02] transition-colors">
                            <p className="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed mb-1.5">{action.message}</p>
                            <span className="text-[10px] font-medium text-zinc-400 dark:text-zinc-500">
                              {new Date(action.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                          </div>
                        ))
                      ) : (
                        <div className="p-6 text-center text-xs text-zinc-400">No new notifications</div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Profile Section */}
            <div className="relative flex items-center ml-2">
              <button 
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="w-8 h-8 rounded-full border border-zinc-200 dark:border-white/[0.06] shadow-sm overflow-hidden flex items-center justify-center hover:ring-2 hover:ring-zinc-300 dark:hover:ring-zinc-600 transition-all"
              >
                {user?.image ? (
                  <img src={user.image} alt="Profile" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold">
                    {user?.name?.charAt(0) || user?.email?.charAt(0) || "U"}
                  </div>
                )}
              </button>

              <AnimatePresence>
                {showProfileMenu && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.15, ease: "easeOut" }}
                    className="absolute right-0 top-full mt-3 w-56 bg-white dark:bg-[#12141A] border border-zinc-200 dark:border-white/[0.06] rounded-2xl shadow-[0_12px_40px_rgba(0,0,0,0.12)] overflow-hidden z-50 py-2"
                  >
                    <div className="px-4 py-3 border-b border-zinc-100 dark:border-white/[0.04]">
                      <p className="text-xs font-semibold text-zinc-900 dark:text-white truncate">{user?.name || "Premium User"}</p>
                      <p className="text-[10px] text-zinc-500 dark:text-zinc-400 truncate mt-0.5">{user?.email}</p>
                    </div>
                    
                    <div className="py-1">
                      <button 
                        onClick={() => { setActiveTab("settings"); setShowProfileMenu(false); }}
                        className="w-full text-left px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-white/[0.03] transition-colors flex items-center gap-2"
                      >
                        <svg className="w-4 h-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                        Account Settings
                      </button>
                      <button 
                        onClick={() => { setActiveTab("billing"); setShowProfileMenu(false); }}
                        className="w-full text-left px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-white/[0.03] transition-colors flex items-center gap-2"
                      >
                        <svg className="w-4 h-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path></svg>
                        Billing & Quotas
                      </button>
                    </div>

                    <div className="border-t border-zinc-100 dark:border-white/[0.04] py-1">
                      <button 
                        onClick={() => signOut({ callbackUrl: "/" })}
                        className="w-full text-left px-4 py-2 text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors flex items-center gap-2"
                      >
                        <svg className="w-4 h-4 text-red-500/70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                        Sign Out
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </header>

        {/* Main Content Workspace Body */}
        <section className="flex-1 p-6 md:p-10 max-w-[1400px] w-full mx-auto space-y-16">
          
          {/* TAB 1: PRODUCT HUB */}
          {activeTab === "product" && (
            <div className="space-y-10 animate-fadeIn max-w-5xl mx-auto w-full">
              
              {/* STATE A: IS ONBOARDING (LOADING) */}
              {isOnboarding && (
                <div className="max-w-md mx-auto p-8 md:p-12 border border-zinc-200/80 dark:border-white/[0.06] rounded-2xl bg-white dark:bg-[#14161C] text-center space-y-10 my-12 shadow-md hover:shadow-xl transition-all duration-300">
                  <div className="relative w-12 h-12 mx-auto flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full border-2 border-zinc-200/60 dark:border-white/[0.04]"></div>
                    <div className="absolute inset-0 rounded-full border-2 border-t-zinc-900 dark:border-t-white animate-spin"></div>
                  </div>
                  <div className="space-y-3">
                    <h3 className="font-semibold text-sm text-zinc-900 dark:text-[#f8f9fa]">Analyzing Website with Agents</h3>
                    <p className="text-sm text-zinc-400 dark:text-[#6e7583]  ">{onboardStep}</p>
                  </div>
                  <div className="text-[10px] text-zinc-400 dark:text-[#6e7583] leading-relaxed max-w-xs mx-auto">
                    Playwright is spinning up a stealth browser, scraping HTML structure, and querying Gemini Flash to build your profile.
                  </div>
                </div>
              )}

              {/* STATE B: NOT ONBOARDED YET */}
              {!isOnboarding && !product && (
                <div className="space-y-10">
                  <div className="space-y-3">
                    <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white">Product Onboarding</h1>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">
                      Onboard your B2B SaaS startup landing page to automatically discover target categories, taglines, and active pain points.
                    </p>
                  </div>
                  
                  <div className="max-w-xl mx-auto space-y-10 p-8 md:p-12 border border-zinc-200/60 dark:border-white/[0.08] rounded-[24px] bg-white dark:bg-[#0D0F12] shadow-[0_8px_32px_rgba(0,0,0,0.04)] hover:shadow-[0_16px_48px_rgba(0,0,0,0.06)] transition-all duration-500 my-6 relative overflow-hidden">
                    <div className="space-y-3">
                      <h2 className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-white">Analyze Startup</h2>
                      <p className="text-sm text-zinc-500 dark:text-[#8b919e] leading-relaxed">
                        Input your landing page URL. The backend agent will use headful browser sessions to index layout elements, parse tech details, and structure custom value propositions.
                      </p>
                    </div>
                    
                    <form onSubmit={handleOnboard} className="space-y-6">
                      <div className="flex flex-col gap-2">
                        <label className="text-sm font-bold text-zinc-500 dark:text-[#8b919e]">Website URL</label>
                        <input 
                          type="url" 
                          placeholder="https://example.com" 
                          value={onboardUrl}
                          onChange={(e) => setOnboardUrl(e.target.value)}
                          required
                          className="w-full px-4 py-3 border rounded-xl border-zinc-200/60 dark:border-white/[0.04] bg-white dark:bg-[#0F1115] rounded-xl outline-none text-sm"
                        />
                      </div>
                      
                      {onboardError && (
                        <div className="p-3 text-sm rounded-xl border border-red-200 bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-400">
                          ⚠️ {onboardError}
                        </div>
                      )}
                      
                      <button 
                        type="submit" 
                        className="w-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold px-4 py-2 rounded-xl transition-colors duration-300 ease-out text-sm"
                      >
                        Start Agent Discovery
                      </button>
                    </form>
                  </div>
                </div>
              )}

              {/* STATE C: STARTUP PROFILE ACTIVE */}
              {!isOnboarding && product && (
                <div className="space-y-10 animate-fadeIn">
                  <div className="flex items-center justify-between border-b border-zinc-200/60 dark:border-white/[0.04] pb-4">
                    <div className="space-y-1">
                      <div className="text-[10px]  font-bold  tracking-wider text-zinc-400 dark:text-[#6e7583]">Active Startup Profile</div>
                      <h1 className="text-xl font-medium text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-2">
                        {product.name}
                      </h1>
                    </div>
                    <button 
                      onClick={() => { updateProductState(null); setOnboardUrl(""); }}
                      className="px-3 py-1.5 text-sm border border-zinc-200/60 dark:border-white/[0.04] hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl font-semibold text-zinc-600 dark:text-[#aab1be]"
                    >
                      Change Startup
                    </button>
                  </div>

                  {/* Product Metadata Info Board */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:p-10">
                    
                    {/* Left Panel: Primary Content */}
                    <div className="md:col-span-2 space-y-10">
                      
                      {/* Tagline Card */}
                      <div className="p-5 border border-zinc-200/50 dark:border-white/[0.06] rounded-[16px] bg-white dark:bg-[#0D0F12] space-y-3 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                        <h3 className="text-sm  font-semibold  tracking-wider text-zinc-400 dark:text-[#6e7583]">AI Tagline</h3>
                        <p className="text-base font-semibold italic text-zinc-800 dark:text-[#c4cad4]">
                          "{product.tagline}"
                        </p>
                      </div>

                      {/* Value Proposition Description */}
                      <div className="p-5 border border-zinc-200/50 dark:border-white/[0.06] rounded-[16px] bg-white dark:bg-[#0D0F12] space-y-3 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                        <h3 className="text-sm  font-semibold  tracking-wider text-zinc-400 dark:text-[#6e7583]">Core Value Proposition</h3>
                        <p className="text-sm leading-relaxed text-zinc-600 dark:text-[#aab1be]">
                          {product.description}
                        </p>
                      </div>

                      {/* Key Features */}
                      {product.key_features && (
                        <div className="p-5 border border-zinc-200/50 dark:border-white/[0.06] rounded-[16px] bg-white dark:bg-[#0D0F12] space-y-5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                          <h3 className="text-sm  font-semibold  tracking-wider text-zinc-400 dark:text-[#6e7583]">Key Features</h3>
                          <ul className="space-y-3 pl-4 list-disc text-sm text-zinc-600 dark:text-[#aab1be]">
                            {Array.isArray(product.key_features)
                              ? product.key_features.map((kf: string, idx: number) => <li key={idx}>{kf}</li>)
                              : <li>{product.key_features}</li>
                            }
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Right Panel: Side attributes & Shortcuts */}
                    <div className="space-y-10">
                      
                      {/* Live Url Card */}
                      <div className="p-5 border border-zinc-200/50 dark:border-white/[0.06] rounded-[16px] bg-white dark:bg-[#0D0F12] space-y-3 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                        <h3 className="text-sm  font-semibold  tracking-wider text-zinc-400 dark:text-[#6e7583]">Target Address</h3>
                        <a 
                          href={product.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-base font-medium text-zinc-600 dark:text-[#aab1be] hover:text-zinc-950 dark:hover:text-white underline truncate block"
                        >
                          {product.url}
                        </a>
                      </div>

                      {/* Target Audiences */}
                      {product.target_audience && (
                        <div className="p-5 border border-zinc-200/50 dark:border-white/[0.06] rounded-[16px] bg-white dark:bg-[#0D0F12] space-y-5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                          <h3 className="text-sm  font-semibold  tracking-wider text-zinc-400 dark:text-[#6e7583]">ICP Audiences</h3>
                          <div className="flex flex-wrap gap-1.5">
                            {Array.isArray(product.target_audience) 
                              ? product.target_audience.map((ta: string, idx: number) => (
                                  <span key={idx} className="px-2 py-0.5 text-sm font-semibold rounded-xl bg-zinc-100 dark:bg-white/[0.04] text-zinc-600 dark:text-[#8b919e] border border-zinc-200/50 dark:border-white/[0.03]">
                                    {ta}
                                  </span>
                                ))
                              : <span className="px-2 py-0.5 text-sm font-semibold rounded-xl bg-zinc-100 dark:bg-white/[0.04] text-zinc-600 dark:text-[#8b919e] border border-zinc-200/50 dark:border-white/[0.03]">{product.target_audience}</span>
                            }
                          </div>
                        </div>
                      )}

                      {/* GTM Hub Links Shortcuts */}
                      <div className="p-5 border border-zinc-200/50 dark:border-white/[0.06] rounded-[16px] bg-white dark:bg-[#0D0F12] space-y-5 shadow-[0_2px_12px_rgba(0,0,0,0.02)]">
                        <h3 className="text-sm  font-semibold  tracking-wider text-zinc-400 dark:text-[#6e7583]">Quick Campaigns</h3>
                        <div className="space-y-1.5 text-sm font-semibold">
                          <button 
                            onClick={() => setActiveTab("social")}
                            className="w-full text-left flex items-center justify-between p-2 rounded-xl hover:bg-zinc-200 dark:hover:bg-zinc-800 border border-zinc-200/40 dark:border-white/[0.03]"
                          >
                            <span>💬 Social listening CRM</span>
                            <span className="text-zinc-400">→</span>
                          </button>
                          <button 
                            onClick={() => setActiveTab("directories")}
                            className="w-full text-left flex items-center justify-between p-2 rounded-xl hover:bg-zinc-200 dark:hover:bg-zinc-800 border border-zinc-200/40 dark:border-white/[0.03]"
                          >
                            <span>📁 Submissions Center</span>
                            <span className="text-zinc-400">→</span>
                          </button>
                        </div>
                      </div>

                    </div>
                  </div>
                </div>
              )}

            </div>
          )}

          {/* TAB 2: SOCIAL LISTENING CRM */}
          {activeTab === "opportunities" && (
            <div className="space-y-10 animate-fadeIn">
              
              {/* CASE A: NO PRODUCT ONBOARDED */}
              {!product && (
                <div className="p-8 md:p-12 border border-dashed border-zinc-200/60 dark:border-white/[0.04] rounded-l-xlg text-center space-y-6 my-6">
                  <div className="text-zinc-300 dark:text-zinc-700 text-4xl">⚠️</div>
                  <h3 className="font-semibold text-zinc-800 dark:text-[#c4cad4]">Startup Onboarding Required</h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-xs mx-auto">
                    Please onboard your SaaS startup first in the <strong>Product Hub</strong> to enable custom intent mapping and database integrations!
                  </p>
                  <button 
                    onClick={() => setActiveTab("product")}
                    className="mt-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold px-4 py-1.5 rounded-xl text-sm transition-colors duration-300 ease-out"
                  >
                    Go to Product Hub
                  </button>
                </div>
              )}

              {/* CASE B: STARTUP ACTIVE */}
              {product && (
                <div className="space-y-10">
                  {/* Header Bar */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-zinc-200/60 dark:border-white/[0.04] pb-4">
                    <div className="space-y-1">
                      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-2">
                        👂 Social Intent CRM
                      </h1>
                      <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">
                        Scan Live Twitter, LinkedIn & Reddit communities for developer bottlenecks, review AI pitch drafts, and launch automated replies.
                      </p>
                    </div>
                    <div className="flex items-center p-1 bg-white dark:bg-[#14161C] border border-zinc-200/80 dark:border-white/[0.08] rounded-full shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
                      <div className="flex items-center pl-3 pr-2 pointer-events-none">
                        <span className="text-zinc-400 dark:text-[#6e7583] text-[11px]">#</span>
                      </div>
                      <input 
                        type="text"
                        placeholder="keyword..."
                        value={targetKeyword}
                        onChange={(e) => setTargetKeyword(e.target.value)}
                        className="bg-transparent text-xs text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none w-[90px] focus:w-[130px] transition-all duration-300 py-1"
                      />
                      
                      <div className="w-[1px] h-4 bg-zinc-200 dark:bg-white/[0.08] mx-2"></div>
                      
                      <button
                        onClick={handleScoutMock}
                        disabled={scoutLoading}
                        className="px-3 py-1.5 text-[11px] bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-200 font-bold rounded-full disabled:opacity-50 transition-all duration-300 ease-out flex items-center gap-1.5 shadow-sm"
                      >
                        {scoutLoading ? (
                          <span className="w-2.5 h-2.5 rounded-full border-2 border-zinc-500 border-t-transparent animate-spin"></span>
                        ) : "🔍"}
                        Scan
                      </button>
                      
                      <div className="w-[1px] h-4 bg-zinc-200 dark:bg-white/[0.08] mx-1"></div>
                      
                      <button
                        onClick={() => setShowAddLeadModal(true)}
                        className="px-3 py-1.5 text-[11px] text-zinc-600 dark:text-[#aab1be] hover:bg-zinc-100 dark:hover:bg-white/[0.04] font-bold rounded-full transition-all duration-300 ease-out flex items-center gap-1"
                      >
                        ➕ F5Bot
                      </button>
                    </div>
                  </div>

                  {/* Operational Metrics Cards */}
                  <div className="grid grid-cols-3 gap-6 text-center">
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-xl  font-bold text-zinc-900 dark:text-[#f8f9fa]">{leads.length}</div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Total Scouted</div>
                    </div>
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-xl  font-bold text-teal-500 dark:text-teal-300">
                        {leads.filter(l => l.status === "posted").length}
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Pitches Published</div>
                    </div>
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-xl  font-bold text-orange-500 dark:text-orange-400">
                        {leads.filter(l => l.status === "pending" || l.status === "failed").length}
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Pending Review</div>
                    </div>
                  </div>

                  {/* CRM Pipeline Feed */}
                  {scoutLoading ? (
                    <div className="p-12 border border-zinc-200/60 dark:border-white/[0.04] rounded-2xl bg-white dark:bg-[#14161C] text-center space-y-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-[1.01]">
                      <div className="relative w-16 h-16 mx-auto flex items-center justify-center">
                        <div className="absolute inset-0 rounded-full border-4 border-zinc-100 dark:border-white/[0.02]"></div>
                        <div className="absolute inset-0 rounded-full border-4 border-t-emerald-500 animate-[spin_1s_linear_infinite]"></div>
                        <div className="absolute inset-2 rounded-full border-4 border-b-cyan-500 animate-[spin_1.5s_linear_infinite_reverse]"></div>
                      </div>
                      <div className="space-y-3">
                        <h3 className="text-lg font-semibold text-zinc-900 dark:text-white flex items-center justify-center gap-2">
                          <span className="animate-pulse">⚡</span> Deploying AI Agents
                        </h3>
                        <p className="text-sm text-zinc-500 dark:text-zinc-400 max-w-sm mx-auto leading-relaxed">
                          Stealth scraping Reddit, Twitter, HackerNews, and LinkedIn. 
                          <br/><span className="text-emerald-600 dark:text-emerald-400 font-medium animate-pulse">Running Gemini 2.5 Flash intent analysis...</span>
                        </p>
                      </div>
                    </div>
                  ) : leadsLoading ? (
                    <div className="text-center py-12 text-zinc-400 text-sm">
                      Loading social CRM lists from database...
                    </div>
                  ) : leads.length === 0 ? (
                    <div className="p-12 border border-dashed border-zinc-200/60 dark:border-white/[0.04] rounded-xl text-center space-y-5">
                      <div className="text-3xl">📨</div>
                      <h4 className="font-semibold text-zinc-700 dark:text-[#aab1be] text-sm">Active Social Campaigns</h4>
                      <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-xs mx-auto">
                        No buyer intent leads stored. Click **Scout Forums** above to simulate automated monitoring or copy-paste alerts from F5Bot!
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {leads.map((lead) => (
                        <div 
                          key={lead.id} 
                          className="border border-zinc-200/60 dark:border-white/[0.08] rounded-[20px] bg-white dark:bg-[#0D0F12] overflow-hidden shadow-[0_4px_24px_rgba(0,0,0,0.03)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.06)] transition-all duration-500"
                        >
                          {/* Visible Card Summary */}
                          <div className="p-5 flex items-start justify-between gap-6">
                            <div className="space-y-1.5 flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className={`px-2 py-0.5 text-[9px] font-bold rounded-xl  tracking-wider ${
                                  lead.platform.toLowerCase() === "hackernews" 
                                    ? "bg-orange-100 dark:bg-orange-950/40 text-orange-850 dark:text-orange-350 border border-orange-200/20"
                                    : lead.platform.toLowerCase() === "linkedin"
                                    ? "bg-blue-100 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300 border border-blue-200/20"
                                    : "bg-red-100 dark:bg-red-950/30 text-red-800 dark:text-red-300 border border-red-200/20"
                                }`}>
                                  {lead.platform}
                                </span>
                                <span className={`px-2 py-0.5 text-[9px] font-bold rounded-xl  tracking-wider ${
                                  lead.status === "posted"
                                    ? "bg-teal-50 dark:bg-teal-950/30 text-teal-700 dark:text-emerald-300"
                                    : lead.status === "failed"
                                    ? "bg-red-100 dark:bg-red-950/30 text-red-800 dark:text-red-300"
                                    : "bg-zinc-100 dark:bg-white/[0.04] text-zinc-600 dark:text-[#8b919e]"
                                }`}>
                                  {lead.status}
                                </span>
                              </div>
                              <h3 className="font-semibold text-sm text-zinc-900 dark:text-[#f8f9fa] leading-snug">
                                {lead.thread_title}
                              </h3>
                              <a 
                                href={lead.source_url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-[11px]  text-zinc-405 dark:text-[#6e7583] hover:text-zinc-950 dark:hover:text-white underline truncate block"
                              >
                                {lead.source_url}
                              </a>
                            </div>
                            
                            {/* Actions column */}
                            <div className="flex flex-col gap-2 shrink-0">
                              {(lead.status === "pending" || lead.status === "failed") && (
                                <button
                                  onClick={() => handlePublishLeadReply(lead.id)}
                                  disabled={isPublishingLeadId === lead.id}
                                  className="px-3 py-1.5 text-sm bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold rounded-xl disabled:opacity-50 transition-all duration-300 ease-out flex items-center gap-1.5 shadow-sm"
                                >
                                  {isPublishingLeadId === lead.id ? (
                                    <>
                                      <span className="w-3.5 h-3.5 rounded-full border-2 border-zinc-500 border-t-transparent animate-spin"></span>
                                      Stealth Posting...
                                    </>
                                  ) : (
                                    <>Launch Reply</>
                                  )}
                                </button>
                              )}
                              
                              {lead.status === "posted" && lead.screenshot_url && (
                                <a
                                  href={`${API_URL}${lead.screenshot_url}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="px-3 py-1.5 text-sm border border-zinc-200/60 dark:border-white/[0.04] hover:bg-zinc-100 dark:hover:bg-zinc-850 font-semibold rounded-xl text-zinc-700 dark:text-[#aab1be] text-center block bg-white dark:bg-[#0F1115] shadow-sm"
                                >
                                  Screenshot Receipt 📸
                                </a>
                              )}
                            </div>
                          </div>
                          
                          {/* Inner Collapsible Block details */}
                          <div className="border-t border-zinc-150 dark:border-white/[0.04] p-5 bg-[#fafafa]/50 dark:bg-[#1b1b1a]/30 space-y-6">
                            {/* Intent Snippet */}
                            <div className="space-y-1.5">
                              <h4 className="text-[9px]  font-bold  tracking-wider text-zinc-400 dark:text-[#6e7583]">Customer Pain Point</h4>
                              <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-350 border-l-2 border-zinc-200/60 dark:border-white/[0.04] pl-3">
                                "{lead.context_snippet}"
                              </p>
                            </div>
                            
                            {/* AI Pitch response draft */}
                            <div className="space-y-1.5">
                              <h4 className="text-[9px]  font-bold  tracking-wider text-zinc-400 dark:text-[#6e7583]">Suggested Response</h4>
                              <div className="p-4 rounded-xl border border-zinc-200/60 dark:border-white/[0.04] bg-white dark:bg-[#1f1f1e]">
                                <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-350 font-sans whitespace-pre-wrap font-normal">
                                  {lead.draft_reply}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              )}

            </div>
          )}

          {/* TAB 3: DIRECTORIES SUBMISSIONS & SOCIAL PROMOTIONS */}
          {activeTab === "campaigns" && (
            <div className="space-y-10 animate-fadeIn">
              
              {/* CASE A: NO PRODUCT ONBOARDED */}
              {!product && (
                <div className="p-8 md:p-12 border border-dashed border-zinc-200/60 dark:border-white/[0.04] rounded-l-xlg text-center space-y-6 my-6">
                  <div className="text-zinc-300 dark:text-zinc-700 text-4xl">⚠️</div>
                  <h3 className="font-semibold text-zinc-800 dark:text-[#c4cad4]">Startup Onboarding Required</h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-xs mx-auto">
                    Please onboard your SaaS startup first in the <strong>Product Hub</strong> to enable automated launch kits and directory submitters.
                  </p>
                  <button 
                    onClick={() => setActiveTab("product")}
                    className="mt-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold px-4 py-1.5 rounded-xl text-sm transition-colors duration-300 ease-out"
                  >
                    Go to Product Hub
                  </button>
                </div>
              )}

              {/* CASE B: STARTUP ACTIVE */}
              {product && (
                <div className="space-y-10">
                  {/* Header Bar */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-zinc-200/60 dark:border-white/[0.04] pb-4">
                    <div className="space-y-1">
                      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-2">
                        📁 Launch & Submissions Center
                      </h1>
                      <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">
                        Autonomously register your startup on tech directories and schedule automated visual promotions to Twitter/Reddit.
                      </p>
                    </div>
                    
                    <button
                      onClick={handleSeedPipeline}
                      disabled={submissionsLoading || postsLoading}
                      className="px-3 py-1.5 text-sm bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold rounded-xl disabled:opacity-50 transition-all duration-300 ease-out flex items-center gap-1.5 shadow-sm"
                    >
                      {(submissionsLoading || postsLoading) ? (
                        <span className="w-3.5 h-3.5 rounded-full border-2 border-zinc-500 border-t-transparent animate-spin"></span>
                      ) : "✨"}
                      Generate & Initialize Launch Kit
                    </button>
                  </div>

                  {/* Operational Launch Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-xl  font-bold text-zinc-900 dark:text-[#f8f9fa]">
                        {submissions.filter(s => s.status === "submitted").length} / {submissions.length || 2}
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Directories Live</div>
                    </div>
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-xl  font-bold text-teal-500 dark:text-teal-300">
                        {posts.filter(p => p.platform !== "Dev.to" && p.status === "posted").length}
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Social Posts Live</div>
                    </div>
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-xl  font-bold text-orange-500 dark:text-orange-400">
                        {submissions.filter(s => s.status === "pending" || s.status === "failed").length}
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Pending Submissions</div>
                    </div>
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-xl  font-bold text-zinc-505 dark:text-[#8b919e]">
                        {posts.filter(p => p.platform !== "Dev.to" && p.status === "draft").length}
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Social Drafts</div>
                    </div>
                  </div>

                  {/* Dual Column Layout */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:p-10">
                    
                    {/* COLUMN 1: DIRECTORIES BOARD */}
                    <div className="space-y-6">
                      <div className="flex items-center justify-between border-b border-zinc-200/60 dark:border-white/[0.04] pb-2">
                        <h2 className="text-sm font-bold text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-1.5">
                          📂 Directory Auto-Submissions
                        </h2>
                        <span className="text-[9px]  font-bold text-zinc-400 bg-zinc-100 dark:bg-white/[0.04] px-2 py-0.5 rounded-xl">
                          Stealth Form Submitter
                        </span>
                      </div>
                      
                      {submissionsLoading ? (
                        <div className="text-center py-12 text-zinc-400  text-sm">
                          Fetching directory queues from DB...
                        </div>
                      ) : submissions.length === 0 ? (
                        <div className="p-8 md:p-12 border border-dashed border-zinc-200/60 dark:border-white/[0.04] rounded-xl text-center space-y-5 bg-[#fbfbfa]/30 dark:bg-[#171A21]/10">
                          <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-xs mx-auto">
                            Queue is uninitialized. Click **Generate & Initialize Launch Kit** above to seed ProductHunt and BetaList submission sheets.
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-5">
                          {(() => {
                            const ALL_DIRECTORIES = [
                              { name: "Product Hunt", url: "https://www.producthunt.com/posts/new" },
                              { name: "Hacker News (Show HN)", url: "https://news.ycombinator.com/submit" },
                              { name: "Indie Hackers", url: "https://www.indiehackers.com/products/new" },
                              { name: "AlternativeTo", url: "https://alternativeto.net/software/add/" },
                              { name: "G2", url: "https://www.g2.com/products/new" },
                              { name: "Capterra", url: "https://www.capterra.com/vendors/new" },
                              { name: "Trustpilot", url: "https://business.trustpilot.com/" },
                              { name: "Crunchbase", url: "https://www.crunchbase.com/add-new" },
                              { name: "Wellfound (AngelList)", url: "https://wellfound.com/companies/new" },
                              { name: "Dev.to", url: "https://dev.to/new" },
                              { name: "Betalist", url: "https://betalist.com/submit" },
                              { name: "SaaSHub", url: "https://www.saashub.com/submit" },
                              { name: "StartupStash", url: "https://startupstash.com/add-listing/" },
                              { name: "There's An AI For That", url: "https://theresanaiforthat.com/submit/" },
                              { name: "Futurepedia", url: "https://www.futurepedia.io/submit-tool" },
                              { name: "AI Tool Hunt", url: "https://www.aitoolhunt.com/submit" },
                              { name: "Toolify.ai", url: "https://www.toolify.ai/submit" },
                              { name: "Starter Story", url: "https://www.starterstory.com/join" },
                              { name: "StackShare", url: "https://stackshare.io/tools/new" },
                              { name: "Slant", url: "https://www.slant.co/topics/new" },
                              { name: "AppSumo", url: "https://sell.appsumo.com/" },
                              { name: "Uneed", url: "https://www.uneed.best/submit" },
                              { name: "Peerlist", url: "https://peerlist.io/projects/new" },
                              { name: "Microlaunch", url: "https://microlaunch.net/submit" },
                              { name: "1000 Tools", url: "https://1000.tools/submit" },
                              { name: "F6S", url: "https://www.f6s.com/" },
                              { name: "Software Advice", url: "https://www.softwareadvice.com/vendors/" },
                              { name: "GetApp", url: "https://www.getapp.com/vendors/" },
                              { name: "TrustRadius", url: "https://www.trustradius.com/vendor" },
                              { name: "SaaSWorthy", url: "https://www.saasworthy.com/add-product" },
                              { name: "SourceForge", url: "https://sourceforge.net/create/" },
                              { name: "GoodFirms", url: "https://www.goodfirms.co/add-company" },
                              { name: "Clutch", url: "https://clutch.co/get-listed" },
                              { name: "BetaPage", url: "https://betapage.co/submit" },
                              { name: "Launching Next", url: "https://www.launchingnext.com/submit/" },
                              { name: "StartupBuffer", url: "https://startupbuffer.com/submit" },
                              { name: "Hashnode", url: "https://hashnode.com/draft" },
                              { name: "TechCrunch (Pitch)", url: "https://techcrunch.com/pages/pitch/" },
                              { name: "Makerlog", url: "https://getmakerlog.com/" },
                              { name: "WIP.co", url: "https://wip.co/" },
                              { name: "PitchWall", url: "https://pitchwall.co/submit" },
                              { name: "CrazyAboutStartups", url: "https://crazyaboutstartups.com/submit-startup/" },
                              { name: "AI Valley", url: "https://aivalley.ai/submit-tool/" },
                              { name: "TopAI.tools", url: "https://topai.tools/submit" },
                              { name: "GPT Store", url: "https://chatgpt.com/gpts" },
                              { name: "AiTools.fyi", url: "https://aitools.fyi/submit" },
                              { name: "Tools.so", url: "https://tools.so/submit" },
                              { name: "StartupBase", url: "https://startupbase.io/submit" },
                              { name: "Startups.fyi", url: "https://www.startups.fyi/submit" },
                              { name: "Reddit r/SaaS", url: "https://www.reddit.com/r/SaaS/submit" },
                              { name: "Reddit r/SideProject", url: "https://www.reddit.com/r/SideProject/submit" },
                              { name: "Reddit r/Entrepreneur", url: "https://www.reddit.com/r/Entrepreneur/submit" },
                              { name: "Reddit r/Startups", url: "https://www.reddit.com/r/startups/submit" }
                            ];
                            
                            const planLimit = userPlan === "PRO" ? 53 : userPlan === "STARTER" ? 30 : 5;
                            
                            return ALL_DIRECTORIES.map((dir, idx) => {
                              const dbSub = submissions.find((s) => s.directory_name === dir.name);
                              const status = dbSub ? dbSub.status : "pending";
                              const screenshot_url = dbSub ? dbSub.screenshot_url : null;
                              const isLocked = idx >= planLimit;
                              
                              return (
                                <div 
                                  key={dir.name} 
                                  className={`p-4 border border-zinc-200/60 dark:border-white/[0.08] rounded-[20px] bg-white dark:bg-[#0D0F12] flex items-center justify-between gap-6 transition-all duration-500 ${isLocked ? "opacity-60" : "shadow-[0_4px_24px_rgba(0,0,0,0.03)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.06)]"}`}
                                >
                                  <div className={`min-w-0 flex-1 ${isLocked ? "blur-md select-none pointer-events-none opacity-50" : ""}`}>
                                    <div className="flex items-center gap-2">
                                      <span className="font-semibold text-sm text-zinc-950 dark:text-[#f8f9fa] flex items-center gap-2">
                                        {isLocked && <span className="text-xs">🔒</span>}
                                        {dir.name}
                                      </span>
                                      {!isLocked && (
                                        <span className={`px-2 py-0.5 text-[9px] font-bold rounded-xl  tracking-wider ${
                                          status === "submitted"
                                            ? "bg-teal-50 dark:bg-teal-950/30 text-teal-700 dark:text-emerald-300"
                                            : status === "failed"
                                            ? "bg-red-100 dark:bg-red-950/30 text-red-800 dark:text-red-300"
                                            : "bg-zinc-100 dark:bg-white/[0.04] text-zinc-600 dark:text-[#8b919e]"
                                        }`}>
                                          {status}
                                        </span>
                                      )}
                                    </div>
                                    <a 
                                      href={isLocked ? "#" : dir.url} 
                                      target={isLocked ? "_self" : "_blank"} 
                                      rel="noopener noreferrer" 
                                      className={`text-[10px] text-zinc-405 dark:text-[#6e7583] hover:text-zinc-950 dark:hover:text-white mt-1 block truncate ${!isLocked && "underline"}`}
                                    >
                                      {dir.url}
                                    </a>
                                  </div>
                                  
                                  <div>
                                    {isLocked ? (
                                      <button
                                        onClick={() => {
                                          setUpgradeMessage("Upgrade to Pro to unlock all 53 automated startup directories!");
                                          setShowUpgradeModal(true);
                                        }}
                                        className="px-3 py-1.5 text-xs bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40 font-semibold rounded-xl transition-all duration-300 ease-out border border-amber-200 dark:border-amber-900/50 flex items-center gap-1.5"
                                      >
                                        Upgrade to unlock
                                      </button>
                                    ) : (
                                      <>
                                        {(status === "pending" || status === "failed") && (
                                          <button
                                            onClick={() => window.open(dir.url, "_blank")}
                                            disabled={isSubmittingDirectoryName === dir.name}
                                            className="px-2.5 py-1.5 text-sm bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold rounded-xl disabled:opacity-50 transition-all duration-300 ease-out flex items-center gap-1 shadow-sm"
                                          >
                                            {isSubmittingDirectoryName === dir.name ? (
                                              <>
                                                <span className="w-3 h-3 rounded-full border-2 border-zinc-500 border-t-transparent animate-spin"></span>
                                                Submitting...
                                              </>
                                            ) : "Submit"}
                                          </button>
                                        )}
                                        {status === "submitted" && screenshot_url && (
                                          <a
                                            href={`${API_URL}${screenshot_url}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="px-2.5 py-1.5 text-sm border border-zinc-200/60 dark:border-white/[0.04] hover:bg-zinc-100 dark:hover:bg-zinc-850 font-semibold rounded-xl text-zinc-700 dark:text-[#aab1be] text-center block bg-white dark:bg-[#0F1115] shadow-sm"
                                          >
                                            Screenshot Receipt 📸
                                          </a>
                                        )}
                                      </>
                                    )}
                                  </div>
                                </div>
                              );
                            });
                          })()}
                        </div>
                      )}
                    </div>
                    
                    {/* COLUMN 2: SOCIAL DRAFTS */}
                    <div className="space-y-6">
                      <div className="flex items-center justify-between border-b border-zinc-200/60 dark:border-white/[0.04] pb-2">
                        <h2 className="text-sm font-bold text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-1.5">
                          📢 Launch Copy Promos
                        </h2>
                        <span className="text-[9px]  font-bold text-zinc-400 bg-zinc-100 dark:bg-white/[0.04] px-2 py-0.5 rounded-xl">
                          AI Social Copywriter
                        </span>
                      </div>
                      
                      {postsLoading ? (
                        <div className="text-center py-12 text-zinc-400  text-sm">
                          Fetching social drafts from DB...
                        </div>
                      ) : posts.filter(p => p.platform !== "Dev.to").length === 0 ? (
                        <div className="p-8 md:p-12 border border-dashed border-zinc-200/60 dark:border-white/[0.04] rounded-xl text-center space-y-5 bg-[#fbfbfa]/30 dark:bg-[#171A21]/10">
                          <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-xs mx-auto">
                            No promotional social posts drafted yet. Click **Generate & Initialize Launch Kit** above to trigger Gemini value-story templates.
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-6">
                          {posts.filter(p => p.platform !== "Dev.to").map((post) => (
                            <div 
                              key={post.id} 
                              className="border border-zinc-200/60 dark:border-white/[0.08] rounded-[20px] bg-white dark:bg-[#0D0F12] overflow-hidden shadow-[0_4px_24px_rgba(0,0,0,0.03)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.06)] transition-all duration-500"
                            >
                              <div className="p-3.5 flex items-center justify-between gap-6 border-b border-zinc-150 dark:border-white/[0.04] bg-[#fafafa]/50 dark:bg-[#1b1b1a]/30">
                                <div className="flex items-center gap-2">
                                  <span className={`px-2 py-0.5 text-[9px] font-bold rounded-xl  tracking-wider ${
                                    post.platform.toLowerCase() === "twitter"
                                      ? "bg-sky-100 dark:bg-sky-950/40 text-sky-850 dark:text-sky-350 border border-sky-200/20"
                                      : "bg-orange-100 dark:bg-orange-950/40 text-orange-850 dark:text-orange-350 border border-orange-200/20"
                                  }`}>
                                    {post.platform}
                                  </span>
                                  <span className={`px-2 py-0.5 text-[9px] font-bold rounded-xl  tracking-wider ${
                                    post.status === "posted"
                                      ? "bg-teal-50 dark:bg-teal-950/30 text-teal-700 dark:text-emerald-300"
                                      : post.status === "failed"
                                      ? "bg-red-100 dark:bg-red-950/30 text-red-800 dark:text-red-300"
                                      : "bg-zinc-100 dark:bg-white/[0.04] text-zinc-600 dark:text-[#8b919e]"
                                  }`}>
                                    {post.status}
                                  </span>
                                </div>
                                
                                <div>
                                  {(post.status === "draft" || post.status === "failed") && (
                                    <button
                                      onClick={() => handlePublishSocialPost(post.id)}
                                      disabled={isPublishingPostId === post.id}
                                      className="px-2.5 py-1 text-sm bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold rounded-xl disabled:opacity-50 transition-all duration-300 ease-out flex items-center gap-1 shadow-sm"
                                    >
                                      {isPublishingPostId === post.id ? (
                                        <>
                                          <span className="w-3 h-3 rounded-full border-2 border-zinc-500 border-t-transparent animate-spin"></span>
                                          Broadcasting...
                                        </>
                                      ) : "Copy & Post"}
                                    </button>
                                  )}
                                  {post.status === "posted" && post.screenshot_url && (
                                    <a
                                      href={`${API_URL}${post.screenshot_url}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="px-2.5 py-1 text-sm border border-zinc-200/60 dark:border-white/[0.04] hover:bg-zinc-100 dark:hover:bg-zinc-850 font-semibold rounded-xl text-zinc-700 dark:text-[#aab1be] block bg-white dark:bg-[#0F1115] shadow-sm"
                                    >
                                      View Receipt 📸
                                    </a>
                                  )}
                                </div>
                              </div>
                              <div className="p-4">
                                <p className="text-sm leading-relaxed text-zinc-650 dark:text-zinc-350 font-sans whitespace-pre-wrap font-normal">
                                  {post.content}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                  </div>
                </div>
              )}

            </div>
          )}

          {/* TAB 4: SEO BLOG STUDIO */}
          {activeTab === "recommendations" && (
            <div className="space-y-10 animate-fadeIn">
              
              {/* CASE A: NO PRODUCT ONBOARDED */}
              {!product && (
                <div className="p-8 md:p-12 border border-dashed border-zinc-200/60 dark:border-white/[0.04] rounded-l-xlg text-center space-y-6 my-6">
                  <div className="text-zinc-300 dark:text-zinc-700 text-4xl">⚠️</div>
                  <h3 className="font-semibold text-zinc-800 dark:text-[#c4cad4]">Startup Onboarding Required</h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-xs mx-auto">
                    Please onboard your SaaS startup first in the <strong>Product Hub</strong> to enable custom SEO keyword tracking and blog engines.
                  </p>
                  <button 
                    onClick={() => setActiveTab("product")}
                    className="mt-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold px-4 py-1.5 rounded-xl text-sm transition-colors duration-300 ease-out"
                  >
                    Go to Product Hub
                  </button>
                </div>
              )}

              {/* CASE B: STARTUP ACTIVE */}
              {product && (
                <div className="space-y-10">
                  {/* Header Bar */}
                  <div className="flex items-center justify-between border-b border-zinc-200/60 dark:border-white/[0.04] pb-4">
                    <div className="space-y-1">
                      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-2">
                        ✍️ SEO Blog Studio
                      </h1>
                      <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">
                        Target high-intent B2B keywords, trigger AI articles with natural HTML backlink weaves, and launch stealth publishing agents.
                      </p>
                    </div>
                  </div>

                  {/* Premium Two-Column Workspace Layout */}
                  <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 md:px-8 pb-10">
                    
                    {/* LEFT PANEL: KEYWORDS & LIBRARY (4 Columns) */}
                    <div className="xl:col-span-4 flex flex-col space-y-8">
                      
                      {/* Section Header */}
                      <div className="flex items-center gap-3">
                        <div className="h-px bg-zinc-200 dark:bg-white/[0.06] flex-1"></div>
                        <span className="text-[10px] font-bold tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Strategy & Library</span>
                        <div className="h-px bg-zinc-200 dark:bg-white/[0.06] flex-1"></div>
                      </div>

                      {/* 1. Keyword Planner Glass Card */}
                      <div className="p-6 rounded-2xl bg-white/70 dark:bg-[#0A0B0E]/70 backdrop-blur-2xl border border-zinc-200/80 dark:border-white/[0.06] shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)] flex flex-col gap-6 relative overflow-hidden group hover:shadow-[0_12px_40px_rgb(0,0,0,0.08)] transition-all duration-500">
                        {/* Top Gradient Accent */}
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-zinc-800 to-zinc-400 dark:from-zinc-200 dark:to-zinc-600 opacity-80"></div>
                        
                        <div className="space-y-1">
                          <h3 className="text-base font-semibold text-zinc-900 dark:text-white tracking-tight">Target Focus Keywords</h3>
                          <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">Add high-intent keywords to weave seamlessly into your technical articles.</p>
                        </div>
                        
                        {/* Keyword Pills */}
                        <div className="flex flex-wrap gap-2">
                          {keywords.map((kw, idx) => (
                            <span 
                              key={idx}
                              className="px-3 py-1.5 text-xs bg-zinc-100 dark:bg-[#15171C] border border-zinc-200/60 dark:border-white/[0.04] text-zinc-700 dark:text-zinc-300 rounded-full flex items-center gap-2 font-medium shadow-sm group/pill hover:bg-zinc-200 dark:hover:bg-[#1A1C23] transition-colors"
                            >
                              {kw}
                              <button 
                                onClick={() => setKeywords(prev => prev.filter((_, i) => i !== idx))}
                                className="text-zinc-400 hover:text-red-500 opacity-60 group-hover/pill:opacity-100 transition-all focus:outline-none"
                              >
                                ✕
                              </button>
                            </span>
                          ))}
                        </div>

                        {/* Keyword input form */}
                        <form 
                          onSubmit={(e) => {
                            e.preventDefault();
                            if (newKeyword.trim() && !keywords.includes(newKeyword.trim())) {
                              setKeywords(prev => [...prev, newKeyword.trim()]);
                              setNewKeyword("");
                            }
                          }}
                          className="flex gap-2"
                        >
                          <input 
                            type="text"
                            placeholder="Add keyword tag..."
                            value={newKeyword}
                            onChange={(e) => setNewKeyword(e.target.value)}
                            className="flex-1 px-3 py-2 border border-zinc-200 dark:border-white/[0.08] bg-white dark:bg-[#0A0B0E] rounded-xl outline-none text-sm text-zinc-900 dark:text-white focus:ring-2 focus:ring-zinc-900/10 dark:focus:ring-white/10 transition-all placeholder:text-zinc-400"
                          />
                          <button 
                            type="submit"
                            className="px-4 py-2 border border-zinc-200 dark:border-white/[0.08] hover:bg-zinc-50 dark:hover:bg-[#15171C] font-semibold rounded-xl text-sm text-zinc-700 dark:text-zinc-300 bg-white dark:bg-[#0A0B0E] shadow-sm transition-colors"
                          >
                            Add
                          </button>
                        </form>

                        {/* Premium Primary CTA */}
                        <button
                          onClick={handleGenerateBlog}
                          disabled={isGeneratingBlog}
                          className="relative w-full py-3 bg-gradient-to-b from-zinc-800 to-zinc-900 dark:from-zinc-100 dark:to-zinc-300 text-white dark:text-zinc-900 font-semibold rounded-xl text-sm shadow-[0_4px_14px_0_rgb(0,0,0,0.1)] dark:shadow-[0_4px_14px_0_rgb(255,255,255,0.1)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.15)] dark:hover:shadow-[0_6px_20px_rgba(255,255,255,0.2)] hover:-translate-y-0.5 transition-all duration-300 ease-out flex items-center justify-center gap-2 disabled:opacity-70 disabled:hover:translate-y-0"
                        >
                          {isGeneratingBlog ? (
                            <>
                              <span className="w-4 h-4 rounded-full border-2 border-white/20 dark:border-zinc-900/20 border-t-white dark:border-t-zinc-900 animate-spin"></span>
                              Drafting Article...
                            </>
                          ) : (
                            <>Generate Tech Blog Post ✨</>
                          )}
                        </button>
                      </div>

                      {/* 2. Article Library Elevated Card */}
                      <div className="p-6 rounded-2xl bg-white dark:bg-[#0D0F12] border border-zinc-200/80 dark:border-white/[0.06] shadow-sm flex flex-col gap-5 flex-1">
                        <div className="flex items-center justify-between">
                          <div className="space-y-1">
                            <h3 className="text-base font-semibold text-zinc-900 dark:text-white tracking-tight">Articles Library</h3>
                            <p className="text-xs text-zinc-500 dark:text-zinc-400">Your generated developer guides.</p>
                          </div>
                          <button
                            onClick={() => setShowDeleteAllModal(true)}
                            className="text-xs text-red-500 hover:text-red-600 bg-red-50 hover:bg-red-100 dark:bg-red-500/10 dark:hover:bg-red-500/20 px-3 py-1.5 rounded-lg transition-colors font-medium border border-red-100 dark:border-red-500/20"
                            title="Delete all drafts"
                          >
                            Delete All
                          </button>
                        </div>
                        
                        {postsLoading ? (
                          <div className="text-center py-8 text-zinc-400 text-sm animate-pulse">
                            Loading library...
                          </div>
                        ) : posts.filter(p => p.platform === "Dev.to").length === 0 ? (
                          <div className="p-6 border border-dashed border-zinc-200/80 dark:border-white/[0.06] rounded-xl text-center text-sm text-zinc-500 dark:text-zinc-400 bg-zinc-50/50 dark:bg-[#12141A]/50">
                            No articles drafted yet.
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {posts.filter(p => p.platform === "Dev.to").map((post) => {
                              let titleText = "B2B Tech Guide Draft";
                              if (post.content.startsWith("Title:")) {
                                const idx = post.content.indexOf("\n\n");
                                if (idx !== -1) {
                                  titleText = post.content.substring(0, idx).replace("Title: ", "").trim();
                                }
                              }
                              
                              const isSelected = selectedBlog && selectedBlog.id === post.id;
                              
                              return (
                                <button
                                  key={post.id}
                                  onClick={() => setSelectedBlog(post)}
                                  className={`w-full text-left p-4 rounded-xl flex items-center justify-between gap-3 transition-all duration-300 ease-out shadow-sm group ${
                                    isSelected 
                                      ? "border-transparent bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 ring-4 ring-zinc-900/10 dark:ring-white/10 scale-[1.02]"
                                      : "border border-zinc-200/80 dark:border-white/[0.06] bg-white dark:bg-[#12141A] hover:bg-zinc-50 dark:hover:bg-[#1A1C23] text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-white/[0.1]"
                                  }`}
                                >
                                  <div className="min-w-0 flex-1">
                                    <h4 className={`font-medium text-sm truncate leading-snug ${isSelected ? "text-white dark:text-zinc-900 font-semibold" : ""}`}>
                                      {titleText}
                                    </h4>
                                    <span className={`text-[10px] mt-1 block ${isSelected ? "text-zinc-300 dark:text-zinc-600" : "text-zinc-400 dark:text-zinc-500"}`}>
                                      Platform: Dev.to
                                    </span>
                                  </div>
                                  <span className={`px-2 py-0.5 text-[9px] font-bold rounded-lg tracking-wider shrink-0 ${
                                    post.status === "posted"
                                      ? (isSelected ? "bg-white/20 dark:bg-zinc-900/10 text-white dark:text-zinc-900" : "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/30 dark:border-teal-800/30")
                                      : (isSelected ? "bg-white/20 dark:bg-zinc-900/10 text-white dark:text-zinc-900" : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400")
                                  }`}>
                                    {post.status}
                                  </span>
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>

                    </div>

                    {/* RIGHT PANEL: DISTRACTION-FREE READ PANE (8 Columns) */}
                    <div className="xl:col-span-8 flex flex-col h-full space-y-8">
                      
                      {/* Section Header */}
                      <div className="flex items-center gap-3">
                        <div className="h-px bg-zinc-200 dark:bg-white/[0.06] flex-1"></div>
                        <span className="text-[10px] font-bold tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Review & Publish</span>
                        <div className="h-px bg-zinc-200 dark:bg-white/[0.06] flex-1"></div>
                      </div>

                      {isGeneratingBlog ? (
                        <div className="flex-1 min-h-[500px] p-10 rounded-2xl border border-zinc-200/80 dark:border-white/[0.08] bg-white dark:bg-[#0D0F12] shadow-sm flex flex-col items-center justify-center text-center relative overflow-hidden group">
                          {/* Animated concentric rings */}
                          <div className="relative w-24 h-24 mx-auto flex items-center justify-center mb-8">
                            <div className="absolute inset-0 rounded-full border-4 border-zinc-100 dark:border-white/[0.02]"></div>
                            <div className="absolute inset-0 rounded-full border-4 border-t-indigo-500 animate-[spin_1s_linear_infinite]"></div>
                            <div className="absolute inset-2 rounded-full border-4 border-b-purple-500 animate-[spin_1.5s_linear_infinite_reverse]"></div>
                            <div className="absolute inset-4 rounded-full border-4 border-l-pink-500 animate-[spin_2s_linear_infinite]"></div>
                            <span className="text-3xl animate-bounce">✍️</span>
                          </div>
                          
                          <h4 className="font-semibold text-zinc-900 dark:text-white text-xl tracking-tight mb-3 flex items-center justify-center gap-2">
                            <span className="animate-pulse text-indigo-500">⚡</span> Gemini 3.5 Flash is Drafting...
                          </h4>
                          <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-md mx-auto">
                            Our AI agent is currently synthesizing market data, structuring high-converting HTML backlinks, and weaving your target keywords into a technical B2B article.
                          </p>
                          
                          {/* Animated Skeleton Wireframe */}
                          <div className="w-full max-w-md mt-10 space-y-4 opacity-50">
                            <div className="h-6 bg-zinc-200 dark:bg-white/[0.08] rounded w-1/2 mx-auto animate-pulse"></div>
                            <div className="space-y-2 pt-2">
                              <div className="h-3 bg-zinc-100 dark:bg-white/[0.04] rounded w-full animate-pulse" style={{ animationDelay: "100ms" }}></div>
                              <div className="h-3 bg-zinc-100 dark:bg-white/[0.04] rounded w-11/12 mx-auto animate-pulse" style={{ animationDelay: "200ms" }}></div>
                              <div className="h-3 bg-zinc-100 dark:bg-white/[0.04] rounded w-4/5 mx-auto animate-pulse" style={{ animationDelay: "300ms" }}></div>
                            </div>
                            <div className="space-y-2 pt-4">
                              <div className="h-3 bg-zinc-100 dark:bg-white/[0.04] rounded w-full animate-pulse" style={{ animationDelay: "400ms" }}></div>
                              <div className="h-3 bg-zinc-100 dark:bg-white/[0.04] rounded w-5/6 mx-auto animate-pulse" style={{ animationDelay: "500ms" }}></div>
                            </div>
                          </div>
                        </div>
                      ) : !selectedBlog ? (
                        /* Polished Onboarding State */
                        <div className="flex-1 min-h-[500px] p-10 rounded-2xl border border-dashed border-zinc-200/80 dark:border-white/[0.08] bg-zinc-50/50 dark:bg-zinc-900/10 flex flex-col items-center justify-center text-center relative overflow-hidden group">
                          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjEiIGZpbGw9InJnYmEoMTUwLDE1MCwxNTAsMC4xNSkiLz48L3N2Zz4=')] [mask-image:linear-gradient(to_bottom,white,transparent)]"></div>
                          
                          <div className="relative z-10 w-20 h-20 mb-6 rounded-2xl bg-white dark:bg-[#12141A] border border-zinc-200 dark:border-white/[0.06] shadow-lg flex items-center justify-center transform -rotate-3 group-hover:rotate-0 transition-all duration-500">
                            <span className="text-3xl">📖</span>
                          </div>
                          
                          <h4 className="font-semibold text-zinc-900 dark:text-white text-lg tracking-tight mb-2">Notion Distraction-Free Reader</h4>
                          <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-sm mx-auto">
                            Select an article from your library to review the draft, verify embedded HTML backlinks, and publish seamlessly with one click.
                          </p>
                        </div>
                      ) : (
                        (() => {
                          let blogTitle = "Technical Article Draft";
                          let blogBody = selectedBlog.content;
                          if (selectedBlog.content.startsWith("Title:")) {
                            const firstSplitIdx = selectedBlog.content.indexOf("\n\n");
                            if (firstSplitIdx !== -1) {
                              blogTitle = selectedBlog.content.substring(0, firstSplitIdx).replace("Title: ", "").trim();
                              blogBody = selectedBlog.content.substring(firstSplitIdx).trim();
                            }
                          }
                          
                          return (
                            <div className="flex-1 p-8 md:p-12 border border-zinc-200/80 dark:border-white/[0.08] rounded-2xl bg-white dark:bg-[#0D0F12] shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)] transition-all duration-500 flex flex-col h-full relative overflow-hidden group">
                              
                              {/* Metadata & Publisher actions header */}
                              <div className="flex items-center justify-between border-b border-zinc-100 dark:border-white/[0.04] pb-6 mb-8 flex-wrap gap-4 relative z-50">
                                <div className="space-y-1.5">
                                  <div className="text-[10px] font-bold tracking-widest text-zinc-400 dark:text-zinc-500 uppercase">Notion Workspace Sheet</div>
                                  <div className="flex items-center gap-2">
                                    <span className="px-2.5 py-1 text-[10px] font-semibold rounded-lg bg-zinc-100 dark:bg-[#15171C] text-zinc-600 dark:text-zinc-400 border border-zinc-200/60 dark:border-white/[0.04]">
                                      Platform: Dev.to
                                    </span>
                                    <span className={`px-2.5 py-1 text-[10px] font-bold rounded-lg tracking-wider ${
                                      selectedBlog.status.includes("posted")
                                        ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/30 dark:border-teal-800/30"
                                        : "bg-zinc-100 dark:bg-[#15171C] text-zinc-600 dark:text-zinc-400 border border-zinc-200/60 dark:border-white/[0.04]"
                                    }`}>
                                      {selectedBlog.status === "posted_both" ? "POSTED (BOTH)" : selectedBlog.status === "posted_devto" ? "POSTED (DEV.TO)" : selectedBlog.status === "posted_linkedin" ? "POSTED (LINKEDIN)" : selectedBlog.status}
                                    </span>
                                  </div>
                                </div>
                                
                                <div>
                                  <div className="flex gap-2 items-center">
                                    {selectedBlog.status.includes("posted") && (
                                      <div className="px-4 py-2.5 text-sm border border-teal-200 dark:border-teal-900/50 font-semibold rounded-xl text-teal-700 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/30 flex items-center gap-2">
                                        <svg className="w-4 h-4 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                                        Published to {selectedBlog.status === "posted_both" ? "Both" : selectedBlog.status === "posted_devto" ? "Dev.to" : "LinkedIn"}
                                      </div>
                                    )}
                                    
                                    <button
                                      onClick={() => {
                                        navigator.clipboard.writeText(`# ${blogTitle}\n\n${blogBody}`);
                                        alert("Blog copied to clipboard!");
                                      }}
                                      className="px-5 py-2.5 text-sm bg-zinc-100 dark:bg-[#1C1F26] text-zinc-900 dark:text-white hover:bg-zinc-200 dark:hover:bg-[#262A34] font-semibold rounded-xl transition-all duration-300 ease-out flex items-center gap-2"
                                    >
                                      Copy
                                    </button>
                                    
                                    {selectedBlog.status !== "posted_both" && (
                                      <div className="relative group/dropdown">
                                        <button
                                          disabled={isGeneratingBlog}
                                          className="px-5 py-2.5 text-sm bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold rounded-xl disabled:opacity-50 transition-all duration-300 ease-out flex items-center gap-2 shadow-[0_2px_10px_rgba(0,0,0,0.08)] dark:shadow-[0_2px_10px_rgba(255,255,255,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] hover:-translate-y-0.5"
                                        >
                                          {isGeneratingBlog ? (
                                            <>
                                              <span className="w-4 h-4 rounded-full border-2 border-white/20 dark:border-zinc-900/20 border-t-white dark:border-t-zinc-900 animate-spin"></span>
                                              Publishing...
                                            </>
                                          ) : (
                                            <>
                                              Publish
                                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                                            </>
                                          )}
                                        </button>
                                        
                                        {/* Dropdown Menu Wrapper (pt-2 creates safe hover bridge) */}
                                        <div className="absolute right-0 top-full pt-2 w-56 opacity-0 invisible group-hover/dropdown:opacity-100 group-hover/dropdown:visible transition-all duration-200 z-50">
                                          <div className="bg-white dark:bg-[#12141A] border border-zinc-200 dark:border-white/[0.06] rounded-xl shadow-xl overflow-hidden translate-y-1 group-hover/dropdown:translate-y-0 transition-transform duration-200">
                                            {!selectedBlog.status.includes("devto") && (
                                              <button 
                                                onClick={() => handlePublishBlog(selectedBlog.id, "dev.to")}
                                                className="w-full text-left px-4 py-3 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-white/[0.03] transition-colors flex items-center gap-3"
                                              >
                                                <span className="w-5 h-5 flex items-center justify-center bg-zinc-900 text-white rounded font-bold text-[10px]">DEV</span>
                                                Publish to Dev.to
                                              </button>
                                            )}
                                            {!selectedBlog.status.includes("linkedin") && (
                                              <button 
                                                onClick={() => handlePublishBlog(selectedBlog.id, "linkedin")}
                                                className="w-full text-left px-4 py-3 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-white/[0.03] transition-colors flex items-center gap-3 border-t border-zinc-100 dark:border-white/[0.04]"
                                              >
                                                <span className="w-5 h-5 flex items-center justify-center bg-[#0a66c2] text-white rounded font-bold text-[10px]">in</span>
                                                Publish to LinkedIn
                                              </button>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                              
                              {/* Title & Body */}
                              <div className="flex-1 space-y-8 overflow-y-auto pr-4 custom-scrollbar relative z-10 pb-8">
                                <h2 className="text-2xl md:text-3xl font-extrabold text-zinc-900 dark:text-white leading-tight font-sans tracking-tight">
                                  {blogTitle}
                                </h2>
                                
                                <div className="prose prose-zinc dark:prose-invert max-w-none text-base leading-relaxed text-zinc-700 dark:text-zinc-300 font-sans whitespace-pre-wrap selection:bg-zinc-900 selection:text-white dark:selection:bg-white dark:selection:text-zinc-900">
                                  {blogBody}
                                </div>
                              </div>

                            </div>
                          );
                        })()
                      )}
                      
                    </div>

                  </div>
                </div>
              )}

            </div>
          )}

          {/* TAB 5: ANALYTICS & SETTINGS */}
          {activeTab === "analytics" && (
            <div className="space-y-10 animate-fadeIn">
              
              {/* CASE A: NO PRODUCT ONBOARDED */}
              {!product && (
                <div className="p-8 md:p-12 border border-dashed border-zinc-200/60 dark:border-white/[0.04] rounded-l-xlg text-center space-y-6 my-6">
                  <div className="text-zinc-300 dark:text-zinc-700 text-4xl">⚠️</div>
                  <h3 className="font-semibold text-zinc-800 dark:text-[#c4cad4]">Startup Onboarding Required</h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-xs mx-auto">
                    Please onboard your SaaS startup first in the <strong>Product Hub</strong> to access unified marketing metrics and activity logs.
                  </p>
                  <button 
                    onClick={() => setActiveTab("product")}
                    className="mt-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold px-4 py-1.5 rounded-xl text-sm transition-colors duration-300 ease-out"
                  >
                    Go to Product Hub
                  </button>
                </div>
              )}

              {/* CASE B: STARTUP ACTIVE */}
              {product && summaryLoading && !summaryData && (
                <div className="text-center py-12 text-zinc-400  text-sm">
                  Aggregating operations data from backend...
                </div>
              )}

              {product && summaryData && (
                <div className="space-y-10">
                  {/* Header Bar */}
                  <div className="flex items-center justify-between border-b border-zinc-200/60 dark:border-white/[0.04] pb-4">
                    <div className="space-y-1">
                      <h1 className="text-xl font-medium text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-2">
                        📊 Operations & Metrics
                      </h1>
                      <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">
                        Unified tracking of all AI agent activities, funnel conversions, and platform integrations.
                      </p>
                    </div>
                  </div>

                  {/* 4-Card Top Level KPI Row */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-2xl  font-bold text-zinc-900 dark:text-[#f8f9fa]">
                        {summaryData.stats.directories.total}
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Directory Submissions</div>
                    </div>
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-2xl  font-bold text-teal-500 dark:text-teal-300">
                        {summaryData.stats.leads.contacted}
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Leads Contacted</div>
                    </div>
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-2xl  font-bold text-sky-500 dark:text-sky-400">
                        {summaryData.stats.roi.clicks}
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Total Tracked Clicks</div>
                    </div>
                    <div className="p-4 border border-zinc-200/60 dark:border-white/[0.03] rounded-xl bg-[#fbfbfa] dark:bg-[#171A21] shadow-sm">
                      <div className="text-2xl  font-bold text-orange-500 dark:text-orange-400">
                        {summaryData.stats.roi.conversion_rate_percentage}%
                      </div>
                      <div className="text-[9px] text-zinc-405 dark:text-[#6e7583]  font-bold  tracking-wider mt-1">Conversion Rate</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:p-10">
                    
                    {/* LEFT PANEL: ACTIVITY FEED */}
                    <div className="space-y-6">
                      <div className="flex items-center justify-between border-b border-zinc-200/60 dark:border-white/[0.04] pb-2">
                        <h2 className="text-sm font-bold text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-1.5">
                          📡 Real-time Agent Log
                        </h2>
                      </div>
                      
                      <div className="border border-zinc-200/80 dark:border-white/[0.06] rounded-2xl bg-white dark:bg-[#14161C] overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 h-[400px] overflow-y-auto custom-scrollbar">
                        <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
                          {summaryData.activity_feed.map((action: any) => (
                            <div key={action.id} className="p-4 hover:bg-zinc-50 dark:hover:bg-[#252525] transition-colors duration-300 ease-out">
                              <div className="flex items-center justify-between mb-1.5">
                                <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                                  action.agent.includes("SEO") ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400" :
                                  action.agent.includes("Directory") ? "bg-purple-100 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400" :
                                  action.agent.includes("Scout") ? "bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400" :
                                  "bg-zinc-100 text-zinc-600 dark:bg-white/[0.06] dark:text-zinc-400"
                                }`}>
                                  {action.agent}
                                </span>
                              </div>
                              <p className="text-sm text-zinc-700 dark:text-[#aab1be] leading-relaxed mt-2">
                                {action.message}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    {/* RIGHT PANEL: BREAKDOWN CHARTS & STATUS */}
                    <div className="space-y-6">
                      <div className="flex items-center justify-between border-b border-zinc-200/60 dark:border-white/[0.04] pb-2">
                        <h2 className="text-sm font-bold text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-1.5">
                          🛠️ System Sub-Tasks
                        </h2>
                      </div>
                      
                      <div className="grid grid-cols-1 gap-3">
                        <div className="p-4 border border-zinc-200/60 dark:border-white/[0.04] rounded-xl flex justify-between items-center shadow-sm">
                          <div className="text-sm font-semibold text-zinc-700 dark:text-[#aab1be]">SEO Articles Drafted</div>
                          <div className="text-sm  font-bold text-zinc-900 dark:text-[#f8f9fa] bg-zinc-100 dark:bg-white/[0.04] px-2 py-0.5 rounded-xl">
                            {summaryData.stats.blogs.total}
                          </div>
                        </div>
                        <div className="p-4 border border-zinc-200/60 dark:border-white/[0.04] rounded-xl flex justify-between items-center shadow-sm">
                          <div className="text-sm font-semibold text-zinc-700 dark:text-[#aab1be]">Competitors Tracked</div>
                          <div className="text-sm  font-bold text-zinc-900 dark:text-[#f8f9fa] bg-zinc-100 dark:bg-white/[0.04] px-2 py-0.5 rounded-xl">
                            {summaryData.stats.competitors_tracked}
                          </div>
                        </div>
                        <div className="p-4 border border-zinc-200/60 dark:border-white/[0.04] rounded-xl flex justify-between items-center shadow-sm">
                          <div className="text-sm font-semibold text-zinc-700 dark:text-[#aab1be]">Active Sequences</div>
                          <div className="text-sm  font-bold text-zinc-900 dark:text-[#f8f9fa] bg-zinc-100 dark:bg-white/[0.04] px-2 py-0.5 rounded-xl">
                            {summaryData.stats.active_sequences}
                          </div>
                        </div>
                        <div className="p-4 border border-zinc-200/60 dark:border-white/[0.04] rounded-xl flex justify-between items-center shadow-sm">
                          <div className="text-sm font-semibold text-zinc-700 dark:text-[#aab1be]">Total Customer Conversions</div>
                          <div className="text-sm  font-bold text-zinc-900 dark:text-[#f8f9fa] bg-zinc-100 dark:bg-white/[0.04] px-2 py-0.5 rounded-xl">
                            {summaryData.stats.roi.conversions}
                          </div>
                        </div>
                      </div>
                      
                    </div>

                  </div>
                </div>
              )}

            </div>
          )}

          {/* TAB 6: ACCOUNT SETTINGS */}
          {activeTab === "settings" && (
            <div className="space-y-10 animate-fadeIn max-w-4xl mx-auto w-full">
              <div className="space-y-1">
                <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Account Settings</h1>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">Manage your profile, preferences, and workspace settings.</p>
              </div>

              <div className="grid grid-cols-1 gap-8">
                {/* Profile Card */}
                <div className="bg-white dark:bg-[#0D0F12] border border-zinc-200/60 dark:border-white/[0.06] rounded-[24px] overflow-hidden shadow-sm">
                  <div className="p-8 space-y-8">
                    <h3 className="text-lg font-semibold text-zinc-900 dark:text-white border-b border-zinc-100 dark:border-white/[0.04] pb-4">Personal Profile</h3>
                    
                    <div className="flex items-center gap-6">
                      <div className="w-20 h-20 rounded-full border border-zinc-200 dark:border-white/[0.08] shadow-sm overflow-hidden flex items-center justify-center shrink-0">
                        {user?.image ? (
                          <img src={user.image} alt="Profile" className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full bg-emerald-500 text-white flex items-center justify-center text-3xl font-bold">
                            {user?.name?.charAt(0) || user?.email?.charAt(0) || "U"}
                          </div>
                        )}
                      </div>
                      <div className="space-y-1">
                        <button className="px-4 py-2 text-sm font-medium border border-zinc-200/80 dark:border-white/[0.08] bg-zinc-50 dark:bg-white/[0.02] hover:bg-zinc-100 dark:hover:bg-white/[0.04] rounded-xl transition-colors">
                          Change Avatar
                        </button>
                        <p className="text-xs text-zinc-500 mt-2">JPG, GIF or PNG. 1MB max.</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
                      <div className="space-y-2">
                        <label className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 ml-1">Full Name</label>
                        <input 
                          type="text" 
                          defaultValue={user?.name || ""} 
                          className="w-full px-4 py-3 bg-zinc-50 dark:bg-[#141417] border border-zinc-200/80 dark:border-white/[0.04] rounded-xl focus:outline-none focus:ring-2 focus:ring-zinc-900/10 dark:focus:ring-white/10 transition-all text-sm"
                          placeholder="Your name"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 ml-1">Email Address</label>
                        <input 
                          type="email" 
                          disabled
                          defaultValue={user?.email || ""} 
                          className="w-full px-4 py-3 bg-zinc-100 dark:bg-[#111113] border border-zinc-200/50 dark:border-white/[0.02] rounded-xl text-zinc-500 dark:text-zinc-500 text-sm cursor-not-allowed"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end pt-4">
                      <button className="px-6 py-2.5 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-sm font-semibold rounded-xl hover:opacity-90 transition-opacity">
                        Save Changes
                      </button>
                    </div>
                  </div>
                </div>

                {/* Authentication Connection */}
                <div className="bg-white dark:bg-[#0D0F12] border border-zinc-200/60 dark:border-white/[0.06] rounded-[24px] overflow-hidden shadow-sm">
                  <div className="p-8 space-y-6">
                    <div className="space-y-1 border-b border-zinc-100 dark:border-white/[0.04] pb-4">
                      <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">Authentication</h3>
                      <p className="text-sm text-zinc-500">Manage your connected authentication providers.</p>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 border border-zinc-100 dark:border-white/[0.04] rounded-xl bg-zinc-50/50 dark:bg-white/[0.01]">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white dark:bg-[#1A1A1E] border border-zinc-200 dark:border-white/[0.08] rounded-full flex items-center justify-center shrink-0">
                          <svg className="w-5 h-5 text-zinc-700 dark:text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M12.545 10.239v3.821h5.445c-.712 2.315-2.647 3.972-5.445 3.972-3.332 0-6.033-2.701-6.033-6.032s2.701-6.032 6.033-6.032c1.498 0 2.866.549 3.921 1.453l2.814-2.814C17.503 2.988 15.139 2 12.545 2 7.021 2 2.543 6.477 2.543 12s4.478 10 10.002 10c8.396 0 10.249-7.85 9.426-11.761h-9.426z"/></svg>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-zinc-900 dark:text-white">Connected Account</h4>
                          <p className="text-xs text-zinc-500 mt-0.5">{user?.email}</p>
                        </div>
                      </div>
                      <span className="px-3 py-1 bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400 text-xs font-medium rounded-full border border-emerald-100 dark:border-emerald-500/20">Active</span>
                    </div>
                  </div>
                </div>

                {/* Danger Zone */}
                <div className="bg-red-50/30 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-[24px] overflow-hidden shadow-sm">
                  <div className="p-8 space-y-6">
                    <div className="space-y-1 pb-2">
                      <h3 className="text-lg font-semibold text-red-600 dark:text-red-400">Danger Zone</h3>
                      <p className="text-sm text-red-500/80 dark:text-red-400/80">Irreversible destructive actions for your account.</p>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-zinc-900 dark:text-white">Delete Account</h4>
                        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">Permanently delete your data and all workspaces.</p>
                      </div>
                      <button className="px-4 py-2 text-sm font-semibold text-red-600 bg-white dark:bg-black hover:bg-red-50 dark:hover:bg-red-950 border border-red-200 dark:border-red-900/50 rounded-xl transition-colors shadow-sm">
                        Delete Account
                      </button>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}
          {/* TAB 7: BILLING & QUOTAS */}
          {activeTab === "billing" && (
            <div className="space-y-10 animate-fadeIn max-w-5xl mx-auto w-full">
              <div className="space-y-1">
                <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Billing & Quotas</h1>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">Manage your subscription, view payment history, and monitor your API usage limits.</p>
              </div>

              {/* Current Plan Overview */}
              <div className="bg-white dark:bg-[#0D0F12] border border-zinc-200/60 dark:border-white/[0.06] rounded-[24px] overflow-hidden shadow-sm p-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div>
                    <h3 className="text-xs font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-2">Current Plan</h3>
                    <div className="flex items-end gap-3">
                      <span className="text-3xl font-bold text-zinc-900 dark:text-white">Hobby</span>
                      <span className="text-zinc-500 mb-1">$0/mo</span>
                    </div>
                    <p className="text-sm text-zinc-500 mt-2">You are currently on the free trial plan with strict autonomous limits.</p>
                  </div>
                  <div className="flex gap-3">
                    <button 
                      onClick={async () => {
                        const res = await fetch('/api/stripe/checkout', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ priceId: 'price_starter_id', plan: 'STARTER' })
                        });
                        const data = await res.json();
                        if (data.url) window.location.href = data.url;
                      }}
                      className="px-6 py-2.5 bg-zinc-100 dark:bg-white/[0.04] text-zinc-900 dark:text-white text-sm font-semibold rounded-xl hover:bg-zinc-200 dark:hover:bg-white/[0.08] transition-colors"
                    >
                      Upgrade Starter ($29)
                    </button>
                    <button 
                      onClick={async () => {
                        const res = await fetch('/api/stripe/checkout', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ priceId: 'price_pro_id', plan: 'PRO' })
                        });
                        const data = await res.json();
                        if (data.url) window.location.href = data.url;
                      }}
                      className="px-6 py-2.5 bg-cyan-500 text-black text-sm font-bold rounded-xl shadow-[0_0_20px_rgba(34,211,238,0.2)] hover:shadow-[0_0_30px_rgba(34,211,238,0.4)] transition-all"
                    >
                      Upgrade to Pro ($79)
                    </button>
                  </div>
                </div>
              </div>

              {/* Quotas & Usage */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-[#0D0F12] border border-zinc-200/60 dark:border-white/[0.06] rounded-[24px] overflow-hidden p-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <h4 className="text-sm font-semibold text-zinc-900 dark:text-white">Directory Submissions</h4>
                    <span className="text-xs font-medium px-2.5 py-1 bg-zinc-100 dark:bg-white/[0.05] rounded-full text-zinc-600 dark:text-zinc-400">0 / 3</span>
                  </div>
                  <div className="w-full h-2 bg-zinc-100 dark:bg-white/[0.04] rounded-full overflow-hidden">
                    <div className="h-full bg-cyan-500 w-0 rounded-full"></div>
                  </div>
                  <p className="text-xs text-zinc-500">Resets on July 5, 2026.</p>
                </div>

                <div className="bg-white dark:bg-[#0D0F12] border border-zinc-200/60 dark:border-white/[0.06] rounded-[24px] overflow-hidden p-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <h4 className="text-sm font-semibold text-zinc-900 dark:text-white">Autonomous AI Leads</h4>
                    <span className="text-xs font-medium px-2.5 py-1 bg-zinc-100 dark:bg-white/[0.05] rounded-full text-zinc-600 dark:text-zinc-400">0 / 10</span>
                  </div>
                  <div className="w-full h-2 bg-zinc-100 dark:bg-white/[0.04] rounded-full overflow-hidden">
                    <div className="h-full bg-cyan-500 w-0 rounded-full"></div>
                  </div>
                  <p className="text-xs text-zinc-500">Resets on July 5, 2026.</p>
                </div>
              </div>

            </div>
          )}
          
        </section>
      </main>

      {/* F5BOT MANUAL ALERT PASTE MODAL */}
      {showAddLeadModal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white dark:bg-[#171A21] border border-zinc-205 dark:border-white/[0.04] rounded-xl max-w-lg w-full p-6 space-y-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-zinc-200/60 dark:border-white/[0.04] pb-3">
              <h2 className="text-sm font-bold text-zinc-900 dark:text-[#f8f9fa] flex items-center gap-1.5">
                📥 Paste F5Bot Alert Details
              </h2>
              <button 
                onClick={() => setShowAddLeadModal(false)}
                className="text-zinc-400 hover:text-zinc-650 dark:hover:text-white text-sm font-bold "
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={handleManualLeadSubmit} className="space-y-6 text-sm font-semibold">
              <div className="grid grid-cols-2 gap-6">
                <div className="flex flex-col gap-3">
                  <label className="text-zinc-500 dark:text-[#8b919e]">Platform</label>
                  <select 
                    value={newLeadPlatform}
                    onChange={(e) => setNewLeadPlatform(e.target.value)}
                    className="bg-white dark:bg-[#0F1115] border border-zinc-200/60 dark:border-white/[0.04] px-2 py-1.5 rounded-xl outline-none"
                  >
                    <option value="HackerNews">HackerNews</option>
                    <option value="Reddit">Reddit</option>
                  </select>
                </div>
                
                <div className="flex flex-col gap-3">
                  <label className="text-zinc-500 dark:text-[#8b919e]">Thread URL (Optional)</label>
                  <input 
                    type="url" 
                    placeholder="https://..." 
                    value={newLeadUrl}
                    onChange={(e) => setNewLeadUrl(e.target.value)}
                    className="bg-white dark:bg-[#0F1115] border border-zinc-200/60 dark:border-white/[0.04] px-2 py-1.5 rounded-xl outline-none"
                  />
                </div>
              </div>
              
              <div className="flex flex-col gap-3">
                <label className="text-zinc-500 dark:text-[#8b919e]">Discussion Title / Topic</label>
                <input 
                  type="text" 
                  placeholder="e.g., Simple alternative to AWS complex cloud scaling" 
                  value={newLeadTitle}
                  onChange={(e) => setNewLeadTitle(e.target.value)}
                  required
                  className="bg-white dark:bg-[#0F1115] border border-zinc-200/60 dark:border-white/[0.04] px-2 py-1.5 rounded-xl outline-none"
                />
              </div>
              
              <div className="flex flex-col gap-3">
                <label className="text-zinc-500 dark:text-[#8b919e]">Alert Snippet (Thread Body Text)</label>
                <textarea 
                  rows={4}
                  placeholder="Paste the buyer intent description text matched by F5Bot..." 
                  value={newLeadBody}
                  onChange={(e) => setNewLeadBody(e.target.value)}
                  required
                  className="bg-white dark:bg-[#0F1115] border border-zinc-200/60 dark:border-white/[0.04] px-2.5 py-1.5 rounded-xl outline-none font-normal"
                />
              </div>
              
              {newLeadError && (
                <div className="p-3 text-[11px] border border-red-200 bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-400 rounded-xl">
                  ⚠️ {newLeadError}
                </div>
              )}
              
              <div className="flex justify-end gap-2 pt-3 border-t border-zinc-200/60 dark:border-white/[0.04]">
                <button 
                  type="button" 
                  onClick={() => setShowAddLeadModal(false)}
                  className="px-3 py-1.5 border border-zinc-200/60 dark:border-white/[0.04] hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl text-zinc-600 dark:text-[#8b919e] font-semibold"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={newLeadLoading}
                  className="px-4 py-1.5 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 font-semibold rounded-xl disabled:opacity-50 transition-all duration-300 ease-out flex items-center gap-1.5"
                >
                  {newLeadLoading ? (
                    <>
                      <span className="w-3 h-3 rounded-full border-2 border-zinc-500 border-t-transparent animate-spin"></span>
                      Generating reply...
                    </>
                  ) : (
                    <>Generate AI Pitch 🤖</>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}



      {/* Embedded Minimalist CSS Animations */}
      <style jsx global>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>
      {/* DELETE ALL DRAFTS MODAL */}
      <AnimatePresence>
        {showDeleteAllModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-[#0D0F12] border border-zinc-200 dark:border-white/[0.06] rounded-2xl w-full max-w-md shadow-2xl overflow-hidden"
            >
              <div className="p-6">
                <div className="w-12 h-12 rounded-full bg-red-50 dark:bg-red-500/10 flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-zinc-900 dark:text-white mb-2">Delete All Drafts?</h3>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  Are you sure you want to permanently delete all your generated blog drafts? This action cannot be undone.
                </p>
                <div className="mt-8 flex items-center justify-end gap-3">
                  <button
                    onClick={() => setShowDeleteAllModal(false)}
                    className="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-[#1A1C23] rounded-xl transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={executeDeleteAllDrafts}
                    className="px-4 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors shadow-sm"
                  >
                    Yes, delete all
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* GLOBAL TOAST NOTIFICATIONS */}
      <div className="fixed bottom-6 right-6 z-[110] flex flex-col gap-3 pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
              className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl border ${
                toast.type === "success" 
                  ? "bg-white dark:bg-[#12141A] border-emerald-100 dark:border-emerald-500/20" 
                  : "bg-white dark:bg-[#12141A] border-red-100 dark:border-red-500/20"
              }`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                toast.type === "success" ? "bg-emerald-50 dark:bg-emerald-500/10" : "bg-red-50 dark:bg-red-500/10"
              }`}>
                {toast.type === "success" ? (
                  <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </div>
              <p className="text-sm font-medium text-zinc-700 dark:text-zinc-200">{toast.message}</p>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {showUpgradeModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="w-full max-w-md bg-white dark:bg-[#15171C] border border-zinc-200 dark:border-white/10 rounded-2xl p-8 text-center shadow-2xl relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
            
            <div className="w-16 h-16 bg-gradient-to-tr from-indigo-500/10 to-purple-500/10 text-indigo-500 dark:text-indigo-400 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-inner ring-1 ring-white/20 dark:ring-white/5">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            
            <h3 className="text-xl font-bold text-zinc-900 dark:text-white mb-2">Upgrade to Unlock More</h3>
            <p className="text-zinc-500 dark:text-zinc-400 mb-8">{upgradeMessage}</p>
            
            <div className="flex flex-col gap-3">
              <button 
                onClick={() => { setShowUpgradeModal(false); setActiveTab("settings"); }}
                className="w-full py-3.5 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-xl font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-100 transition-colors"
              >
                View Upgrade Plans
              </button>
              <button 
                onClick={() => setShowUpgradeModal(false)}
                className="w-full py-3.5 text-zinc-500 dark:text-zinc-400 font-medium hover:text-zinc-800 dark:hover:text-white transition-colors"
              >
                Maybe Later
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
