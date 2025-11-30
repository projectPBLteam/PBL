{/*.csv 파일인지 검증하는 코드 추가*/}
import { useRef, useState, useEffect } from 'react'
import { useNavigate } from "react-router-dom"
import "./DataUpload.css"

interface NotificationProps {
  type: 'success' | 'error' | null;
  message: string;
}

function CustomNotification({ type, message }: NotificationProps) {
  if (!type || !message) return null;

  const style = {
    position: 'fixed' as 'fixed',
    top: '20px',
    right: '20px',
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

export default function DataUpload() {
  const navigate = useNavigate()
  const handleBack = () => {
    navigate('/main')
  }

  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [fileName, setFileName] = useState('')
  const [fileSelected, setFileSelected] = useState(false)
  const [notification, setNotification] = useState<NotificationProps>({ type: null, message: '' });

  useEffect(() => {
    if (notification.type) {
      const timer = setTimeout(() => {
        setNotification({ type: null, message: '' });
      }, 3500); // 3.5초 후 알림 자동 닫기
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNotification({ type: null, message: '' });

    const file = e.target.files?.[0];
    if (file) {
      const name = file.name.trim().toLowerCase(); // 공백 제거 + 소문자 변환
  
      if (!name.endsWith(".csv")) {
        setNotification({ type: 'error', message: "CSV 파일 형식이 아닙니다. (.csv 파일만 지원합니다)" });
        e.target.value = "";
        setFileName("");
        setFileSelected(false);
        return;
      }
  
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
      credentials: "include",
    });

    const data = await response.json();
    console.log("백엔드 응답:", data);

    if (data.success) {
      setNotification({ type: 'success', message: "데이터가 성공적으로 업로드되었습니다!" });
      setTimeout(() => navigate('/main'), 1000);
    } else {
      setNotification({ type: 'error', message: data.message || "업로드 실패: 서버에서 알 수 없는 오류가 발생했습니다." });
    }
  };


  return (
    <div className="data-upload-screen">
      <CustomNotification type={notification.type} message={notification.message} />
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
