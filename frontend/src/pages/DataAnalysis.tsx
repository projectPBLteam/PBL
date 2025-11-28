import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./DataAnalysis.css";

export default function DataAnalysis() {
    const navigate = useNavigate();
    const handleBack = () => navigate('/data-select');

    // 뒤 화면에서 dataId 넘겨받기
    const location = useLocation();
    const dataId = location.state?.dataId;

    const [columns, setColumns] = useState<string[]>([]);
    const [selectedCol, setSelectedCol] = useState<string>("");
    const [selectedStat, setSelectedStat] = useState<string>("평균");
    const statsOptions = ["평균", "중앙값", "최빈값"];
    const [analysisResult, setAnalysisResult] = useState<string>("");

    // 🚨 페이지 들어오면 컬럼 목록 가져오기
    useEffect(() => {
        if (!dataId) return;

        fetch(`http://localhost:8000/api/data/${dataId}/columns/`, {
            credentials: "include",
        })
            .then((res) => res.json())
            .then((json) => {
                if (json.success) {
                    setColumns(json.columns);
                    if (json.columns.length > 0) {
                        setSelectedCol(json.columns[0]);
                    }
                } else {
                    alert(json.message);
                }
            })
            .catch(() => {
                alert("컬럼 정보를 불러오는 중 오류가 발생했습니다.");
            });
    }, [dataId]);

    // 🎯 통계 요청 함수
    const handleAnalyze = () => {
        if (!selectedCol) {
            alert("컬럼을 선택해주세요.");
            return;
        }

        const statMap: any = {
            "평균": "mean",
            "중앙값": "median",
            "최빈값": "mode"
        };

        fetch(`http://localhost:8000/api/data/${dataId}/analyze/`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                stat: statMap[selectedStat],
                col: selectedCol
            }),
        })
            .then((res) => res.json())
            .then((json) => {
                if (json.success) {
                    setAnalysisResult(json.result);
                } else {
                    alert(json.message);
                }
            })
            .catch(() => {
                alert("분석 중 오류가 발생했습니다.");
            });
    };

    // CSV 다운로드 함수
    const handleExportCSV = () => {
        const csvContent = `"${analysisResult}"`;
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

                    {/* 📌 컬럼 선택 추가!! */}
                    <div className="column-select-box">
                        <label className="text-wrapper-5">컬럼 선택</label>
                        <select
                            className="col-dropdown"
                            value={selectedCol}
                            onChange={(e) => setSelectedCol(e.target.value)}
                        >
                            {columns.map((col) => (
                                <option key={col} value={col}>{col}</option>
                            ))}
                        </select>
                    </div>

                    {/* 📌 통계 선택 라디오 버튼 */}
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

                    {/* 🎯 분석 버튼 */}
                    <div className="component-69-wrapper">
                        <button
                            className="component-69-instance-component-69-2"
                            onClick={handleAnalyze}
                        >
                            확인
                        </button>
                    </div>
                </div>

                {/* 결과 */}
                <div className="div-5">
                    <div className="text-wrapper-6">통계 처리 결과</div>

                    <div className="div-6">
                        <div className="rectangle" />
                        <div className="text-wrapper-7">
                            {analysisResult || "결과 없음"}
                        </div>
                    </div>
                </div>
            </div>

            {/* CSV 다운로드 */}
            <div className="view-wrapper">
                <button className="view-2-view-3" onClick={handleExportCSV}>
                    결과 반출
                </button>
            </div>
        </div>
    );
}
