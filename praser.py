import pandas as pd
import json
import matplotlib.pyplot as plt
import sys

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

FILE_NAME = str(sys.argv[1])

symbols_mark = [
    {'key': '草', 'symbols': ['草']},
    {'key': '?', 'symbols': ['?', '？']},
    {'key': 'kksk/awsl', 'symbols': ['kksk', 'awsl']},
    {'key': 'anti', 'symbols': ['anti']}
]


def symbol_in_message(symbols, msg):
    for symbol in symbols:
        if symbol in msg.lower():
            return True
    return False


with open(FILE_NAME, 'r', encoding='utf-8') as file:
    data = file.read()
data = '[' + data[:-1] + ']'
data = json.loads(data)
df = pd.DataFrame(data)
df['time'] = df['time'].apply(lambda x: pd.Timestamp(x, unit='ms', tz='Asia/Shanghai'))
concat_list = []
for symbol_mark in symbols_mark:
    df[symbol_mark.get('key')] = df['text'].apply(lambda msg: symbol_in_message(symbol_mark.get('symbols'), msg))
    has_symbol_df = df[df[symbol_mark.get('key')]]
    symbol_final = has_symbol_df.groupby(pd.Grouper(key='time', freq='60s')).count()
    if len(symbol_final) > 0:
        concat_list.append(symbol_final[symbol_mark.get('key')])

final = pd.concat(concat_list, axis=1)
final.index = final.index.format(formatter=lambda x: x.strftime('%H:%M'))
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(final)
ax = final.plot()
ax.set_xticklabels(list(final.index[::5]))
ax.set_xticks(range(0, final.index.size, 5))
plt.show()
_ = input()
