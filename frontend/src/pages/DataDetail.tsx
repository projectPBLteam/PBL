import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import "./DataDetail.css";

interface DataDetailType {
  id: string;
  name: string;
  provider: string;
  uploadDate: string;
  usageCount: number;
  catalog: string;
}

export default function DataDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<DataDetailType | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError("데이터 ID가 없습니다.");
      setLoading(false);
      return;
    }

    // 데이터 상세 정보와 컬럼 목록을 동시에 가져오기
    Promise.all([
      fetch(`http://localhost:8000/api/data-detail/${id}/`, { credentials: "include" })
        .then(res => res.json()),
      fetch(`http://localhost:8000/api/data/${id}/columns/`, { credentials: "include" })
        .then(res => res.json())
    ])
      .then(([detailJson, columnsJson]) => {
        if (detailJson.success) {
          setDetail(detailJson.data);
        } else {
          setError(detailJson.message || "데이터를 불러오지 못했습니다!");
        }
        
        if (columnsJson.success) {
          setColumns(columnsJson.columns || []);
        }
        
        setLoading(false);
      })
      .catch(err => {
        setError("서버 오류가 발생했습니다.");
        setLoading(false);
        console.error(err);
      });
  }, [id]);

  const handleBack = () => navigate('/data-select');

  if (loading) {
    return (
      <div className="data-detail-screen">
        <div className="loading">불러오는 중...</div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="data-detail-screen">
        <div className="error-message">{error || "데이터를 찾을 수 없습니다."}</div>
        <button className="back-button" onClick={handleBack}>← 뒤로가기</button>
      </div>
    );
  }

  return (
    <div className="data-detail-screen">
      {/* 뒤로가기 버튼 */}
      <div className="component-148-wrapper">
        <button className="back-button" onClick={handleBack}>← 뒤로가기</button>
      </div>

      {/* 제목 */}
      <div className="text-wrapper-3">데이터 상세 정보</div>

      {/* 상세 정보 카드 */}
      <div className="detail-card">
        <div className="detail-item">
          <div className="detail-label">데이터명</div>
          <div className="detail-value">{detail.name}</div>
        </div>

        <div className="detail-item">
          <div className="detail-label">데이터 제공자</div>
          <div className="detail-value">{detail.provider}</div>
        </div>

        <div className="detail-item">
          <div className="detail-label">데이터 업로드 날짜</div>
          <div className="detail-value">{detail.uploadDate}</div>
        </div>

        <div className="detail-item">
          <div className="detail-label">데이터 이용 수</div>
          <div className="detail-value">{detail.usageCount}회</div>
        </div>

        <div className="detail-item">
          <div className="detail-label">제공 카탈로그</div>
          <div className="detail-value">
            {columns.length > 0 ? (
              <div className="columns-list">
                {columns.map((col, index) => (
                  <span key={index} className="column-tag">
                    {col}
                  </span>
                ))}
              </div>
            ) : (
              <div className="columns-loading">컬럼 정보를 불러오는 중...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
