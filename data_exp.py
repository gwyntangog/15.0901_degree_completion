import pandas as pd

master = pd.read_csv("school_level_clean_2021-2025.csv")
filter_1  = master[(master["CIP_Code"]==15.0901) & (master["Award_Level"] =="Certificates of less than 12 weeks")]
filter_1 = filter_1[["Year","Institution","Completions"]]
# print(filter_1)
# Answer: Illinois Eastern started offering the program

filter_2  = master[(master["CIP_Code"]==15.0901) & (master["Institution"] =="Illinois Eastern Community Colleges")]
filter_2 = filter_2[["Year","Award_Level","Completions"]]
# Answer: Illinois Eastern did not previously have it.
# print(filter_2)

filter_3  = master[(master["CIP_Code"]==15.0901) &  (master["Award_Level"] =="Associate's degree")]
filter_3 = filter_3[["Year","Institution","Completions"]]
# Answer: 1 graduate from Illinois Eastern Community Colleges and 1 graduate from Southwest Virginia Community College.
# print(filter_3)

filter_4  = master[(master["CIP_Code"]==15.0999) &  (master["Award_Level"] =="Associate's degree")]
filter_4 = filter_4[["Year","Institution","Completions"]]
# Answer: 1 graduate from Illinois Eastern Community Colleges and 1 graduate from Southwest Virginia Community College.
print(filter_4)
