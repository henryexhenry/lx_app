import pandas as pd

students_df = pd.read_csv('students.csv')

print(students_df.columns)



print(students_df["学员别名"].value_counts())
# print(students_df["学员别名"].count())
# print(students_df["nickname"])