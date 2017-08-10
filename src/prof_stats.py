# import pstats
# p = pstats.Stats('profiler')
# p.strip_dirs().sort_stats(-1).print_stats()


import memory_profiler as mprof

import matplotlib.pyplot as plt
from matplotlib import rc


# import matplotlib.font_manager
# a = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
# print()
# for b in a:
#     b = b.split("/")
#     if 'erda' in b[len(b)-1]:
#         print(b)



# rc('font', family='Times New Roman')
# plt.plot([1, 2, 3, 4, 5, 6], [9.189,20.153,61.627,114.927, 321.948, 731.760], linestyle='-', marker='o', color='r')
# plt.ylabel('time')
# plt.xlabel("task complexity")
# plt.axis([0, 7, 0, 800])
#
# plt.show()
#
# plt.plot([1, 2, 3, 4, 5, 6], [21.9,45.3,85.0,131.9, 307.6, 503.1], linestyle='-', marker='o', color='b')
# plt.ylabel('memory')
# plt.xlabel("task complexity")
# plt.axis([0, 7, 0, 600])
#
# plt.show()


import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()
t = [1, 2, 3, 4, 5, 6, 7, 8]
s1 = [9.189,20.153,61.627,114.927, 321.948, 731.760, 15.343, 7.842]
ax1.plot(t, s1, linestyle='-', marker='o', color='r')
ax1.set_xlabel('task complexity')
# Make the y-axis label, ticks and tick labels match the line color.
ax1.set_ylabel('time', color='b')
ax1.tick_params('y', colors='b')

ax2 = ax1.twinx()
s2 = [21.9,45.3,85.0,131.9, 307.6, 503.1, 143.1, 49.7]
ax2.plot(t, s2, linestyle='-', marker='o', color='b')
ax2.set_ylabel('memory', color='r')
ax2.tick_params('y', colors='r')

fig.tight_layout()
plt.show()