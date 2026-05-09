# NeuroDesk AMD — Demo Script (3 Minutes)

This is a structured demo flow for judges during the AMD Developer Hackathon.

---

## 🎯 Demo Objective

Demonstrate a real multi-agent AI system running on AMD MI300X GPUs, with transparent orchestration and measurable performance.

---

## ⏱️ Timing Breakdown

| Phase | Duration | Key Points |
|-------|----------|------------|
| **Introduction** | 0:00-0:30 | Product positioning, AMD connection |
| **Setup** | 0:30-1:00 | Navigate UI, show configuration |
| **Campaign Execution** | 1:00-2:00 | Run actual campaign with activity stream |
| **Results & AMD Value** | 2:00-2:45 | Show report, performance metrics |
| **Q&A Prep** | 2:45-3:00 | Highlight key differentiators |

---

## 📋 DEMO FLOW

### Phase 1: Introduction (0:00-0:30)

**Narrative:**
"Hi, my name is [Name]. Today I'm demonstrating **NeuroDesk AMD** — a multi-agent marketing operations copilot powered by AMD Developer Cloud and MI300X GPUs."

**What to Show:**
1. Open the NeuroDesk AMD web interface
2. Show the header: "NeuroDesk AMD" with AMD Developer Cloud branding
3. Briefly explain the architecture: "We have MAB (orchestrator) and three specialized agents (SAB1, SAB2, SAB3)"

**Key Message:**
"This is not a chatbot — it's a real agentic AI system that delegates tasks to specialized agents."

---

### Phase 2: Setup & Configuration (0:30-1:00)

**Narrative:**
"Let me show you how NeuroDesk AMD is configured to use AMD Developer Cloud."

**What to Show:**
1. Click "Settings" tab in the navigation
2. Show SAB1 configuration:
   - Provider: **AMD Cloud (vLLM)** - highlight with "🚀 Powered by AMD MI300X" badge
   - Model: **Qwen/Qwen2.5-7B-Instruct** (open-source)
   - Base URL: **http://localhost:8000/v1**
3. Repeat for SAB2 and SAB3

**Key Message:**
"All agents use AMD Cloud (vLLM) on MI300X GPUs, with open-source models. This is hackathon-recommended configuration."

**Optional Toggle:**
"Demo Mode is enabled by default for reliable demonstrations. We can switch to Live Tool Mode when real APIs are configured."

---

### Phase 3: Campaign Execution (1:00-2:00)

**Narrative:**
"Let's run a marketing campaign. I'll use a sample goal: launching a social media campaign for a local coffee shop."

**What to Show:**
1. Go to "Campaign" tab (MAB)
2. Enter goal: *"Launch Instagram campaign for a local coffee shop called 'Bean & Brew' targeting 25-45 year olds in Austin. Focus on weekend specials and loyalty program."*
3. Select "Instagram" as platform
4. Click "Run Full Campaign"

**During Execution:**
Watch the activity stream showing:
- MAB: "Understanding your marketing goal..."
- MAB: "Breaking your goal into 3 tasks..."
- MAB: "Checking tools..."
- MAB: "Assigning T1 to SAB1..."
- SAB1: "🔍 SAB1: Processing task..."
- SAB2: "📊 SAB2: Processing task..."
- SAB3: "✍️ SAB3: Processing task..."
- MAB: "Synthesizing final campaign report..."

**Key Message:**
"Notice how MAB orchestrates the workflow, delegates tasks, and monitors completion in real-time."

---

### Phase 4: Results & AMD Value (2:00-2:45)

**Narrative:**
"Let me show you the results and why AMD MI300X matters for this workload."

**What to Show:**
1. Click the campaign output modal to show the full report
2. Navigate to "Performance" tab:
   - Show KPI cards with real metrics
   - Point out "AMD Cloud (vLLM)" highlighted in results
   - Show benchmark comparison table
3. Scroll to "AMD Info" tab:
   - Show "Powered by AMD MI300X" banner
   - Explain the vLLM/OpenAI-compatible endpoint
4. In the final report, point out:
   - Business Value section
   - Strategy vs Copy Drift Checker results

**Key Message:**
"Notice the performance metrics — we're achieving 45+ tokens/second on AMD MI300X. The AMD Cloud provider shows consistently better latency than other providers."

**Demo Mode vs Live Mode:**
"In Live Tool Mode, agents would call real tools like Serper search and website scrapers to produce grounded, fact-based outputs."

