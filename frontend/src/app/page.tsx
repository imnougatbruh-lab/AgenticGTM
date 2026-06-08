"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession, signIn } from "next-auth/react";
import { ArrowRight, Sparkles, Play, Zap, Globe, BarChart3, Target, Workflow, Users } from "lucide-react";

export default function XyrocoLanding() {
  const { data: session } = useSession();
  const user = session?.user;
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [hoveredFeature, setHoveredFeature] = useState<number | null>(null);

  const router = useRouter();

  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Global Fetch Interceptor to inject authentication headers dynamically
  useEffect(() => {
    if (!user) return;
    const originalFetch = window.fetch;
    window.fetch = async (input, init) => {
      const initObj = init || {};
      const headers = new Headers(initObj.headers || {});
      headers.set("X-Clerk-ID", user.email || "");
      if (user.email) {
        headers.set("X-User-Email", user.email);
      }
      initObj.headers = headers;
      return originalFetch(input, initObj);
    };
    return () => {
      window.fetch = originalFetch;
    };
  }, [user]);

  const handleWaitlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    try {
      await fetch(`${API_URL}/waitlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setLoading(false);
      setSubmitted(true);
    } catch (err) {
      setLoading(false);
      setSubmitted(true);
    }
  };

  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  
  const handleCheckout = async (plan: string) => {
    if (!user) {
      router.push("/login");
      return;
    }
    try {
      setCheckoutLoading(plan);
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan })
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        alert(data.error || "Checkout failed");
      }
    } catch (err) {
      alert("Checkout failed. Please try again.");
    } finally {
      setCheckoutLoading(null);
    }
  };

  const staggerContainer = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.3,
      },
    },
  };

  const fadeUp = {
    hidden: { opacity: 0, y: 30 },
    show: { opacity: 1, y: 0, transition: { type: "spring", bounce: 0.4, duration: 1 } },
  };

  return (
    <div className="min-h-screen w-full bg-[#050505] text-zinc-100 font-sans selection:bg-cyan-500/30 overflow-x-hidden relative">
      
      {/* Dynamic Backgrounds & Gradients */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
        
        {/* Animated Aurora Glows - Optimized with will-change and hardware acceleration */}
        <motion.div 
          style={{ willChange: "transform, opacity" }}
          animate={{ 
            scale: [1, 1.1, 1],
            opacity: [0.2, 0.3, 0.2],
            x: [0, 30, 0],
            y: [0, 20, 0]
          }}
          transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
          className="absolute top-[-20%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-purple-600/20 blur-[100px] transform-gpu"
        />
        <motion.div 
          style={{ willChange: "transform, opacity" }}
          animate={{ 
            scale: [1, 1.05, 1],
            opacity: [0.15, 0.25, 0.15],
            x: [0, -20, 0],
            y: [0, -10, 0]
          }}
          transition={{ duration: 12, repeat: Infinity, ease: "linear", delay: 2 }}
          className="absolute top-[10%] right-[-10%] w-[40vw] h-[40vw] rounded-full bg-cyan-600/20 blur-[80px] transform-gpu"
        />
        
        {/* Removed heavy backdrop-blur-[100px] and SVG noise for 144hz performance */}
      </div>

      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-[#050505]/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            {/* User Logo */}
            <img src="/logo.png" alt="Xyroco Logo" className="w-8 h-8 object-contain drop-shadow-[0_0_15px_rgba(139,92,246,0.5)] group-hover:scale-105 transition-transform" />
            <span className="font-bold text-xl tracking-tight text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-zinc-400 transition-all">Xyroco</span>
          </Link>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium">
            <Link href="#features" className="text-zinc-400 hover:text-white transition-colors">Features</Link>
            <Link href="#workflow" className="text-zinc-400 hover:text-white transition-colors">Workflow</Link>
            <Link href="#pricing" className="text-zinc-400 hover:text-white transition-colors">Pricing</Link>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <Link href="/dashboard" className="relative group overflow-hidden rounded-full bg-white/10 px-5 py-2 text-sm font-medium text-white border border-white/10 hover:border-white/20 transition-all">
                <span className="relative z-10">Dashboard</span>
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              </Link>
            ) : (
              <button onClick={() => signIn(undefined, { callbackUrl: "/dashboard" })} className="relative group overflow-hidden rounded-full bg-white px-5 py-2 text-sm font-semibold text-black hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(255,255,255,0.2)]">
                <span className="relative z-10 flex items-center gap-2">Get Started <ArrowRight className="w-4 h-4" /></span>
              </button>
            )}
          </div>
        </div>
      </nav>

      <main className="relative z-10 pt-32 pb-24">
        {/* 1. HERO SECTION */}
        <section className="px-6 min-h-[85vh] flex items-center max-w-7xl mx-auto relative">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center w-full">
            
            {/* Left side copy */}
            <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-8 relative z-20">
              <motion.div variants={fadeUp} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-zinc-300 backdrop-blur-md">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>The new standard for GTM in 2026</span>
              </motion.div>
              
              <motion.div variants={fadeUp} className="space-y-4">
                <h1 className="text-5xl md:text-7xl font-bold tracking-tighter text-white leading-[1.05]">
                  Growth on <br/>
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600">Autopilot.</span>
                </h1>
                <p className="text-lg md:text-xl text-zinc-400 max-w-lg leading-relaxed font-light">
                  A premium autonomous engine that discovers intent, builds pipelines, and executes high-converting campaigns while you sleep.
                </p>
              </motion.div>

              <motion.div variants={fadeUp} className="flex flex-col sm:flex-row items-center gap-4 pt-4">
                {user ? (
                  <Link 
                    href="/dashboard"
                    className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-full bg-white px-8 py-4 text-sm font-semibold text-black shadow-[0_0_40px_rgba(255,255,255,0.15)] hover:shadow-[0_0_60px_rgba(255,255,255,0.25)] hover:scale-[1.02] active:scale-[0.98] transition-all"
                  >
                    Go to Dashboard <ArrowRight className="w-4 h-4" />
                  </Link>
                ) : (
                  <button 
                    onClick={() => signIn(undefined, { callbackUrl: "/dashboard" })}
                    className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-full bg-white px-8 py-4 text-sm font-semibold text-black shadow-[0_0_40px_rgba(255,255,255,0.15)] hover:shadow-[0_0_60px_rgba(255,255,255,0.25)] hover:scale-[1.02] active:scale-[0.98] transition-all"
                  >
                    Deploy Engine <ArrowRight className="w-4 h-4" />
                  </button>
                )}
                <button className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-full bg-white/5 border border-white/10 px-8 py-4 text-sm font-medium text-white hover:bg-white/10 transition-colors">
                  <Play className="w-4 h-4 text-zinc-400" /> Watch Demo
                </button>
              </motion.div>
            </motion.div>

            {/* Right side interactive visual centerpiece */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }} 
              animate={{ opacity: 1, scale: 1 }} 
              transition={{ duration: 1.5, type: "spring", bounce: 0.3 }}
              className="relative w-full h-[500px] lg:h-[600px] flex items-center justify-center"
            >
              {/* Central glowing orb */}
              <motion.div 
                style={{ willChange: "transform" }}
                animate={{ scale: [1, 1.05, 1], rotate: [0, 90, 0] }}
                transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                className="absolute w-64 h-64 rounded-full bg-gradient-to-tr from-cyan-500/20 to-purple-500/20 blur-[60px] transform-gpu"
              />
              
              {/* Floating Glass Panels */}
              <div className="relative w-full max-w-[500px] aspect-square perspective-1000">
                {/* Main Dashboard Panel */}
                <motion.div 
                  style={{ willChange: "transform", transformStyle: 'preserve-3d' }}
                  animate={{ y: [0, -10, 0], rotateX: [10, 15, 10], rotateY: [-10, -5, -10] }}
                  transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute inset-10 rounded-2xl bg-white/[0.03] border border-white/10 shadow-2xl overflow-hidden flex flex-col transform-gpu"
                >
                  {/* Mock Header */}
                  <div className="h-12 border-b border-white/10 flex items-center px-4 gap-2 bg-white/[0.01]">
                    <div className="flex gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                      <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                      <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
                    </div>
                  </div>
                  {/* Mock Content */}
                  <div className="flex-1 p-6 flex flex-col gap-4">
                    <div className="flex justify-between items-center">
                      <div className="h-4 w-32 bg-white/10 rounded"></div>
                      <div className="h-4 w-12 bg-cyan-500/40 rounded"></div>
                    </div>
                    <div className="h-24 w-full bg-gradient-to-r from-white/5 to-transparent rounded-lg border border-white/5 relative overflow-hidden">
                      <motion.div 
                        initial={{ x: "-100%" }}
                        animate={{ x: "200%" }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-y-0 w-1/2 bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent"
                      />
                    </div>
                    <div className="flex gap-4">
                      <div className="h-16 flex-1 bg-white/5 rounded-lg border border-white/5"></div>
                      <div className="h-16 flex-1 bg-white/5 rounded-lg border border-white/5"></div>
                    </div>
                  </div>
                </motion.div>

                {/* Floating Intent Card */}
                <motion.div 
                  style={{ willChange: "transform" }}
                  animate={{ y: [0, 15, 0], rotateZ: [5, 2, 5] }}
                  transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                  className="absolute top-4 -right-4 w-48 p-4 rounded-xl bg-[#111111]/90 border border-purple-500/30 shadow-[0_10px_40px_rgba(139,92,246,0.15)] z-20 transform-gpu"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                      <Zap className="w-4 h-4 text-purple-400" />
                    </div>
                    <div className="text-xs font-semibold text-white">High Intent Detected</div>
                  </div>
                  <div className="h-2 w-full bg-white/10 rounded mt-3"></div>
                  <div className="h-2 w-2/3 bg-white/10 rounded mt-2"></div>
                </motion.div>

                {/* Floating Analytics Card */}
                <motion.div 
                  style={{ willChange: "transform" }}
                  animate={{ y: [0, -15, 0], rotateZ: [-5, -8, -5] }}
                  transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                  className="absolute bottom-8 -left-8 w-56 p-4 rounded-xl bg-[#111111]/90 border border-cyan-500/30 shadow-[0_10px_40px_rgba(6,182,212,0.15)] z-20 transform-gpu"
                >
                  <div className="flex items-center gap-3">
                    <div className="text-3xl font-bold text-white">+342%</div>
                    <div className="text-[10px] text-cyan-400 font-medium uppercase tracking-wider leading-tight">Pipeline<br/>Generated</div>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* 2. PRODUCT PREVIEW SECTION */}
        <section className="py-24 px-6 relative max-w-7xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className="rounded-3xl border border-white/10 bg-[#0A0A0A] p-2 overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.5)] relative"
          >
            {/* Top glowing edge */}
            <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent"></div>
            
            <div className="rounded-2xl border border-white/5 bg-[#030303] overflow-hidden relative">
              {/* App UI Header */}
              <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-[#050505]">
                <div className="flex items-center gap-6">
                  <div className="font-semibold text-white">Dashboard</div>
                  <div className="text-zinc-500 text-sm">Campaigns</div>
                  <div className="text-zinc-500 text-sm">Analytics</div>
                </div>
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-zinc-700 to-zinc-900 border border-white/10"></div>
              </div>
              
              {/* App UI Content Area */}
              <div className="p-8 grid grid-cols-3 gap-6 h-[500px]">
                <div className="col-span-2 space-y-6">
                  <div className="h-32 rounded-xl bg-white/[0.02] border border-white/5 flex items-center p-6 gap-6 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                      <Target className="w-8 h-8 text-cyan-400" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-white mb-1">Active Hunt</div>
                      <div className="text-sm text-zinc-400">Scraping 400+ communities for buying signals</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-6 h-[260px]">
                    <div className="rounded-xl bg-white/[0.02] border border-white/5 p-6">
                      <div className="h-4 w-24 bg-white/10 rounded mb-8"></div>
                      <div className="space-y-4">
                        {[1, 2, 3].map(i => (
                          <div key={i} className="h-10 w-full bg-white/5 rounded-lg border border-white/5"></div>
                        ))}
                      </div>
                    </div>
                    <div className="rounded-xl bg-white/[0.02] border border-white/5 p-6 flex flex-col justify-end relative overflow-hidden">
                      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-purple-500/20 to-transparent"></div>
                      <div className="text-4xl font-bold text-white relative z-10 mb-2">94%</div>
                      <div className="text-sm text-zinc-400 relative z-10">Match Accuracy</div>
                    </div>
                  </div>
                </div>
                <div className="col-span-1 rounded-xl bg-white/[0.02] border border-white/5 p-6 relative overflow-hidden">
                  <div className="absolute right-0 top-0 w-32 h-32 bg-cyan-500/10 blur-[40px]"></div>
                  <div className="text-sm font-semibold text-white mb-6">Live Intent Feed</div>
                  <div className="space-y-4">
                    {[1,2,3,4].map((i, index) => (
                      <motion.div 
                        key={i}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.2, duration: 0.5 }}
                        className="p-3 rounded-lg bg-white/5 border border-white/5 text-xs text-zinc-400"
                      >
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-white font-medium">New Signal</span>
                          <span className="text-cyan-400">Just now</span>
                        </div>
                        <div className="h-2 w-full bg-white/10 rounded mb-1.5"></div>
                        <div className="h-2 w-2/3 bg-white/10 rounded"></div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* 3. FEATURES SECTION */}
        <section id="features" className="py-24 px-6 max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-4">A completely new <br/> category of software.</h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto font-light">Not just another tool. A fully autonomous team working tirelessly for your growth.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: <Globe className="w-6 h-6 text-cyan-400" />,
                title: "Global Distribution",
                desc: "We submit your product to 100+ high-traffic directories, securing powerful backlinks and early traction automatically.",
                colSpan: "md:col-span-2"
              },
              {
                icon: <Zap className="w-6 h-6 text-purple-400" />,
                title: "Real-time Intent",
                desc: "Monitor social channels for users explicitly asking for a solution like yours.",
                colSpan: "md:col-span-1"
              },
              {
                icon: <Workflow className="w-6 h-6 text-green-400" />,
                title: "Autonomous Outreach",
                desc: "Hyper-personalized messaging generated and sent to high-intent leads instantly.",
                colSpan: "md:col-span-1"
              },
              {
                icon: <BarChart3 className="w-6 h-6 text-blue-400" />,
                title: "Self-Optimizing Funnels",
                desc: "The engine learns from every interaction. A/B testing copy, channels, and timing without human intervention.",
                colSpan: "md:col-span-2"
              }
            ].map((feature, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                onMouseEnter={() => setHoveredFeature(i)}
                onMouseLeave={() => setHoveredFeature(null)}
                className={`relative p-8 rounded-3xl bg-white/[0.02] border border-white/5 overflow-hidden group cursor-pointer ${feature.colSpan}`}
              >
                {/* Hover Glow */}
                <div 
                  className={`absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 transition-opacity duration-500 ${hoveredFeature === i ? 'opacity-100' : ''}`}
                ></div>
                
                <div className="relative z-10">
                  <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
                  <p className="text-zinc-400 leading-relaxed font-light">{feature.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* 4. BENEFITS/METRICS SECTION */}
        <section className="py-24 border-y border-white/5 bg-white/[0.01] relative overflow-hidden">
          {/* Subtle moving light effect in background */}
          <motion.div 
            animate={{ x: ["-100%", "200%"] }}
            transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
            className="absolute top-0 bottom-0 w-[500px] bg-gradient-to-r from-transparent via-cyan-500/5 to-transparent skew-x-[-45deg]"
          />
          
          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 divide-x divide-white/5 text-center">
              {[
                { label: "Hours Saved/Month", value: "120+" },
                { label: "Directories Supported", value: "150+" },
                { label: "Intent Accuracy", value: "94%" },
                { label: "Uptime", value: "24/7" }
              ].map((metric, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                  className="px-4"
                >
                  <div className="text-4xl md:text-5xl font-bold text-white mb-2 tracking-tight">{metric.value}</div>
                  <div className="text-sm font-medium text-zinc-500 uppercase tracking-widest">{metric.label}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* 4.5 PRICING SECTION */}
        <section className="py-24 px-6 relative max-w-7xl mx-auto" id="pricing">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-4">Simple, transparent pricing.</h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto font-light">Choose the plan that fits your growth engine.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Hobby Plan */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="p-8 rounded-[24px] bg-white/[0.01] border border-white/5 relative flex flex-col opacity-80 hover:opacity-100 transition-opacity"
            >
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-white mb-2">Hobby</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">$0</span>
                  <span className="text-zinc-500">/mo</span>
                </div>
                <p className="text-sm text-zinc-400 mt-3 font-light">Test the autonomous engine.</p>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                {['1 Active Workspace', '3 Directory Submissions', '10 Autonomous AI Leads/mo', 'Community Support'].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm text-zinc-400">
                    <Zap className="w-4 h-4 text-zinc-500" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link href={user ? "/dashboard" : "/login"} className="w-full py-3 px-4 bg-transparent hover:bg-white/5 border border-white/10 rounded-xl text-zinc-300 font-medium text-center transition-all">
                {user ? "Go to Dashboard" : "Start Free"}
              </Link>
            </motion.div>

            {/* Starter Plan */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="p-8 rounded-[24px] bg-white/[0.02] border border-white/5 relative flex flex-col"
            >
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-white mb-2">Starter</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">$29</span>
                  <span className="text-zinc-500">/mo</span>
                </div>
                <p className="text-sm text-zinc-400 mt-3 font-light">Perfect for early-stage startups.</p>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                {['1 Active Workspace', '70 Directory Submissions', '100 Autonomous AI Leads/mo', 'Standard Support'].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm text-zinc-300">
                    <Zap className="w-4 h-4 text-cyan-400" />
                    {feature}
                  </li>
                ))}
              </ul>
              {user ? (
                <button 
                  onClick={() => handleCheckout("starter")}
                  disabled={checkoutLoading === "starter"}
                  className="w-full py-3 px-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white font-medium text-center transition-all"
                >
                  {checkoutLoading === "starter" ? "Loading..." : "Buy Now"}
                </button>
              ) : (
                <Link href="/login" className="w-full py-3 px-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white font-medium text-center transition-all">
                  Get Started
                </Link>
              )}
            </motion.div>

            {/* Pro Plan */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="p-8 rounded-[24px] bg-gradient-to-b from-cyan-900/20 to-transparent border border-cyan-500/20 relative flex flex-col overflow-hidden"
            >
              <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent"></div>
              <div className="mb-8">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-xl font-semibold text-white">Pro</h3>
                  <span className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium rounded-full">Most Popular</span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">$79</span>
                  <span className="text-zinc-500">/mo</span>
                </div>
                <p className="text-sm text-zinc-400 mt-3 font-light">For teams ready to scale rapidly.</p>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                {['Unlimited Workspaces', 'Unlimited Directory Submissions', '1,000 Autonomous AI Leads/mo', 'Priority 24/7 Support'].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm text-white">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    {feature}
                  </li>
                ))}
              </ul>
              {user ? (
                <button 
                  onClick={() => handleCheckout("pro")}
                  disabled={checkoutLoading === "pro"}
                  className="w-full py-3 px-4 bg-cyan-500 hover:bg-cyan-400 text-black rounded-xl font-bold text-center transition-all shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)]"
                >
                  {checkoutLoading === "pro" ? "Loading..." : "Buy Now"}
                </button>
              ) : (
                <Link href="/login" className="w-full py-3 px-4 bg-cyan-500 hover:bg-cyan-400 text-black rounded-xl font-bold text-center transition-all shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)]">
                  Upgrade to Pro
                </Link>
              )}
            </motion.div>
          </div>
        </section>

        {/* 5. FINAL CTA */}
        <section className="py-32 px-6 relative max-w-4xl mx-auto text-center">
          <div className="absolute inset-0 bg-gradient-to-t from-cyan-900/20 to-transparent blur-3xl -z-10 rounded-full"></div>
          
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="space-y-8"
          >
            <div className="inline-block px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-zinc-300">
              Limited Early Access
            </div>
            
            <h2 className="text-4xl md:text-6xl font-bold text-white tracking-tighter leading-tight">
              Ready to scale <br/> effortlessly?
            </h2>
            
            <p className="text-xl text-zinc-400 font-light">
              Join the elite group of founders who let AI handle their growth.
            </p>

            <form onSubmit={handleWaitlist} className="max-w-md mx-auto mt-10 relative">
              <div className="flex p-1.5 rounded-full bg-white/5 border border-white/10 focus-within:border-cyan-500/50 focus-within:bg-white/10 transition-all shadow-2xl">
                <input 
                  type="email" 
                  required
                  placeholder="founder@startup.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-transparent border-none text-white px-6 focus:outline-none placeholder:text-zinc-600"
                />
                <button 
                  type="submit"
                  disabled={loading || submitted}
                  className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-black shrink-0 hover:scale-[1.02] active:scale-[0.98] transition-transform disabled:opacity-70 disabled:hover:scale-100"
                >
                  {loading ? "Requesting..." : (submitted ? "Added to Waitlist" : "Get Access")}
                </button>
              </div>
            </form>
          </motion.div>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 bg-[#030303] py-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Xyroco Logo" className="w-6 h-6 object-contain" />
            <span className="font-bold text-lg tracking-tight text-white">Xyroco</span>
          </div>
          <p className="text-sm text-zinc-600">
            © {new Date().getFullYear()} Xyroco. Premium Growth Infrastructure.
          </p>
        </div>
      </footer>

    </div>
  );
}
