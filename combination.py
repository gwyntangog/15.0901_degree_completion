import pandas as pd

uni_data = pd.read_excel('uni_mining.xlsx')
uni_data.columns = uni_data.iloc[0]
print(uni_data['Institution type'].unique())
uni_data = uni_data[uni_data['Institution type']=='Universities']
print(uni_data.columns)
