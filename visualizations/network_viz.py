import networkx as nx
import matplotlib.pyplot as plt
from model.network import build_network
from model.parameters import load_parameters  # adjust import if needed

def plot_single_period_network():
    params = load_parameters()  # or hardcode small M, K, T=[1]
    net = build_network(params['M'], params['traditional_m_dict'], 
                    params['L'], params['K'], [1], seed=456)
    
    G = nx.DiGraph()
    for arc in net['regular_arcs']:
        if arc[2] == 1:  # only first time period
            u = f"{arc[0]}_{arc[3]}"
            v = f"{arc[1]}_{arc[3]}"
            G.add_edge(u, v)
    
    pos = nx.spring_layout(G, k=0.3)
    plt.figure(figsize=(14, 10))
    nx.draw(G, pos, with_labels=True, node_size=800, 
            node_color='lightblue', arrows=True, font_size=8)
    plt.title("CSAM Network - One Time Period (Simplified)")
    plt.savefig("visualizations/network_one_period.png", dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    plot_single_period_network()