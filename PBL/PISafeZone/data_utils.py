import pandas as pd
from django.db import connection # maketbl과 insert_data에서 커밋 처리를 위해 필요

def read_csvfile(file_object):
    """
    파일 객체를 Pandas로 읽어 컬럼명과 데이터 리스트를 반환합니다.
    (Django uploaded_file.file 객체 입력)
    파일 포인터 리셋과 인코딩/구분자 문제를 모두 처리합니다.
    """
    df = None

    # uploaded_file.file 객체는 pandas의 read_csv가 직접 처리 가능합니다.
    # 인코딩 문제 해결을 위해 cp949를 사용합니다.
    try:
        file_object.seek(0) # 👈 파일 포인터를 맨 처음으로 리셋 (필수!)
        # 명시적으로 쉼표 구분자(sep=',')를 지정합니다.
        df = pd.read_csv(file_object, encoding='utf-8', sep=',') 
    except Exception:
        pass # DecodeError, ParserError 등 모든 오류를 일단 통과

    if df is None or len(df.columns) == 0:
        try:
            file_object.seek(0) # 재시도 전에 파일 포인터를 다시 리셋 
            df = pd.read_csv(file_object, encoding='cp949', sep=',')
        except Exception:
            pass
        
    if df is None or len(df.columns) == 0:
        try:
            file_object.seek(0)
            df = pd.read_csv(file_object, encoding='utf-8', sep=';')
        except Exception as e:
            # 모든 시도가 실패했을 때 최종 오류를 발생시킵니다.
            raise ValueError(f"CSV 파일을 올바르게 파싱할 수 없습니다. 구분자 또는 데이터 구조를 확인하세요. (최종 오류: {e})")
        
    # Pandas DataFrame의 헤더와 데이터를 추출하여 [컬럼 리스트, 데이터 리스트...] 형태로 반환
    columns = list(df.columns)
    values = df.values.tolist()
    
    if len(columns) == 0:
        # 이 시점에도 컬럼이 0개라면 파일을 읽었지만 비어있는 경우이므로 명시적으로 오류 발생
        raise ValueError("파일에서 유효한 컬럼을 찾을 수 없습니다. 파일이 비어 있거나 헤더가 없는지 확인하세요.")
        
    return [columns] + values

def maketbl(input_string, curs, tablename): # conn 인수는 커서가 처리하므로 제거
    """
    CSV 헤더와 데이터 타입 추론을 기반으로 동적 테이블을 생성합니다.
    """
    input_id = []
    # input_type은 첫 번째 데이터 행을 보고 추론해야 하므로, 리스트로 미리 초기화합니다.
    input_type = [] 

    # 헤더(첫 번째 요소) 추출 및 컬럼 이름 정제
    for l in input_string[0]:
        # 컬럼 이름 정제: MySQL 예약어 및 특수 문자 충돌 방지
        safe_col = l.strip().replace(' ', '_').lower()
        input_id.append(safe_col)
        # 컬럼 길이 정보는 동적 SQL 생성에서 필요하지 않아 제거했습니다.
    
    # 데이터 타입 추론: 첫 번째 데이터 행(input_string[1])을 기준으로 타입을 추론합니다.
    if len(input_string) > 1:
        first_data_row = input_string[1]
        for value in first_data_row:
            try:
                # 숫자 변환을 시도하여 타입을 추론
                int(value)
                input_type.append('INT')
            except:
                try:
                    float(value)
                    input_type.append('FLOAT')
                except:
                    input_type.append('VARCHAR')
    else:
        # 데이터 행이 없으면 모두 VARCHAR로 처리
        input_type = ['VARCHAR'] * len(input_id)
        
    
    # CREATE TABLE 쿼리 생성
    # 테이블명과 컬럼명은 백틱(`)으로 감싸서 MySQL 예약어 충돌을 방지합니다.
    query = f"CREATE TABLE IF NOT EXISTS `{tablename}` (`id` INT AUTO_INCREMENT PRIMARY KEY, "
    for i in range(len(input_id)):
        col_def = f"`{input_id[i]}` {input_type[i]}"
        if input_type[i] == 'VARCHAR':
            col_def += "(255)"
        col_def += " NULL" # NULL 허용
        query += col_def
        if i != len(input_id) - 1:
            query += ", "
    query += ")"

    curs.execute(query)
    # conn.commit() # 커밋은 insert_data에서 일괄 처리합니다.
    return 0

def insert_data(input_string, curs, tablename): # conn 인수는 커서가 처리하므로 제거
    """
    생성된 테이블에 데이터를 삽입합니다.
    """
    input_id = [col.strip().replace(' ', '_').lower() for col in input_string[0]] # 컬럼명 정제
    input_data = input_string[1:]

    # INSERT INTO 쿼리 생성
    column_names_sql = ', '.join([f"`{col}`" for col in input_id])
    value_placeholders = ', '.join(['%s'] * len(input_id))
    query = f"INSERT INTO `{tablename}` ({column_names_sql}) VALUES ({value_placeholders})"

    # 데이터를 튜플 리스트로 변환하고 NULL 처리를 준비
    cleaned_data = []
    for row in input_data:
        # 튜플로 변환하고, 'Null', 'null', '' 값을 None으로 대체
        clean_row = tuple([None if str(val).strip().lower() in ['null', ''] else val for val in row])
        cleaned_data.append(clean_row)

    if cleaned_data:
        curs.executemany(query, cleaned_data) # executemany로 대량 삽입 (매우 빠름)
    
    # 커밋은 Django가 관리하므로, execute/executemany 후 자동으로 처리될 수도 있으나 명시적으로 호출
    # with connection.cursor() as cursor: 블록을 사용하므로 commit은 Django가 관리하지만, 명시적 커밋은 DB 작업이 복잡할 때 필요합니다.
    # 여기서는 Django의 트랜잭션 관리(ATOMIC_REQUESTS=True)에 맡기거나, 명시적으로 connection.commit()을 호출합니다.

    print(f"{len(input_data)}개의 데이터가 {tablename}에 삽입되었습니다.")