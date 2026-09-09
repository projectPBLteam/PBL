import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup';
import Main from './pages/Main';
import DataDetail from './pages/DataDetail';
import DataUpload from './pages/DataUpload';
import DataSelect from './pages/DataSelect';
import DataAnalysis from './pages/DataAnalysis';
import Guide from './pages/Guide';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/main" element={<Main />} />
        <Route path="/data-detail/:id" element={<DataDetail />} />
        <Route path="/data-upload" element={<DataUpload />} />
        <Route path="/data-select" element={<DataSelect />} />
        <Route path="/data-analysis" element={<DataAnalysis />} />
        <Route path="/guide" element={<Guide />} />
      </Routes>
    </Router>
  )
}
