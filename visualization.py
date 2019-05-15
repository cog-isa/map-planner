import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
import numpy as np

x = [1, 2, 3, 4, 5]
y1 = [21, 28, 56, 62, 93]
y2 = [0.2, 1.4, 5.8, 7.2, 8.2]
y3 = [0.3, 1.2, 3.1, 4.2, 5.5]
y4 = [0.8, 1.3, 4.6, 6.3, 6.5]

plt.xticks(np.arange(min(x), max(x)+1, 1.0))
plt.xlabel('solved tasks')
plt.ylabel('time points')

line1, = plt.plot(x, y1, 'black', label='HierMAP without experience')
line2, = plt.plot(x, y2, 'gray', label='HierMAP with experience')
line3 = plt.plot(x, y3, 'black', linestyle='--', label='PANDA')
line4 = plt.plot(x, y4, 'gray', linestyle='-.', label='MIDCA')

plt.legend(handler_map={line1: HandlerLine2D(numpoints=4)})


plt.show()

