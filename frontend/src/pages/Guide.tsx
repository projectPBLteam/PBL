{/*.csv 파일인지 검증하는 코드 추가*/}
import { useRef, useState } from 'react'
import { useNavigate } from "react-router-dom"
import "./Guide.css"

export default function DataUpload() {
  const navigate = useNavigate()
  const handleBack = () => {
    navigate('/main')
  }

  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [fileName, setFileName] = useState('')
  const [fileSelected, setFileSelected] = useState(false)

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const name = file.name.trim().toLowerCase(); // 공백 제거 + 소문자 변환
  
      if (!name.endsWith(".csv")) {
        alert(".csv 파일만 업로드할 수 있습니다.");
        // 파일 입력 초기화
        e.target.value = "";
        setFileName("");
        setFileSelected(false);
        return;
      }
  
      // 통과 시 상태 업데이트
      setFileName(file.name);
      setFileSelected(true);
    }
  };
  const handleComplete = () => {
    alert("데이터가 업로드되었습니다.")
    navigate('/main')
  }

  return (
        <div className="guide-screen">
            <div className="component-51-wrapper">
                <button className="back-button" onClick={handleBack}>← 뒤로가기</button>
            </div>

            <div className="text-wrapper-2">개인정보 이노베이션 존 이용 안내</div>

            <div className="div-2">
                <div className="div-3">
                    <div className="text-wrapper-3">개인정보 이노베이션 존 안내 사항</div>
                    <div className="frame">
                        <div className="frame-2">
                            <div className="text-wrapper-4">'개인정보 이노베이션 존'은 제로 트러스트(Zero Trust) 원칙을 기반으로 유연한 개인·가명정보 활용, 개인정보 보호·활용기술 실증 등 개인정보 처리에 필요한 안전한 이용환경을 지원하여 안전성을 보장하는 공간입니다.
                                오프라인 폐쇄망으로만 진행되던 기존의 분석 환경에서 벗어나 차분 프라이버시를 이용하여 온라인에서도 안전한 개인정보 활용을 지원하고자 합니다.</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div className="upload-container" style={{ margin: '20px auto', display: 'flex', gap: '15px', alignItems: 'center' }}>
                
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                    accept=".csv"
                />

                <button
                    onClick={handleUploadClick}
                    style={{ padding: '10px 20px', backgroundColor: '#e0e0e0', border: '1px solid #ccc', borderRadius: '5px' }}
                >
                    파일 선택 (.csv)
                </button>
                <div 
                    style={{ 
                        padding: '10px', 
                        border: '1px solid #ccc', 
                        borderRadius: '5px', 
                        minWidth: '200px', 
                        textAlign: 'center',
                        color: fileSelected ? '#000' : '#888'
                    }}
                >
                    {fileName || "선택된 파일 없음"}
                </div>
            </div>
            <div className="div-5" style={{ alignSelf: 'center', width: '100%', maxWidth: '400px' }}>
                <div className="component-52-wrapper">
                    <button 
                        className="component-52-instance component-52-2" 
                        onClick={handleComplete}
                        disabled={!fileSelected} 
                        style={{ opacity: fileSelected ? 1 : 0.5 }}
                    > 
                        업로드 완료
                    </button>
                </div>
            </div>
        </div>
    );
}
