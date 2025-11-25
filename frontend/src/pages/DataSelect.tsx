import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./DataSelect.css";

interface DataItem {
  id: number;
  name: string;
  provider: string;
  uploadDate: string;
  usageCount: number;
}

export default function DataSelect() {
  const navigate = useNavigate();
  const handleBack = () => navigate('/main');

  const [dataList, setDataList] = useState<DataItem[]>([]); // 여기서 초기화
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/data-list/", { credentials: "include" })
      .then(res => res.json())
      .then(json => {
        if(json.success) setDataList(json.data);
        else alert("데이터를 불러오는데 실패했습니다.");
      });
  }, []);

 const handleSelect = (id: number) => {
    setSelectedId(id);
  };

  return (
    <div className="data-select-screen">
      {/* 뒤로가기 버튼 */}
      <div className="component-148-wrapper">
        <button className="back-button" onClick={handleBack}>← 뒤로가기</button>
      </div>

      {/* 제목 */}
      <div className="text-wrapper-3">데이터 목록</div>
      <div className="text-wrapper-4">분석에 사용할 데이터를 선택해주세요.</div>

      {/* 데이터가 없으면 메시지 표시 */}
      {dataList.length === 0 ? (
        <div className="no-data">등록된 데이터가 없습니다.</div>
      ) : (
        <div className="div-wrapper-2">
          <div className="div-wrapper-3">
            <div className="table-wrapper">
              <div className="table">
                {/* 헤더 */}
                <div className="row-instance header" style={{ display: 'flex', gap: '10px', padding: '10px', borderBottom: '2px solid #0246cd', fontWeight: 'bold' }}>
                  <div className="cell-select">선택</div>
                  <div className="cell-flex">데이터명</div>
                  <div className="cell-flex">제공자</div>
                  <div className="cell-flex">업로드 날짜</div>
                  <div className="cell-flex">이용수</div>
                  <div className="cell-flex">상세</div>
                </div>

                {/* 데이터 행 */}
                {dataList.map(item => (
                  <div key={item.id} className="row-instance">
                    <div className="cell-select">
                      <input
                        type="radio"
                        name="selectedData"
                        checked={selectedId === item.id}
                        onChange={() => handleSelect(item.id)}
                      />
                    </div>
                    <div className="cell-flex">{item.name}</div>
                    <div className="cell-flex">{item.provider}</div>
                    <div className="cell-flex">{item.uploadDate}</div>
                    <div className="cell-flex">{item.usageCount}</div>
                    <div className="cell-flex" 
                        style={{ color: '#0246cd', cursor: 'pointer' }}
                        onClick={() => alert(`${item.name} 상세보기 클릭됨`)}>
                      상세 정보
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 분석 버튼 */}
      <div className="component-153-wrapper">
        <button 
          className="component-153-instance" 
          onClick={() => {
            if (selectedId !== null) navigate('/data-analysis')
            else alert("데이터를 선택해주세요.")
          }}
        >
          데이터 분석
        </button>
      </div>
    </div>
  );
}
