import glob
import pandas as pd

'''
Bring together all the state DMV files into one CSV.
'''


def concatDMVfiles():
    fileNames = glob.glob("data/dmv??.csv")

    print("Combining the following files: ")
    for f in fileNames:
        print(f)

    df = pd.concat([pd.read_csv(x, index_col = 0) for x in fileNames], ignore_index=True)
    df.to_csv('data/allDMV.csv', encoding = 'utf-8')

    print('\a')


if __name__ == '__main__':
    concatDMVfiles()

