import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np


def create_graph(nodes_list, links_list):
    G = nx.DiGraph()
    for i in nodes_list:
        G.add_node(i)
    G.add_edges_from(links_list)
    return G


def get_number_of_outbound_links(links_list, node):
    return sum(1 for i in links_list if i[0] == node)


def get_number_of_inbound_links(links_list, node):
    return sum(1 for i in links_list if i[1] == node)


def get_nodes_points_to_me(links_list, me):
    return [i[0] for i in links_list if i[1] == me]


def get_nodes_me_points_to(links_list, me):
    return [i[1] for i in links_list if i[0] == me]


def check_stop(itt_1, itt_2):
    return all(abs(x - y) < 0.005 for x, y in zip(itt_1, itt_2))


def prepare_data_to_preview(page_ranks, nodes_list):
    for i in range(len(page_ranks)):
        page_ranks[i] = [round(pr, 3) for pr in page_ranks[i]]

    values = page_ranks[-1]
    sorted_indices = sorted(range(len(values)), key=lambda k: values[k])
    sorted_indices = [i + 1 for i in sorted_indices]
    sorted_indices.insert(0, "Ranks")

    nodes_list.insert(0, "nodes")
    for i in range(len(page_ranks)):
        page_ranks[i].insert(0, f"itr {i}")

    page_ranks.insert(0, nodes_list)
    page_ranks.append(sorted_indices)
    return page_ranks


def calc_page_ranks(g):
    page_ranks = []
    nodes_list = list(g.nodes())
    links_list = list(g.edges())
    num_of_nodes = len(nodes_list)

    # Calculate the number of outbound links for each node
    outbound_links_count = {node: get_number_of_outbound_links(links_list, node) for node in nodes_list}

    # Identify dangling nodes (nodes with no outbound links)
    dangling_nodes = [node for node in nodes_list if outbound_links_count[node] == 0]

    # Calculate the initial PageRank values
    initial_page_rank = 1 / num_of_nodes
    page_ranks.append([initial_page_rank] * num_of_nodes)

    # Calculate the constant term
    d = 0.85
    const = (1 - d) / num_of_nodes

    cur_itt = 0
    stop = False

    while not stop:
        iteration = []
        for i in range(len(page_ranks[cur_itt])):
            npm = get_nodes_points_to_me(links_list, nodes_list[i])

            # Adjust PageRank calculation for dangling nodes
            pr_over_c = sum(page_ranks[cur_itt][nodes_list.index(j)] / outbound_links_count[j] for j in npm)
            if dangling_nodes:
                pr_over_c += sum(page_ranks[cur_itt][nodes_list.index(j)] / num_of_nodes for j in dangling_nodes)

            pr = const + d * pr_over_c
            iteration.append(pr)

        page_ranks.append(iteration)
        cur_itt += 1
        stop = check_stop(page_ranks[cur_itt - 1], page_ranks[cur_itt])

    return prepare_data_to_preview(page_ranks, nodes_list)


def draw_graph(g, ax):
    pos = nx.spring_layout(g, seed=42)
    nx.draw(g, pos, ax=ax, with_labels=True, node_color='lightgreen', node_size=2000, edge_color='black', arrows=True,
            arrowsize=20)


def draw_table(ax, page_ranks):
    data = page_ranks
    columns = data[0]
    data = data[1:]

    df = pd.DataFrame(data, columns=columns)

    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.2)


def draw(g, page_ranks, canvas_frame):
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 6))
    draw_graph(g, ax0)
    draw_table(ax1, page_ranks)

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def on_calculate():
    try:
        nodes_list = list(map(int, nodes_entry.get().split(',')))
        links_list = eval(links_entry.get())

        graph = create_graph(nodes_list, links_list)
        ranks = calc_page_ranks(graph)
        draw(graph, ranks, canvas_frame)
    except Exception as e:
        messagebox.showerror("Error", str(e))


