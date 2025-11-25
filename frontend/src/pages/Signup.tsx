import './Signup.css'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Signup() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [emailDuplicate, setEmailDuplicate] = useState(false)

  const handleBack = () => {
    navigate('/')
  }

  const handleSignup = async () => {
    const response = await fetch("http://localhost:8000/signup/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        email: email, 
        password: password }),
      credentials: "include",  // 세션 쿠키 포함
    })

    const data = await response.json()
    console.log("백엔드 응답:", data)

    if (data.success) {
      alert("회원가입이 완료되었습니다.")
      navigate('/main')
    } else {
      alert(data.message)
    }
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
            value={email}
            onChange={(e) => { setEmail(e.target.value); setEmailDuplicate(false); }}
          />
          {emailDuplicate && (
            <div className="signup-text-wrapper-6">* 가입된 이메일이 존재합니다</div>
          )}

          <div className="signup-text-wrapper-7">비밀번호</div>
          <input
            className="signup-input-field-instance"
            type="password"
            placeholder="비밀번호를 입력해주세요."
            value={password}
            onChange={(e) => setPassword(e.target.value)}
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
