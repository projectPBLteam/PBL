import { useCallback, useEffect, useMemo, useState, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./DataAnalysis.css";

interface NotificationProps {
  type: 'success' | 'error' | null;
  message: string;
}

function CustomNotification({ type, message }: NotificationProps) {
  if (!type || !message) return null;

  const style = {
    position: 'fixed' as 'fixed',
    top: '20px', 
    left: '50%', 
    transform: 'translateX(-50%)', 
    padding: '15px 25px',
    borderRadius: '8px',
    color: 'white',
    fontWeight: 'bold' as 'bold',
    zIndex: 1000,
    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
    backgroundColor: type === 'success' ? '#28a745' : '#dc3545', 
    transition: 'opacity 0.3s ease-in-out',
  };

  return (
    <div style={style}>
      {type === 'success' ? '✅ 성공: ' : '❌ 오류: '} {message}
    </div>
  );
}

const STAT_OPTIONS = [
    { label: "평균", value: "mean", type: "single" },
    { label: "중앙값", value: "median", type: "single" },
    { label: "최빈값", value: "mode", type: "single" },
    { label: "표본분산", value: "variance", type: "single" },
    { label: "표준편차", value: "std_dev", type: "single" },
    { label: "표준오차", value: "sem", type: "single" },
    { label: "선형회귀", value: "regression", type: "pair" },
    { label: "상관분석 (피어슨)", value: "correlation_p", type: "pair" },
    { label: "상관분석 (스피어만)", value: "correlation_s", type: "pair" },
] as const;

type AnalysisEntry = {
    id: number;
    timestamp: string;
    statLabel: string;
    columnsLabel: string;
    text: string;
    remaining: number | null;
};

const formatTimestamp = (date = new Date()) =>
    `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(
        date.getDate()
    ).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(
        date.getMinutes()
    ).padStart(2, "0")}:${String(date.getSeconds()).padStart(2, "0")}`;

export default function DataAnalysis() {
    const navigate = useNavigate();
    const location = useLocation();
    const dataId = location.state?.dataId;

    const [columns, setColumns] = useState<string[]>([]);
    const [selectedStat, setSelectedStat] = useState<string>(STAT_OPTIONS[0].value);
    const [selectedCol, setSelectedCol] = useState<string>("");
    const [selectedColY, setSelectedColY] = useState<string>("");
    const [selectedColX, setSelectedColX] = useState<string>("");
    const [resultHistory, setResultHistory] = useState<AnalysisEntry[]>([]);
    const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
    const [customCode, setCustomCode] = useState<string>("");
    const [customLog, setCustomLog] = useState<string>("");
    const [customStatus, setCustomStatus] = useState<string>("");
    const [showCustomConsole, setShowCustomConsole] = useState<boolean>(false);
    const hasIncrementedUsage = useRef<boolean>(false);
    const [notification, setNotification] = useState<NotificationProps>({ type: null, message: '' });

    
    const isPairStat = useMemo(
        () => STAT_OPTIONS.find((opt) => opt.value === selectedStat)?.type === "pair",
        [selectedStat]
    );

    const fetchColumns = useCallback(() => {
        if (!dataId) return;
        fetch(`http://localhost:8000/api/data/${dataId}/columns/`, {
            credentials: "include",
        })
            .then((res) => res.json())
            .then((json) => {
                if (!json.success) {
                    alert(json.message || "컬럼 정보를 불러오지 못했습니다.");
                    return;
                }
                const fetched: string[] = json.columns || [];
                setColumns(fetched);
                if (fetched.length > 0) {
                    setSelectedCol((prev) => prev || fetched[0]);
                    setSelectedColY((prev) => prev || fetched[0]);
                    const fallbackX = fetched.length > 1 ? fetched[1] : fetched[0];
                    setSelectedColX((prev) => prev || fallbackX);
                } else {
                    setSelectedCol("");
                    setSelectedColY("");
                    setSelectedColX("");
                }
            })
            .catch(() => alert("컬럼 정보를 불러오는 중 오류가 발생했습니다."));
    }, [dataId]);

    const fetchConsoleLog = useCallback(() => {
        if (!dataId) return;
        fetch(`http://localhost:8000/api/data/${dataId}/custom-console/`, {
            credentials: "include",
        })
            .then((res) => res.json())
            .then((json) => {
                if (json.success) {
                    setCustomLog(json.log || "");
                }
            })
            .catch(() => setCustomLog(""));
    }, [dataId]);

    useEffect(() => {
        if (!dataId) return;
        
        // 데이터 분석 화면 진입 시 이용 횟수 증가 (한 번만 실행)
        if (!hasIncrementedUsage.current) {
            hasIncrementedUsage.current = true;
            fetch(`http://localhost:8000/api/data/${dataId}/increment-usage/`, {
                method: "POST",
                credentials: "include",
            })
                .then((res) => res.json())
                .then((json) => {
                    if (!json.success) {
                        console.error("이용 횟수 증가 실패:", json.message);
                    } else {
                        console.log("이용 횟수 증가 성공:", json.usageCount);
                    }
                })
                .catch((err) => {
                    console.error("이용 횟수 증가 중 오류:", err);
                });
        }
        
        fetchColumns();
        fetchConsoleLog();
    }, [dataId, fetchColumns, fetchConsoleLog]);
    
    // dataId가 변경되면 hasIncrementedUsage 리셋
    useEffect(() => {
        hasIncrementedUsage.current = false;
    }, [dataId]);

    useEffect(() => {
        if (notification.type) {
            const timer = setTimeout(() => {
                // 성공적으로 반출되었으면 메인으로 이동
                if (notification.type === 'success') {
                    navigate('/main');
                } else {
                    // 오류인 경우 알림만 제거
                    setNotification({ type: null, message: '' });
                }
            }, 3000); 

            return () => clearTimeout(timer);
        }
    }, [notification, navigate]);

    const handleBack = () => navigate("/data-select");

    const validateSelections = () => {
        if (!dataId) {
            alert("유효한 데이터가 선택되지 않았습니다.");
            return false;
        }
        if (isPairStat) {
            if (!selectedColY || !selectedColX) {
                alert("Y/X 컬럼을 모두 선택해주세요.");
                return false;
            }
            if (selectedColY === selectedColX) {
                alert("Y와 X는 서로 다른 컬럼을 선택해야 합니다.");
                return false;
            }
        } else if (!selectedCol) {
            alert("컬럼을 선택해주세요.");
            return false;
        }
        return true;
    };

    const handleAnalyze = () => {
        if (!validateSelections() || !dataId) return;
        setIsAnalyzing(true);
        const payload: Record<string, string> = { stat: selectedStat };
        if (isPairStat) {
            payload.col_y = selectedColY;
            payload.col_x = selectedColX;
        } else if (selectedCol) {
            payload.col = selectedCol;
        }

        fetch(`http://localhost:8000/api/data/${dataId}/analyze/`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        })
            .then((res) => res.json())
            .then((json) => {
                if (json.success) {
                    const statMeta = STAT_OPTIONS.find((opt) => opt.value === selectedStat);
                    const statLabel = statMeta?.label ?? selectedStat;
                    const columnsLabel = isPairStat
                        ? `${selectedColY} vs ${selectedColX}`
                        : selectedCol;
                    const entry: AnalysisEntry = {
                        id: Date.now(),
                        timestamp: formatTimestamp(),
                        statLabel,
                        columnsLabel,
                        text: json.result ?? "결과 없음",
                        remaining:
                            typeof json.remaining === "number" ? json.remaining : null,
                    };
                    setResultHistory((prev) => [...prev, entry]);
                } else {
                    alert(json.message || "분석 중 오류가 발생했습니다.");
                }
            })
            .catch(() => alert("분석 중 오류가 발생했습니다."))
            .finally(() => setIsAnalyzing(false));
    };

    const handleRunCustomCode = () => {
        if (!dataId) {
            alert("데이터를 먼저 선택해주세요.");
            return;
        }
        
        // statistics_basic과 statistics_advanced 모듈의 모든 함수 사용 차단
        const blockedFunctions = [
            // statistics_basic 모듈 함수들
            'calculate_mean', 'calculate_median', 'calculate_mode',
            'calculate_range', 'calculate_variance', 'calculate_std_dev',
            'calculate_sem', 'calculate_kurtosis', 'calculate_skewness',
            'calculate_population_variance', 'calculate_population_std_dev',
            'print_column_statistics',
            // statistics_advanced 모듈 함수들
            'run_regression_analysis', 'run_correlation_analysis',
            'pearson_correlation', 'spearman_correlation',
            // 기타 (레거시)
            'Regression_Analysis', 'Correlation_Analysis'
        ];
        
        // Pandas 메서드와 Python 함수를 모두 포함한 차단 목록
        const fullBlockedList = [
            ...blockedFunctions,
            '.mean', '.median', '.mode', '.sum', '.min', '.max', '.std', '.var', '.corr', '.cov', '.describe'
        ];
        
        const codeLower = customCode.toLowerCase();
        const foundBlocked = fullBlockedList.find(func => {
            const funcLower = func.toLowerCase();
            
            // 띄어쓰기를 무시하고 검색하여 'df. mean'과 'df.mean' 모두 잡습니다.
            const codeCompact = codeLower.replace(/\s/g, ''); 
            const funcCompact = funcLower.replace(/\s/g, '');
            
            // Pandas 메서드 형태 (.mean 등)는 앞에 변수 이름이 붙는지 확인합니다.
            if (funcLower.startsWith('.')) {
                const regex = new RegExp(`[a-z0-9_]${funcCompact}`);
                return regex.test(codeCompact);
            }
            // 일반 Python 함수 이름 검사
            return codeCompact.includes(funcCompact);
        });

        if (foundBlocked) {
            // 차단 메시지를 구성
            const displayFunction = foundBlocked.startsWith('.') ? `df${foundBlocked}()` : foundBlocked;
            setCustomStatus(`'${displayFunction}'와 같은 분석 모듈 함수는 사용할 수 없습니다. 왼쪽 선택창에서 분석 옵션을 선택해주세요.`);
            return;
        }
        
        setCustomStatus("실행 중...");
        fetch(`http://localhost:8000/api/data/${dataId}/custom-console/`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: customCode }),
        })
            .then((res) => res.json())
            .then((json) => {
                if (json.success) {
                    setCustomStatus(json.message || "실행 완료");
                    setCustomLog(json.log || "");
                    if (!showCustomConsole) setShowCustomConsole(true);
                } else {
                    setCustomStatus(json.message || "실행 실패");
                }
            })
            .catch(() => setCustomStatus("실행 실패"));
    };

    const handleExportCSV = () => {
        setNotification({ type: null, message: '' }); // 알림 초기화
        
        // 반출할 데이터가 없는 경우 오류 알림
        if (resultHistory.length === 0) {
            setNotification({ type: 'error', message: "반출할 분석 결과 기록이 없습니다." });
            return;
        }
        
        const rows = resultHistory.map((entry) => {
            const safeText = String(entry.text).replace(/"/g, '""');
            return `"${entry.timestamp}","${entry.statLabel}","${entry.columnsLabel}","${safeText}"`;
        });
        const csvContent = ["timestamp,stat,columns,result", ...rows].join("\n");
        const bom = "\uFEFF";
        const blob = new Blob([bom + csvContent], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.href = url;
        link.setAttribute("download", "analysis_result.csv");
        link.click();
        URL.revokeObjectURL(url);
        
        // 결과 반출 시 사용한 분석 기록 초기화 및 쿼리 차감
        if (dataId) {
            fetch(`http://localhost:8000/api/data/${dataId}/reset-used-analyses/`, {
                method: "POST",
                credentials: "include",
            })
                .then((res) => res.json())
                .then((json) => {
                    if (json.success) {
                        console.log("사용한 분석 기록이 초기화되었습니다.");
                    }
                })
                .catch((err) => {
                    console.error("분석 기록 초기화 중 오류:", err);
                });
        }
        
        setNotification({ type: 'success', message: "결과 반출이 완료되었습니다. 메인 페이지로 이동합니다." });
    };

    // [renderColumnSelectors 함수 정의를 여기에 복원했습니다.]
    const renderColumnSelectors = () => {
        if (isPairStat) {
            return (
                <div className="column-pair-wrapper">
                    <div className="column-select-box">
                        <label className="column-label">종속 변수 (Y)</label>
                        <select
                            className="col-dropdown"
                            value={selectedColY}
                            onChange={(e) => setSelectedColY(e.target.value)}
                        >
                            {columns.map((col) => (
                                <option key={col} value={col}>
                                    {col}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="column-select-box">
                        <label className="column-label">독립 변수 (X)</label>
                        <select
                            className="col-dropdown"
                            value={selectedColX}
                            onChange={(e) => setSelectedColX(e.target.value)}
                        >
                            {columns.map((col) => (
                                <option key={col} value={col}>
                                    {col}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            );
        }

        return (
            <div className="column-select-box">
                <label className="column-label">컬럼 선택</label>
                <select
                    className="col-dropdown"
                    value={selectedCol}
                    onChange={(e) => setSelectedCol(e.target.value)}
                >
                    {columns.map((col) => (
                        <option key={col} value={col}>
                            {col}
                        </option>
                    ))}
                </select>
            </div>
        );
    };

    return (
        <div className="data-analysis-screen">
            <CustomNotification type={notification.type} message={notification.message} />
            <div className="component-66-wrapper">
                <button className="back-button" onClick={handleBack}>
                    ← 뒤로가기
                </button>
            </div>

            <div className="text-wrapper-4">데이터 이용</div>

            <div className="div-2">
                <div className="div-3">
                    <div className="text-wrapper-5">통계 옵션</div>

                    {renderColumnSelectors()}

                    <div className="div-4">
                        {STAT_OPTIONS.map((stat) => (
                            <label key={stat.value} className="radio-option">
                                <input
                                    type="radio"
                                    name="statistics"
                                    value={stat.value}
                                    checked={selectedStat === stat.value}
                                    onChange={() => setSelectedStat(stat.value)}
                                />
                                {stat.label}
                            </label>
                        ))}
                    </div>

                    <div className="component-69-wrapper">
                        <button
                            className="component-69-instance-component-69-2"
                            onClick={handleAnalyze}
                            disabled={isAnalyzing}
                        >
                            {isAnalyzing ? "분석 중..." : "확인"}
                        </button>
                    </div>
                </div>

                <div className="div-5">
                    <div className="text-wrapper-6">통계 처리 결과</div>

                    <div className="div-6">
                        <div className="rectangle" />
                        <div className="analysis-history">
                            {resultHistory.length === 0 ? (
                                <div className="analysis-entry empty">결과 없음</div>
                            ) : (
                                resultHistory.map((entry) => (
                                    <div key={entry.id} className="analysis-entry">
                                        <div className="analysis-entry-meta">
                                            <span className="meta-timestamp">{entry.timestamp}</span>
                                            <span className="meta-stat">{entry.statLabel}</span>
                                            <span className="meta-columns">{entry.columnsLabel}</span>
                                        </div>
                                        <div className="analysis-entry-text">{entry.text}</div>
                                        {entry.remaining !== null}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    <div className="custom-console-section">
                        <div className="custom-console-header">
                            <div>
                                <div className="custom-console-title">직접 코드 입력</div>
                                <div className="custom-console-hint">
                                    pandas DataFrame(df)와 numpy(np)를 사용할 수 있어요.
                                </div>
                            </div>
                            <button
                                className="toggle-console-btn"
                                onClick={() => setShowCustomConsole((prev) => !prev)}
                            >
                                {showCustomConsole ? "닫기" : "열기"}
                            </button>
                        </div>

                        {showCustomConsole && (
                            <>
                                <textarea
                                    className="custom-code-input"
                                    rows={6}
                                    placeholder="예) df.describe()"
                                    value={customCode}
                                    onChange={(e) => {
                                        const code = e.target.value;
                                        setCustomCode(code);
                                        // 분석 모듈 함수 사용 차단
                                        const blockedFunctions = [
                                            'calculate_mean', 'calculate_median', 'calculate_mode',
                                            'calculate_range', 'calculate_variance', 'calculate_std_dev',
                                            'calculate_sem', 'calculate_kurtosis', 'calculate_skewness',
                                            'calculate_population_variance', 'calculate_population_std_dev',
                                            'print_column_statistics', 'Regression_Analysis', 'Correlation_Analysis'
                                        ];
                                        const blockedPattern = ['.mean', '.median', '.mode', '.sum', '.min', '.max', '.std', '.var', '.corr', '.cov', '.describe'];
                                        
                                        const fullBlockedList = [...blockedFunctions, ...blockedPattern];
                                        const foundBlocked = fullBlockedList.find(func => {
                                            const codeCompact = codeLower.replace(/\s/g, ''); 
                                            const funcLower = func.toLowerCase();
                                            const funcCompact = funcLower.replace(/\s/g, '');
                                            
                                            // Pandas 메서드 형태 (.mean 등)는 앞에 변수 이름이 붙는지 확인합니다.
                                            if (funcLower.startsWith('.')) {
                                                const regex = new RegExp(`[a-z0-9_]${funcCompact}`);
                                                return regex.test(codeCompact);
                                            }
                                            // 일반 Python 함수 이름 검사
                                            return codeCompact.includes(funcCompact);
                                        });

                                        if (foundBlocked) {
                                            const displayFunction = foundBlocked.startsWith('.') ? `df${foundBlocked}()` : foundBlocked;
                                            setCustomStatus(`'${displayFunction}'와 같은 분석 모듈 함수는 사용할 수 없습니다. 왼쪽 선택창에서 분석 옵션을 선택해주세요.`);
                                        } else {
                                            setCustomStatus("");
                                        }
                                    }}
                                />
                                {/* RED ERROR DISPLAY (Long Message) */}
                                {customStatus && customStatus.includes("분석 모듈 함수") && (
                                    <div style={{ color: '#dc3545', fontSize: '12px', marginTop: '4px' }}>
                                        {customStatus} 
                                    </div>
                                )}
                                <div className="custom-console-actions">
                                    <button
                                        className="run-code-btn"
                                        onClick={handleRunCustomCode}
                                        disabled={!!customStatus.includes("분석 모듈 함수")}
                                    >
                                        실행
                                    </button>
                                    <span className="custom-status">
                                            {/* BLUE STATUS DISPLAY (Short Message) */}
                                            {customStatus && customStatus.includes("분석 모듈 함수") 
                                                ? "실행 실패" // 긴 메시지일 경우 "실행 실패"로 대체
                                                : customStatus}
                                        </span>
                                </div>
                                <div className="custom-log">
                                    {customLog ? <pre>{customLog}</pre> : "실행 기록이 없습니다."}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>

            <div className="view-wrapper">
                <button className="view-2-view-3" onClick={handleExportCSV}>
                    결과 반출
                </button>
            </div>
        </div>
    );
}