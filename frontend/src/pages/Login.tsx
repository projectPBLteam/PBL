import './login.css'

// Figma 자동 코드 구조를 반영한 정적 UI
export default function Login() {
  return (
    <div className="screen">

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
            <input className="input-field-instance" placeholder="이메일을 입력해주세요." />
            <div className="text-wrapper-4">비밀번호</div>
            <input className="input-field-instance" type="password" placeholder="비밀번호를 입력해주세요." />
          </div>

          <div className="component-54-wrapper">
            <button className="component-54">로그인</button>
          </div>

          <div className="component-54-instance-wrapper">
            <a href="/signup" className="component-54-instance">회원가입</a>
          </div>
        </div>
      </div>
    </div>
  )
}