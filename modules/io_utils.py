# csv파일 읽기
def read_csvfile(filename):
    df = pd.read_csv(filename, encoding='utf-8')
    return df.values.tolist()

    # input_data=[]
    # with open(filename, 'r', encoding='utf-8') as f:
    #     rdr = csv.reader(f)
    #     for line in rdr:
    #         input_data.append(line)
    # return input_data

# DB 테이블 만들기
def maketbl(input_string, conn, curs):
    global tableN
    # 데이터 크기, 이름 확인
    input_len=[]
    input_type=[]
    input_id=[]
    for l in input_string[0]:
        i_id = l
        i_len= len(l)
        input_id.append(i_id)
        input_len.append(i_len)

		#데이터 타입 확인
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
    #쿼리문 저장                
    query = f"CREATE TABLE userTable{tableN} ("
    
    for i in range(len(input_id)):
        col_def = f"{input_id[i]} {input_type[i]}"
        if input_type[i] == 'VARCHAR':
            col_def += f"(255)"  # 문자열이면 길이 설정
        query += col_def
        if i != len(input_id)-1:
            query += ", "
    query += ")"

    conn.commit()
    tableN += 1
    curs.execute(query)
    return 0
    
# DB table 정보 보내기
def insert_data(input_string, conn, curs, tableN):
    table_name = f"userTable{tableN}"
    input_id = []
    input_data = []

    for col in input_string[0]:
        input_id.append(col)
    for row in input_string[1:]:
        input_data.append(row)

    # 쿼리문 저장
    query = "INSERT INTO " + table_name + " ("
    for i in range(len(input_id)):
        query += input_id[i]
        if i != len(input_id) - 1:
            query += ", "
    query += ") VALUES ("
    for i in range(len(input_id)):
        query += "%s"
        if i != len(input_id) - 1:
            query += ", "
    query += ")"

    # 데이터 삽입
    for row in input_data:
        clean_row = [None if val in ['Null', 'null', '', None] else val for val in row]
        clean_row = [None if isinstance(val, str) and val == 'None' else val for val in clean_row]
        curs.execute(query, row)
        
    conn.commit()
    print(f"{len(input_data)}개의 데이터가 {table_name}에 삽입되었습니다.")
