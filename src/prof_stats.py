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
plt.plot([1, 2, 3, 4, 5, 6], [21.9,45.3,85.0,131.9, 307.6, 503.1], linestyle='-', marker='o', color='b')
plt.ylabel('memory')
plt.xlabel("task complexity")
plt.axis([0, 7, 0, 600])

plt.show()
