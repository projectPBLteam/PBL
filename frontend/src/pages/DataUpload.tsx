{/*.csv 파일인지 검증하는 코드 추가*/}
import { useRef, useState } from 'react'
import { useNavigate } from "react-router-dom"
import "./DataUpload.css"

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
  const handleComplete = async () => {
    if (!fileInputRef.current?.files?.[0]) return;

    const file = fileInputRef.current.files[0];
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://localhost:8000/fileupload/", {
      method: "POST",
      body: formData,
      credentials: "include", // 로그인 세션 포함
    });

    const data = await response.json();
    console.log("백엔드 응답:", data);

    if (data.success) {
      alert("데이터가 업로드되었습니다!");
      navigate('/main');
    } else {
      alert(data.message || "업로드 실패");
    }
  };


  return (
    <div className="data-upload-screen">
      <div className="component-51-wrapper">
        <button className="back-button" onClick={handleBack}>← 뒤로가기</button>
      </div>

      <div className="text-wrapper-2">데이터 업로드</div>

      <div className="div-2">
        <div className="div-3">
          <div className="text-wrapper-3">업로드 가능 파일 형식</div>
          <div className="frame">
            <div className="frame-2">
              <div className="text-wrapper-4">.csv 파일 형식을 지원합니다.</div>
            </div>
          </div>
        </div>

        <div className="div-4">
          <div className="text-wrapper-3">파일 업로드</div>
          <div className="frame-wrapper">
            <div className="frame-2">
              <div className="text-wrapper-4">{fileName || '파일을 업로드해주세요.'}</div>
            </div>
          </div>
        </div>
      </div>
      {/*버튼*/}
        <div className="div-5">
          <div className="component-52-wrapper">
            {/* 숨겨진 파일 입력 */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />

            {/* 업로드 버튼 */}
            <button className="component-52-instance component-52-2" onClick={handleUploadClick}> 파일 업로드 </button>

            {/* 파일이 선택된 경우에만 완료 버튼 표시 */}
            {fileSelected && (
              <button className="component-52-3" onClick={handleComplete}>완료</button>
            )}
          </div>
        </div>
    </div>
  )
}
