import streamlit as st
import time
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain
import search_direct, scrape_direct from tools

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchMind · AI Research Agent",
    page_icon="🔬",
    layout="centered",          # centered feed instead of wide dashboard
    initial_sidebar_state="collapsed",
)

# ── Minimal CSS (kept, but no card-grid — just typography + accents) ─────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #0a0a0f; }

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: #f0ebe0;
    text-align: center;
    margin-bottom: 0.2rem;
}
.hero-title span { color: #ff8c32; }
.hero-sub {
    text-align: center;
    color: #a09890;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

/* chat bubble accents per agent */
.agent-tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #ff8c32;
    margin-bottom: 0.3rem;
}
.stChatMessage { border-radius: 14px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-title">Research<span>Mind</span></div>
<div class="hero-sub">Watch four agents work the problem, live, as a conversation.</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in (("results", {}), ("running", False), ("done", False)):
    if key not in st.session_state:
        st.session_state[key] = default

STEP_ORDER = [
    ("search", "🔍", "Search Agent", "assistant"),
    ("reader", "📄", "Reader Agent", "assistant"),
    ("writer", "✍️", "Writer Chain", "assistant"),
    ("critic", "🧐", "Critic Chain", "assistant"),
]

# ── Input row (chat_input pins to bottom like a real conversation) ──────────
topic = st.chat_input("Enter a research topic and press enter…")

if topic and not st.session_state.running:
    st.session_state.results = {}
    st.session_state.running = True
    st.session_state.done = False
    st.session_state["topic_val"] = topic
    st.rerun()

# ── Replay: show the user's "message" (the topic) as the first bubble ───────
topic_val = st.session_state.get("topic_val")
if topic_val:
    with st.chat_message("user"):
        st.markdown(f"**Research topic:** {topic_val}")

r = st.session_state.results

# progress bar across the top instead of side-by-side step cards
if topic_val:
    completed = len(r)
    total = len(STEP_ORDER)
    st.progress(completed / total, text=f"{completed}/{total} agents finished")

# ── Render already-completed steps as chat bubbles ───────────────────────────
for key, icon, label, role in STEP_ORDER:
    if key in r:
        with st.chat_message(role, avatar=icon):
            st.markdown(f'<div class="agent-tag">{label}</div>', unsafe_allow_html=True)
            if key == "writer":
                st.markdown(r[key])
            elif key == "critic":
                st.markdown(r[key])
            else:
                # raw search/reader output tucked away so the feed stays readable
                with st.expander("View raw output", expanded=False):
                    st.markdown(r[key])
                st.caption("✓ done — see raw output above")

# ── Pipeline execution (runs once per topic submission) ──────────────────────
if st.session_state.running and not st.session_state.done:
    results = dict(r)

    if "search" not in results:
        with st.chat_message("assistant", avatar="🔍"):
            st.markdown('<div class="agent-tag">Search Agent</div>', unsafe_allow_html=True)
            try:
                with st.spinner("Searching the web…"):
                    hits = search_direct(topic_val)
                    results["search_hits"] = hits
                    results["search"] = "\n\n".join(
                        f"{h['title']}\n{h['url']}\n{h['content'][:400]}" for h in hits
                    )
            except Exception as e:
                st.session_state.running = False
                st.error(f"Search failed: {e}")
                st.stop()
    st.session_state.results = dict(results)
    st.rerun()

if "reader" not in results:
    with st.chat_message("assistant", avatar="📄"):
        st.markdown('<div class="agent-tag">Reader Agent</div>', unsafe_allow_html=True)
        with st.spinner("Scraping the most relevant source…"):
            top_url = results["search_hits"][0]["url"]
            results["reader"] = scrape_direct(top_url)
    st.session_state.results = dict(results)
    st.rerun()

    if "writer" not in results:
        with st.chat_message("assistant", avatar="✍️"):
            st.markdown('<div class="agent-tag">Writer Chain</div>', unsafe_allow_html=True)
            try:
                with st.spinner("Drafting the report…"):
                    research_combined = (
                        f"SEARCH RESULTS:\n{results['search']}\n\n"
                        f"DETAILED SCRAPED CONTENT:\n{results['reader']}"
                    )
                    results["writer"] = writer_chain.invoke({
                        "topic": topic_val,
                        "research": research_combined
                    })
            except Exception as e:
                st.session_state.running=False
                st.error("f writer agent is failed {e}")
                st.stop()
        st.session_state.results = dict(results)
        st.sleep(5)
        st.rerun()

    if "critic" not in results:
        with st.chat_message("assistant", avatar="🧐"):
            st.markdown('<div class="agent-tag">Critic Chain</div>', unsafe_allow_html=True)
            try:
                with st.spinner("Reviewing the report…"):
                    results["critic"] = critic_chain.invoke({"report": results["writer"]})
                st.session_state.results = dict(results)
            except  Exception as e:
                st.session_state.running=False
                st.error(f"crtic chain is failed {e}")
                st.stop()

    st.session_state.running = False
    st.session_state.done = True
    st.rerun()

# ── Download once complete ───────────────────────────────────────────────────
if st.session_state.done and "writer" in r:
    st.download_button(
        "⬇  Download Report (.md)",
        data=r["writer"],
        file_name=f"research_report_{int(time.time())}.md",
        mime="text/markdown",
    )
    if st.button("↺ Start new research"):
        st.session_state.results = {}
        st.session_state.running = False
        st.session_state.done = False
        st.session_state["topic_val"] = None
        st.rerun()
