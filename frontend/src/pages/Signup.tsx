import './Signup.css'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Signup() {
  const navigate = useNavigate()
  const [emailDuplicate, setEmailDuplicate] = useState(false)

  const handleBack = () => {
    navigate('/')
  }

  const handleSignup = () => {
    alert("회원가입이 완료되었습니다.")
    navigate('/')
  }

  return (
    <div className="signup-screen">
      <div className="signup-view-wrapper">
        <button className="back-button" onClick={handleBack}>← 뒤로가기</button>
      </div>

      <div className="signup-div-wrapper-2">
        <p className="signup-p">
          <span className="signup-span">차분 프라이버시 기반의<br /></span>
          <span className="signup-text-wrapper-2">개인정보 이노베이션 존</span>
        </p>
      </div>

      <div className="signup-div-2">
        <div className="signup-div-wrapper-3">
          <div className="signup-text-wrapper-4">회원 정보를 입력해주세요.</div>
        </div>

        <div className="signup-div-3">
          <div className="signup-text-wrapper-5">이메일</div>
          <input
            className="signup-input-field-instance"
            placeholder="이메일을 입력해주세요."
            onChange={() => setEmailDuplicate(false)}
          />
          {emailDuplicate && (
            <div className="signup-text-wrapper-6">* 가입된 이메일이 존재합니다</div>
          )}

          <div className="signup-text-wrapper-7">비밀번호</div>
          <input
            className="signup-input-field-instance"
            type="password"
            placeholder="비밀번호를 입력해주세요."
          />

          <div className="signup-frame-wrapper">
            
            <button className="signup-frame-component-58-instance" onClick={handleSignup}>
              가입하기
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
