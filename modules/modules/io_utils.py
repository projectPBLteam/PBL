import pandas as pd

def read_csvfile(filename):
    df = pd.read_csv(filename, encoding='cp949')
    columns = list(df.columns)
    values = df.values.tolist()
    return [columns] + values

def maketbl(input_string, conn, curs, tablename):
    input_len = []
    input_type = []
    input_id = []

    for l in input_string[0]:
        i_id = l
        i_len = len(str(l))
        input_id.append(i_id)
        input_len.append(i_len)

    for value in input_string[1]:
        try:
            int(value)
            input_type.append('INT')
        except:
            try:
                float(value)
                input_type.append('FLOAT')
            except:
                input_type.append('VARCHAR')

    query = f"CREATE TABLE IF NOT EXISTS {tablename} ("
    for i in range(len(input_id)):
        col_def = f"{input_id[i]} {input_type[i]}"
        if input_type[i] == 'VARCHAR':
            col_def += "(255)"
        query += col_def
        if i != len(input_id) - 1:
            query += ", "
    query += ")"

    curs.execute(query)
    conn.commit()
    return 0

def insert_data(input_string, conn, curs, tablename):
    input_id = input_string[0]
    input_data = input_string[1:]

    query = f"INSERT INTO {tablename} ({', '.join(input_id)}) VALUES ({', '.join(['%s'] * len(input_id))})"

    for row in input_data:
        clean_row = [None if val in ['Null', 'null', '', None] else val for val in row]
        curs.execute(query, clean_row)

    conn.commit()
    print(f"{len(input_data)}개의 데이터가 {tablename}에 삽입되었습니다.")
