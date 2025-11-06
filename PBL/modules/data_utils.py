import pandas as pd
from django.db import connection

def read_csvfile(file_object):
    df = None

    # uploaded_file.file 객체는 pandas의 read_csv가 직접 처리 가능합니다.
    try:
        file_object.seek(0) #파일 포인터를 맨 처음으로 리셋(필수!)
        # 명시적으로 쉼표 구분자(sep=',')를 지정합니다.
        df = pd.read_csv(file_object, encoding='utf-8', sep=',') 
    except Exception:
        pass

    if df is None or len(df.columns) == 0:
        try:
            file_object.seek(0)
            df = pd.read_csv(file_object, encoding='cp949', sep=',')
        except Exception:
            pass
        
    if df is None or len(df.columns) == 0:
        try:
            file_object.seek(0)
            df = pd.read_csv(file_object, encoding='utf-8', sep=';')
        except Exception as e:
            # 모든 시도가 실패한 최종 오류 출력
            raise ValueError(f"CSV 파일을 올바르게 파싱할 수 없습니다. 구분자 또는 데이터 구조를 확인하세요. (오류: {e})")
        
    columns = list(df.columns)
    values = df.values.tolist()
    
    if len(columns) == 0:
        # 파일을 읽었지만 비어있는 경우
        raise ValueError("파일에서 유효한 컬럼을 찾을 수 없습니다. 파일이 비어 있거나 헤더가 없는지 확인하세요.")
        
    return [columns] + values

def maketbl(input_string, curs, tablename):
    input_id = []
    input_type = []
    id_col_index= -1

    for i, l in enumerate(input_string[0]):
        safe_col = l.strip().replace(' ', '_').lower()
        
        if not safe_col:
            raise ValueError(f"{i+1}번째 컬럼의 이름이 비어있습니다. CSV 파일을 확인해 주세요.")

        if len(safe_col) > 64:
            raise ValueError(f"컬럼 이름 '{l}'이(가) 너무 깁니다. 64자 이하로 줄여주세요.")
        
        if safe_col == 'id':
            id_col_index = i 
            continue

        input_id.append(safe_col)
    
    if len(input_string) > 1:
        first_data_row = input_string[1]
        for i, value in enumerate(first_data_row):
            if i == id_col_index:
                continue
            
            if pd.isna(value) or str(value).strip().lower() in ['null', '']:
                input_type.append('TEXT') 
                continue

            try:
                int_val = int(float(value)) 
                if abs(int_val) > 2147483647:
                    input_type.append('BIGINT')
                else:
                    input_type.append('INT')
            except:
                try:
                    float(value)
                    input_type.append('DOUBLE')
                except:
                    input_type.append('TEXT') 
    else:
        input_type = ['TEXT'] * len(input_id) 
        
    
    # CREATE TABLE 쿼리 생성
    query = f"CREATE TABLE IF NOT EXISTS `{tablename}` (`id` INT AUTO_INCREMENT PRIMARY KEY, "
    for i in range(len(input_id)):
        col_def = f"`{input_id[i]}` {input_type[i]} NULL" 
        
        query += col_def
        if i != len(input_id) - 1:
            query += ", "
    query += ")"

    curs.execute(query)
    return 0

def insert_data(input_string, curs, tablename):
    """
    생성된 테이블에 데이터를 삽입합니다.
    (id 무시, NaN/Null 처리, % 이스케이프 처리)
    """
    input_id = []
    input_data = input_string[1:]
    id_col_index = -1

    # 'id'를 제외한 컬럼 리스트(input_id)를 생성
    for i, col in enumerate(input_string[0]):
        safe_col = col.strip().replace(' ', '_').lower()
        if safe_col == 'id':
            id_col_index = i
            continue
        input_id.append(safe_col)

    # INSERT INTO 쿼리 생성
    column_names_sql = ', '.join([f"`{col}`" for col in input_id])
    value_placeholders = ', '.join(['%s'] * len(input_id))
    query = f"INSERT INTO `{tablename}` ({column_names_sql}) VALUES ({value_placeholders})"

    # 데이터를 튜플 리스트로 변환하고 NULL 처리 준비
    cleaned_data = []
    for row in input_data:
        # 'id' 컬럼의 데이터를 제외한 임시 리스트 생성
        temp_row = []
        for i, val in enumerate(row):
            if i == id_col_index:
                continue
            temp_row.append(val)

        processed_row = []
        for val in temp_row:
            # 1. NaN, 'null', '' 값을 None (NULL)으로 변환
            if pd.isna(val) or str(val).strip().lower() in ['null', '']:
                processed_row.append(None)
            # 2. 문자열일 경우, '%'를 '%%'로 치환 (DB 드라이버 오류 방지)
            elif isinstance(val, str):
                processed_row.append(val.replace('%', '%%'))
            # 3. 숫자나 다른 타입은 그대로 추가
            else:
                processed_row.append(val)
            
        clean_row = tuple(processed_row)
        cleaned_data.append(clean_row)

    if cleaned_data:
        curs.executemany(query, cleaned_data) # executemany로 대량 삽입
    
    print(f"{len(cleaned_data)}개의 데이터가 {tablename}에 삽입되었습니다.")