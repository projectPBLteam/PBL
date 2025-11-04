import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import Main from './pages/Main'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Guide from './pages/Guide'
import DataSelect from './pages/DataSelect'
import DataDetail from './pages/DataDetail'
import DataUpload from './pages/DataUpload'
import DataAnalysis from './pages/DataAnalysis'

const router = createBrowserRouter([
  { path: '/', element: <Login /> },
  { path: '/main', element: <Main /> },
  { path: '/signup', element: <Signup /> },
  { path: '/guide', element: <Guide /> },
  { path: '/data-select', element: <DataSelect /> },
  { path: '/data-detail', element: <DataDetail /> },
  { path: '/data-upload', element: <DataUpload /> },
  { path: '/data-analysis', element: <DataAnalysis /> },
])

createRoot(document.getElementById('root')!).render(<RouterProvider router={router} />)