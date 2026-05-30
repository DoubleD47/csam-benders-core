import networkx as nx
import matplotlib.pyplot as plt
from model.network import build_network
from model.parameters import get_default_params

def plot_improved_network():
    params = get_default_params()
    net = build_network(params['M'], params['traditional_m_dict'], 
                       params['L'], params['K'], [1], seed=456)
    
    G = nx.DiGraph()
    
    # Color coding
    node_colors = []
    labels = {}
    
    for arc in net['regular_arcs']:
        if arc[2] == 1:   # only t=1
            u = f"{arc[0]}_{arc[3][1]}"   # simplify label with k only
            v = f"{arc[1]}_{arc[3][1]}"
            G.add_edge(u, v)
            
            # Color by type
            if 'source' in u: color = 'green'
            elif 'sink' in u or 'ss' in u: color = 'red'
            elif 'dummy' in u: color = 'gray'
            elif '_q_l1' in u: color = 'orange'
            elif '_q_l2' in u: color = 'purple'
            elif '_in' in u: color = 'lightblue'
            else: color = 'lightgray'
            node_colors.append(color)
    
    plt.figure(figsize=(18, 12))
    pos = nx.spring_layout(G, k=0.35, iterations=80, seed=42)
    
    nx.draw(G, pos, with_labels=True, node_color=node_colors, 
            node_size=650, arrows=True, font_size=7, alpha=0.85)
    
    plt.title("CSAM Network — Time Period 1\n(Orange=l1 queue, Purple=l2 queue, Blue=entry points)")
    plt.savefig("visualizations/network_one_period_improved.png", dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    plot_improved_network()