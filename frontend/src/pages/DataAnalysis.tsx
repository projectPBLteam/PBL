import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./DataAnalysis.css";

export default function DataAnalysis() {
    const navigate = useNavigate();
    const handleBack = () => navigate('/data-select');

    const [selectedStat, setSelectedStat] = useState<string>("평균");
    const statsOptions = ["평균", "중앙값", "최빈값"];

    // 분석 결과 (예시)
    const analysisResult = "데이터 분석 결과입니다.";

    // CSV 다운로드 함수
    const handleExportCSV = () => {
      const csvContent = `"${analysisResult}"`;
  
      // UTF-8 BOM 추가
      const bom = "\uFEFF";
  
      const blob = new Blob([bom + csvContent], { type: "text/csv;charset=utf-8;" });
  
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.href = url;
      link.setAttribute("download", "analysis_result.csv");
      link.click();
      URL.revokeObjectURL(url);
  };

    return (
        <div className="data-analysis-screen">
            <div className="component-66-wrapper">
                <button className="back-button" onClick={handleBack}>← 뒤로가기</button>
            </div>

            <div className="text-wrapper-4">데이터 이용</div>

            <div className="div-2">
                <div className="div-3">
                    <div className="text-wrapper-5">통계 선택</div>

                    <div className="div-4">
                        {statsOptions.map((stat) => (
                            <label key={stat} className="radio-option">
                                <input
                                    type="radio"
                                    name="statistics"
                                    value={stat}
                                    checked={selectedStat === stat}
                                    onChange={() => setSelectedStat(stat)}
                                />
                                {stat}
                            </label>
                        ))}
                    </div>

                    <div className="component-69-wrapper">
                        <button className="component-69-instance-component-69-2">
                            확인
                        </button>
                    </div>
                </div>

                <div className="div-5">
                    <div className="text-wrapper-6">통계 처리 결과</div>

                    <div className="div-6">
                        <div className="rectangle" />
                        <div className="text-wrapper-7">{analysisResult}</div>
                    </div>
                </div>
            </div>

            <div className="view-wrapper">
                <button
                    className="view-2-view-3"
                    onClick={handleExportCSV}
                >
                    결과 반출
                </button>
            </div>
        </div>
    );
};