---

### Phase 5: Q&A Prep (2:45-3:00)

**Key Differentiators to Highlight:**

| Feature | Why It Matters |
|---------|----------------|
| **Multi-Agent Architecture** | Real orchestration, not just chat responses |
| **AMD Cloud Integration** | Demonstrated on MI300X, ROCm-ready |
| **Open-Source First** | Qwen2.5, Llama 3.1, Mistral — no vendor lock-in |
| **Performance Dashboard** | Measurable AMD acceleration |
| **Demo Mode** | Reliable demo even without external API keys |
| **Business Value Layer** | Shows practical impact for judges |
| **Hugging Face Ready** | Public deployment path |
| **Strategy Drift Checker** | Original feature ensuring quality |

---

## 💡 Sample Campaign Goals for Live Demo

1. **E-commerce**: "Launch TikTok campaign for a boutique clothing store targeting Gen Z"
2. **Service Business**: "Create LinkedIn strategy for a local accounting firm"
3. **Food Service**: "Instagram campaign for a vegan bakery in Portland"
4. **Tech Startup**: "Campaign for a SaaS product launching new feature"

---

## 🔧 Technical Details to Have Ready

### Architecture
- **MAB**: Task planning, orchestration, synthesis
- **SAB1**: Research, competitor analysis, audience insights
- **SAB2**: 30-day content strategy, platform formats
- **SAB3**: Social media captions, ad copy, email content

### Tech Stack
- Backend: FastAPI + WebSocket streaming
- Frontend: Vanilla JS + CSS (lightweight, no build)
- LLM: vLLM on AMD MI300X (OpenAI-compatible)
- Memory: SQLite for persistent storage

### AMD Integration
- Provider: AMD Cloud (vLLM)
- Model: Qwen/Qwen2.5-7B-Instruct (or similar)
- Endpoint: OpenAI-compatible API on port 8000
- Framework: ROCm for GPU acceleration

---

## 🎨 Visual Tips

1. **Dark Theme**: NeuroDesk uses a premium dark theme by default — show this
2. **Activity Stream**: Highlight the real-time activity feed — makes it feel alive
3. **Performance Tab**: Shows real AMD acceleration metrics
4. **AMD Badges**: Highlight the green "Powered by AMD MI300X" badges

---

## 📝 Follow-Up Resources to Share

After the demo, point judges to:
- GitHub repo: https://github.com/neurodesk-amd/neurodesk-amd
- Hackathon submission: `HACKATHON_SUBMISSION.md`
- AMD deployment guide: `DEPLOY_AMD_CLOUD.md`
- Hugging Face demo: `demo_app.py`

---

## ❓ Common Judge Questions & Answers

**Q: How is this different from a simple LangChain app?**
**A:** This demonstrates a true multi-agent architecture with specialized agents (Research, Strategy, Content) orchestrated by MAB, with transparent task delegation and performance metrics.

**Q: What AMD-specific optimizations are you using?**
**A:** We use vLLM with ROCm for AMD GPU acceleration, targeting MI300X instances on AMD Developer Cloud.

**Q: Can this run on local AMD hardware?**
**A:** Absolutely! The same vLLM endpoint works on local AMD GPUs. AMD Developer Cloud just provides scalable access to MI300X.

**Q: How do you verify AMD acceleration?**
**A:** The Performance tab shows benchmark comparisons between AMD Cloud (vLLM) and other providers, with measurable latency and throughput differences.

---

## ✅ Demo Checklist

- [ ] Open NeuroDesk AMD in browser
- [ ] Navigate to Settings → Show AMD Cloud configuration
- [ ] Enter campaign goal
- [ ] Click "Run Campaign"
- [ ] Show activity stream during execution
- [ ] Display final report
- [ ] Navigate to Performance tab → Show metrics
- [ ] Navigate to AMD Info tab → Show architecture
- [ ] Highlight Business Value section
- [ ] Explain AMD MI300X integration
- [ ] Q&A prep

---

## 🎯 Success Criteria

After this demo, judges should understand:
1. ✅ This is a real multi-agent AI system
2. ✅ It's powered by AMD Developer Cloud (MI300X)
3. ✅ Performance is measurable and superior
4. ✅ Open-source models are prioritized
5. ✅ The UI is polished and demo-friendly
6. ✅ The architecture is sophisticated and original

---

*Good luck with your hackathon!* 🚀