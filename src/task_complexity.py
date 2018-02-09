import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()
t = [1, 2, 3, 4, 5, 6]
s1 = [8940, 17, 6600, 4040, 160000, 5020]
ax1.plot(t, s1, linestyle='-', marker='o', color='gray')
ax1.set_xlabel('сложность задачи')
# Make the y-axis label, ticks and tick labels match the line color.
ax1.set_ylabel('время', color='gray')
ax1.tick_params('y', colors='gray')

ax2 = ax1.twinx()
s2 = [38.6, 33.3, 39.9, 62.1, 180.4, 69.5]
ax2.plot(t, s2, linestyle='-', marker='o', color='black')
ax2.set_ylabel('память', color='black')
ax2.tick_params('y', colors='black')

fig.tight_layout()
plt.show()