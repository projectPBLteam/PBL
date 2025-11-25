import './login.css'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

// CSRF 토큰 가져오는 함수
function getCookie(name: string) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(';').shift()
  return null
}

// Figma 자동 코드 구조를 반영한 정적 UI
export default function Login() {
  const navigate = useNavigate()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const handleLogin = async () => {
    const csrfToken = getCookie('csrftoken') // CSRF 토큰 가져오기

    const response = await fetch("http://localhost:8000/login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken || "", // 토큰 추가
      },
      body: JSON.stringify({ email, password }),
      credentials: "include", // 쿠키 같이 보내기
    })

    if (!response.ok) {
      alert("로그인 요청 실패!")
      return
    }

    const data = await response.json()
    console.log("백엔드 응답:", data)

    if (data.success) {
      navigate('/main')
    } else {
      alert("입력한 정보를 다시 확인해주세요.")
    }
  }

  return (
    <div className="login-screen">
      <div className="div-wrapper-2">
        <p className="p">
          <span className="span">차분 프라이버시 기반의<br /></span>
          <span className="text-wrapper-2">개인정보 이노베이션 존</span>
        </p>
      </div>

      <div className="div-wrapper-3">
        <div className="div-2">
          <div className="div-3">
            <div className="text-wrapper-3">이메일</div>
            <input
              className="input-field-instance"
              placeholder="이메일을 입력해주세요."
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <div className="text-wrapper-4">비밀번호</div>
            <input
              className="input-field-instance"
              type="password"
              placeholder="비밀번호를 입력해주세요."
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="component-54-wrapper">
            <button className="component-54" onClick={handleLogin}>
              로그인
            </button>
          </div>

          <div className="component-54-instance-wrapper">
            <a href="/signup" className="component-54-instance">회원가입</a>
          </div>
        </div>
      </div>
    </div>
  )
}
