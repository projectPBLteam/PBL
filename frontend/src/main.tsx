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
import React, { useState, useEffect } from 'react';

const checkAuthStatus = async () => {
    try {
        const response = await fetch("http://localhost:8000/api/data-list/", {
            method: 'GET',
            credentials: 'include',
        });
        if (response.status === 200) {
            const data = await response.json();
            return data.success === true;
        }
        return false;

    } catch (e) {
        console.error("인증 상태 확인 중 오류 발생:", e);
        return false;
    }
};

const ProtectedRoute = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAuthStatus().then(status => {
            setIsAuthenticated(status);
            setLoading(false);
        });
    }, []);

    if (loading) {
        return <div>로딩 중...</div>;
    }
    
    if (!isAuthenticated) {
        window.location.replace('/');
        return null;
    }

    return children;
};

const router = createBrowserRouter([
  { path: '/', element: <Login /> },
  { path: '/main', element: <ProtectedRoute><Main /></ProtectedRoute> },
  { path: '/signup', element: <Signup /> },
  { path: '/guide', element: <Guide /> },
  { path: '/data-select', element: <ProtectedRoute><DataSelect /></ProtectedRoute> },
  { path: '/data-detail/:id', element: <ProtectedRoute><DataDetail /></ProtectedRoute> },
  { path: '/data-upload', element: <ProtectedRoute><DataUpload /></ProtectedRoute> },
  { path: '/data-analysis', element: <ProtectedRoute><DataAnalysis /></ProtectedRoute> },
])

createRoot(document.getElementById('root')!).render(<RouterProvider router={router} />)