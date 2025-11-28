import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

interface DataDetailType {
  id: number;
  name: string;
  provider: string;
  uploadDate: string;
  usageCount: number;
  catalog: string;
}

export default function DataDetail() {
  const { id } = useParams();
  const [detail, setDetail] = useState<DataDetailType | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/data-detail/${id}/`, { credentials: "include" })
      .then(res => res.json())
      .then(json => {
        if (json.success) setDetail(json.data);
        else alert("데이터를 불러오지 못했습니다!");
      });
  }, [id]);

  if (!detail) return <div>불러오는 중...🍡</div>;

  return (
    <div style={{ padding: "20px" }}>
      <h1>데이터 상세 정보</h1>

      <div style={{ marginTop: "20px", fontSize: "18px", lineHeight: "1.8" }}>
        <div><b>데이터명:</b> {detail.name}</div>
        <div><b>데이터 제공자:</b> {detail.provider}</div>
        <div><b>데이터 업로드 날짜:</b> {detail.uploadDate}</div>
        <div><b>데이터 이용수:</b> {detail.usageCount}</div>
        <div><b>제공 카탈로그:</b> {detail.catalog}</div>
      </div>
    </div>
  );
}
