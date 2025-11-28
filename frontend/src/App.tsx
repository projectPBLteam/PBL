import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup';
import Main from './pages/Main';
import DataDetail from './pages/DataDetail';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/main" element={<Main />} />
        <Route path="/data-detail/:id" element={<DataDetail />} />
      </Routes>
    </Router>
  )
}