def open_matrix_window(matrix, multiplications):
    matrix_window = tk.Toplevel(root)
    matrix_window.title("Multiplication Process")
    matrix_window.geometry("600x800")

    text = tk.Text(matrix_window, font=("Courier", 12), padx=10, pady=10)
    text.pack(expand=True, fill=tk.BOTH)

    text.insert(tk.END, "Stochastic Matrix (Rounded to 3 decimals):\n\n")
    for row in matrix:
        formatted_row = "  ".join(f"{num:.3f}" for num in row) + "\n"
        text.insert(tk.END, formatted_row)

    text.insert(tk.END, "\nMultiplication Process:\n\n")

    text.insert(tk.END, f"Iteration 1:\n")
    text.insert(tk.END, f"        Matrix                       Vector          =         New Vector:\n")
    for i in range(len(multiplications[0]['matrix'])):
        matrix_row = "  ".join(f"{num:.3f}" for num in multiplications[0]['matrix'][i])
        vector_val = str(1/len(row))
        print(vector_val)
        new_vector_val = f"{multiplications[0]['prev_vector'][i]:.3f}"
        text.insert(tk.END, f"{matrix_row}           {vector_val}           =           {new_vector_val}\n")
    text.insert(tk.END, "\n")

    for step in multiplications:
        text.insert(tk.END, f"Iteration {step['iteration']+1}:\n")
        text.insert(tk.END, f"        Matrix                       Vector          =         New Vector:\n")
        for i in range(len(step['matrix'])):
            matrix_row = "  ".join(f"{num:.3f}" for num in step['matrix'][i])
            vector_val = f"{step['prev_vector'][i]:.3f}"
            new_vector_val = f"{step['new_vector'][i]:.3f}"
            text.insert(tk.END, f"{matrix_row}           {vector_val}           =           {new_vector_val}\n")
        text.insert(tk.END, "\n")


def show_matrix():
    try:
        nodes_list = list(map(int, nodes_entry.get().split(',')))
        links_list = eval(links_entry.get())

        graph = create_graph(nodes_list, links_list)
        matrix = create_stochastic_matrix(nodes_list, links_list)
        multiplications = create_multiplications(matrix)
        open_matrix_window(matrix, multiplications)
    except Exception as e:
        messagebox.showerror("Error", str(e))


def create_stochastic_matrix(nodes_list, links_list):
    def initialize_matrix_with_zeros(num_of_nodes):
        return [[0] * num_of_nodes for _ in range(num_of_nodes)]

    def initialize_matrix_with_value(num_of_nodes, val):
        return [[val] * num_of_nodes for _ in range(num_of_nodes)]

    def create_matrix_A(nodes_list, links_list):
        A = initialize_matrix_with_zeros(len(nodes_list))
        for i in range(len(nodes_list)):
            n = get_nodes_me_points_to(links_list, nodes_list[i])
            if n:
                const = 1 / len(n)
                for j in range(len(A)):
                    if j + 1 in n:
                        A[j][i] = const
            else:
                for j in range(len(A)):
                    A[j][i] = 1/len(nodes_list)
        return np.array(A)

    def create_matrix_B(nodes_list):
        num_of_nodes = len(nodes_list)
        B = initialize_matrix_with_value(num_of_nodes, 1)
        return (1 / num_of_nodes) * np.array(B)

    A = create_matrix_A(nodes_list, links_list)
    B = create_matrix_B(nodes_list)

    d = 0.85
    const = (1 - d)

    M = d * A + const * B
    return M


def create_initial_vector(num_of_nodes):
    return np.array([1 / num_of_nodes] * num_of_nodes)


def create_multiplications(matrix):
    num_of_nodes = len(matrix)
    v = create_initial_vector(num_of_nodes)
    prev_res = np.dot(matrix, v)
    stop = False
    iterations = []

    iteration_count = 0
    while not stop:
        iteration_count += 1
        results = np.dot(matrix, prev_res)
        iterations.append(
            {'iteration': iteration_count, 'matrix': matrix, 'prev_vector': prev_res, 'new_vector': results})
        stop = check_stop(prev_res, results)
        prev_res = results

    return iterations


root = tk.Tk()
root.title("PageRank Visualizer")
root.geometry("1000x700")

style = ttk.Style()
style.configure("TLabel", font=("Helvetica", 12))
style.configure("TEntry", font=("Helvetica", 12), padding=10)
style.configure("TButton", font=("Helvetica", 12, "bold"), padding=10)

frame = ttk.Frame(root, padding="20")
frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)

nodes_label = ttk.Label(frame, text="Nodes List (comma-separated):")
nodes_label.pack(side=tk.TOP, fill=tk.X, pady=5)

nodes_entry = ttk.Entry(frame)
nodes_entry.pack(side=tk.TOP, fill=tk.X, pady=5)

links_label = ttk.Label(frame, text="Links List (list of pairs, e.g., [[1,2],[2,3]]):")
links_label.pack(side=tk.TOP, fill=tk.X, pady=5)

links_entry = ttk.Entry(frame)
links_entry.pack(side=tk.TOP, fill=tk.X, pady=5)

calculate_button = ttk.Button(frame, text="Calculate", command=on_calculate)
calculate_button.pack(side=tk.TOP, fill=tk.X, pady=5)

matrix_button = ttk.Button(frame, text="Show Multiplication Process", command=show_matrix)
matrix_button.pack(side=tk.TOP, fill=tk.X, pady=5)

canvas_frame = ttk.Frame(root, padding="20")
canvas_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


root.mainloop()
