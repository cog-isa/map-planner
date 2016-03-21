import numpy as np
import matplotlib.pyplot as plt

ind = np.arange(3)
width = 0.35

steps = plt.subplot('211')
times = plt.subplot('212')
rects1 = steps.bar(ind, [6, 6, 6], align='center', width=0.35)
rects2 = steps.bar(ind + width, [10, 10, 10], align='center', color='y', width=0.35)
steps.set_xticks(ind + width / 2)
steps.set_xticklabels(('MAP', 'A*', 'W*'))
steps.set_ylim([0, 15])
steps.set_ylabel('Number of steps')
steps.set_title('Plan length by planners')
steps.legend((rects1[0], rects2[0]), ('Task 1', 'Task 2'))

rects1 = times.bar(ind, [0.22, 0.0077, 0.0068], align='center', width=width)
rects2 = times.bar(ind + width, [0.31, 0.0068, 0.0060], align='center', color='y', width=width)
times.set_xticks(ind + width / 2)
times.set_xticklabels(('MAP', 'A*', 'W*'))
times.set_ylim([0, 0.35])
times.set_ylabel('Nominal time units')
times.set_title('Plan generation duration by planners')
times.legend((rects1[0], rects2[0]), ('Task 1', 'Task 2'))

plt.show()
