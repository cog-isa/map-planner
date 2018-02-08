import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import read_dot

G = nx.Graph(read_dot('Knowledge.dot'))

nx.draw(G)
plt.show()
