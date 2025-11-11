import './Main.css'
import { useNavigate } from 'react-router-dom'

export default function Main() {
  const navigate = useNavigate()
  const handleLogout = () => {
    navigate('/')
  }
  return (
    <div className="main-screen">
      {/* 로그아웃 버튼 */}
      <div className="component-49-wrapper">
        <div className="component-49-instance">
          <button className="logout-button" onClick={handleLogout}>로그아웃</button>
        </div>
      </div>

      {/* 중앙 타이틀 */}
      <div className="div-wrapper-2">
        <p className="p">
        <span className="span">차분 프라이버시 기반의<br /></span>
          <span className="text-wrapper-3">개인정보 이노베이션 존</span>
        </p>
      </div>

      {/* 메인 버튼 2개 */}
      <div className="div-2">
        <button
          className="component-50-instance" onClick={() => navigate('/data-upload')}>데이터 업로드</button>
        <button className="component-50-instance" onClick={() => navigate('/data-select')}>데이터 분석</button>
      </div>

      {/* 이용 안내 */}
      <div className="view-wrapper">
        <div className="component-51-instance" onClick={() => navigate('/guide')}>이용 안내</div>
      </div>
    </div>
  )
}