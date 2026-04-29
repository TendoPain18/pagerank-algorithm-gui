import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PageRank Visualizer",
    page_icon="🌐",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

/* Dark background */
.stApp {
    background-color: #0d0f14;
    color: #e8eaf0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #12151c;
    border-right: 1px solid #1e2330;
}

/* Title */
h1 {
    font-family: 'JetBrains Mono', monospace !important;
    color: #4fffb0 !important;
    letter-spacing: -1px;
}

h2, h3 {
    color: #a0f0cd !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* Cards / containers */
.metric-card {
    background: #12151c;
    border: 1px solid #1e2330;
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
}

.rank-badge {
    display: inline-block;
    background: linear-gradient(135deg, #4fffb0, #00c9ff);
    color: #0d0f14;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 13px;
    border-radius: 6px;
    padding: 2px 10px;
    margin-right: 6px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #4fffb0, #00c9ff);
    color: #0d0f14;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 15px;
    width: 100%;
    transition: opacity .2s;
}
.stButton > button:hover { opacity: .85; }

/* Input boxes */
.stTextInput input, .stTextArea textarea {
    background: #12151c !important;
    border: 1px solid #1e2330 !important;
    color: #e8eaf0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 8px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #12151c !important;
    color: #4fffb0 !important;
    border: 1px solid #1e2330 !important;
    border-radius: 8px !important;
}

/* DataFrame */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* Divider colour */
hr { border-color: #1e2330 !important; }

/* Selectbox */
.stSelectbox div[data-baseweb="select"] > div {
    background: #12151c !important;
    border: 1px solid #1e2330 !important;
    color: #e8eaf0 !important;
}

/* Info / warning boxes */
.stAlert { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)


# ── Core logic (ported from original tkinter app) ─────────────────────────────

def create_graph(nodes_list, links_list):
    G = nx.DiGraph()
    for i in nodes_list:
        G.add_node(i)
    G.add_edges_from(links_list)
    return G


def get_number_of_outbound_links(links_list, node):
    return sum(1 for i in links_list if i[0] == node)


def get_nodes_points_to_me(links_list, me):
    return [i[0] for i in links_list if i[1] == me]


def get_nodes_me_points_to(links_list, me):
    return [i[1] for i in links_list if i[0] == me]


def check_stop(itt_1, itt_2):
    return all(abs(x - y) < 0.005 for x, y in zip(itt_1, itt_2))


def calc_page_ranks(g):
    page_ranks = []
    nodes_list = list(g.nodes())
    links_list = list(g.edges())
    num_of_nodes = len(nodes_list)

    outbound_links_count = {node: get_number_of_outbound_links(links_list, node) for node in nodes_list}
    dangling_nodes = [node for node in nodes_list if outbound_links_count[node] == 0]

    initial_page_rank = 1 / num_of_nodes
    page_ranks.append([initial_page_rank] * num_of_nodes)

    d = 0.85
    const = (1 - d) / num_of_nodes

    cur_itt = 0
    stop = False

    while not stop:
        iteration = []
        for i in range(len(page_ranks[cur_itt])):
            npm = get_nodes_points_to_me(links_list, nodes_list[i])
            pr_over_c = sum(
                page_ranks[cur_itt][nodes_list.index(j)] / outbound_links_count[j] for j in npm
            )
            if dangling_nodes:
                pr_over_c += sum(
                    page_ranks[cur_itt][nodes_list.index(j)] / num_of_nodes for j in dangling_nodes
                )
            pr = const + d * pr_over_c
            iteration.append(pr)

        page_ranks.append(iteration)
        cur_itt += 1
        stop = check_stop(page_ranks[cur_itt - 1], page_ranks[cur_itt])

    return nodes_list, page_ranks


def create_stochastic_matrix(nodes_list, links_list):
    n = len(nodes_list)
    A = np.zeros((n, n))
    for i in range(n):
        targets = get_nodes_me_points_to(links_list, nodes_list[i])
        if targets:
            c = 1 / len(targets)
            for j in range(n):
                if nodes_list[j] in targets:
                    A[j][i] = c
        else:
            for j in range(n):
                A[j][i] = 1 / n

    B = np.full((n, n), 1 / n)
    d = 0.85
    M = d * A + (1 - d) * B
    return M


# ── Graph drawing ─────────────────────────────────────────────────────────────

def draw_graph_fig(g, final_ranks, nodes_list):
    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_facecolor('#0d0f14')
    ax.set_facecolor('#0d0f14')

    pos = nx.spring_layout(g, seed=42)

    # Node colour by rank (green gradient)
    ranks = np.array(final_ranks)
    norm_ranks = (ranks - ranks.min()) / (ranks.max() - ranks.min() + 1e-9)
    node_colors = [plt.cm.YlGn(0.35 + 0.65 * r) for r in norm_ranks]

    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=node_colors,
                           node_size=2200, alpha=0.95)
    nx.draw_networkx_labels(g, pos, ax=ax,
                            labels={n: str(n) for n in g.nodes()},
                            font_color='#0d0f14', font_size=13, font_weight='bold')
    nx.draw_networkx_edges(g, pos, ax=ax, edge_color='#4fffb0', arrows=True,
                           arrowsize=20, width=1.6,
                           connectionstyle='arc3,rad=0.08',
                           node_size=2200)

    # PR labels beside nodes
    pr_labels = {nodes_list[i]: f"  PR={final_ranks[i]:.3f}" for i in range(len(nodes_list))}
    nx.draw_networkx_labels(g, pos, ax=ax, labels=pr_labels,
                            font_color='#a0f0cd', font_size=9,
                            verticalalignment='bottom')

    ax.axis('off')
    plt.tight_layout()
    return fig


def draw_convergence_fig(nodes_list, page_ranks):
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('#0d0f14')
    ax.set_facecolor('#12151c')
    ax.spines[:].set_color('#1e2330')
    ax.tick_params(colors='#9098b0')

    colors = plt.cm.cool(np.linspace(0, 1, len(nodes_list)))
    for i, node in enumerate(nodes_list):
        values = [pr[i] for pr in page_ranks]
        ax.plot(values, label=f"Node {node}", color=colors[i],
                linewidth=2, marker='o', markersize=4)

    ax.set_xlabel("Iteration", color='#9098b0', fontsize=11)
    ax.set_ylabel("PageRank", color='#9098b0', fontsize=11)
    ax.set_title("Convergence of PageRank per Node", color='#4fffb0',
                 fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', framealpha=0.2, labelcolor='#e8eaf0',
              facecolor='#12151c', edgecolor='#1e2330', fontsize=9)
    ax.grid(axis='y', color='#1e2330', linewidth=0.8)
    plt.tight_layout()
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.markdown("## 🌐 PageRank Visualizer")
st.sidebar.markdown("---")

preset = st.sidebar.selectbox("📦 Load a Preset Graph", [
    "Custom",
    "Simple 4-node web",
    "6-node with dangling",
    "Large 10-node network",
])

PRESETS = {
    "Simple 4-node web": {
        "nodes": "1,2,3,4",
        "links": "[[1,2],[1,3],[2,4],[3,4],[4,1],[3,2]]",
    },
    "6-node with dangling": {
        "nodes": "1,2,3,4,5,6",
        "links": "[[1,2],[1,3],[2,4],[3,4],[4,5],[5,6],[6,1],[3,5]]",
    },
    "Large 10-node network": {
        "nodes": "1,2,3,4,5,6,7,8,9,10",
        "links": ("[[1,2],[1,3],[2,4],[2,5],[3,5],[3,6],[4,7],[4,8],"
                  "[5,8],[5,9],[6,9],[6,10],[7,1],[8,2],[9,3],[10,4],"
                  "[1,6],[7,9],[10,5],[3,8]]"),
    },
}

if preset != "Custom":
    default_nodes = PRESETS[preset]["nodes"]
    default_links = PRESETS[preset]["links"]
else:
    default_nodes = "1,2,3,4"
    default_links = "[[1,2],[2,3],[3,1],[1,4],[4,2]]"

st.sidebar.markdown("### ✏️ Graph Input")
nodes_input = st.sidebar.text_input("Nodes (comma-separated)", value=default_nodes)
links_input = st.sidebar.text_area("Links (list of pairs)", value=default_links, height=120)

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Format Help")
st.sidebar.markdown("""
- **Nodes**: `1,2,3,4`  
- **Links**: `[[1,2],[2,3],[3,1]]`  
  Each pair is `[from, to]` (directed edge).
""")

run = st.sidebar.button("⚡ Calculate PageRank")

# ── Main layout ───────────────────────────────────────────────────────────────

st.markdown("# 🌐 PageRank Visualizer")
st.markdown("Interactive implementation of the **Google PageRank algorithm** with convergence analysis and stochastic matrix inspection.")
st.markdown("---")

if run:
    try:
        nodes_list = list(map(int, nodes_input.split(',')))
        links_list = eval(links_input)

        g = create_graph(nodes_list, links_list)
        nodes_list_ordered, page_ranks = calc_page_ranks(g)
        final_ranks = page_ranks[-1]

        # ── Top metrics ──────────────────────────────────────────────────────
        sorted_indices = sorted(range(len(final_ranks)), key=lambda k: final_ranks[k], reverse=True)
        top_node = nodes_list_ordered[sorted_indices[0]]
        top_pr = final_ranks[sorted_indices[0]]
        n_iters = len(page_ranks) - 1

        col1, col2, col3 = st.columns(3)
        col1.metric("🏆 Top Node", f"Node {top_node}", f"PR = {top_pr:.4f}")
        col2.metric("🔄 Iterations to Converge", n_iters)
        col3.metric("📌 Nodes / Edges", f"{g.number_of_nodes()} / {g.number_of_edges()}")

        st.markdown("---")

        # ── Graph + Convergence ───────────────────────────────────────────────
        col_g, col_c = st.columns([1, 1])

        with col_g:
            st.markdown("### 🗺️ Graph Visualization")
            fig_g = draw_graph_fig(g, final_ranks, nodes_list_ordered)
            st.pyplot(fig_g, use_container_width=True)

        with col_c:
            st.markdown("### 📈 Convergence")
            fig_conv = draw_convergence_fig(nodes_list_ordered, page_ranks)
            st.pyplot(fig_conv, use_container_width=True)

        st.markdown("---")

        # ── Rankings ─────────────────────────────────────────────────────────
        st.markdown("### 🏅 Final Rankings")
        rank_cols = st.columns(min(len(nodes_list_ordered), 5))
        for rank_pos, idx in enumerate(sorted_indices):
            col = rank_cols[rank_pos % len(rank_cols)]
            node = nodes_list_ordered[idx]
            pr = final_ranks[idx]
            col.markdown(f"""
            <div class="metric-card" style="text-align:center">
                <span class="rank-badge">#{rank_pos+1}</span><br/>
                <span style="font-size:22px;font-weight:700;color:#4fffb0">Node {node}</span><br/>
                <span style="font-family:'JetBrains Mono';color:#9098b0;font-size:14px">PR = {pr:.5f}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Iteration table ───────────────────────────────────────────────────
        st.markdown("### 📋 Iteration Table")
        rows = {}
        for i, pr_list in enumerate(page_ranks):
            label = "Initial" if i == 0 else f"Iter {i}"
            rows[label] = {f"Node {nodes_list_ordered[j]}": round(pr_list[j], 5)
                           for j in range(len(nodes_list_ordered))}

        df = pd.DataFrame(rows).T
        df.index.name = "Iteration"
        st.dataframe(df.style.background_gradient(cmap='YlGn', axis=1), use_container_width=True)

        # ── Stochastic matrix ─────────────────────────────────────────────────
        with st.expander("🔢 Show Stochastic Matrix (Google Matrix)"):
            M = create_stochastic_matrix(nodes_list_ordered, list(g.edges()))
            col_labels = [f"Node {n}" for n in nodes_list_ordered]
            df_m = pd.DataFrame(np.round(M, 4),
                                index=col_labels, columns=col_labels)
            st.dataframe(df_m.style.background_gradient(cmap='Blues'), use_container_width=True)
            st.caption("M = 0.85 × A + 0.15 × B   (damping factor d = 0.85)")

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.info("Check your input format. Nodes: `1,2,3,4` — Links: `[[1,2],[2,3],[3,1]]`")

else:
    st.info("👈 Enter your graph in the sidebar and click **Calculate PageRank** to begin.")

    st.markdown("### How PageRank Works")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color:#4fffb0">📌 Core Idea</h4>
        A page is important if many important pages link to it. PageRank is computed iteratively until convergence.
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color:#4fffb0">🔢 Formula</h4>
        <code style="color:#a0f0cd">PR(u) = (1-d)/N + d × Σ PR(v)/L(v)</code><br/>
        d = 0.85 (damping factor), L(v) = outbound links of v
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color:#4fffb0">🎲 Dangling Nodes</h4>
        Nodes with no outbound links distribute their rank equally to all nodes in the graph.
        </div>
        """, unsafe_allow_html=True)