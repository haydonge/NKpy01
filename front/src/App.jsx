import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css'
import './index.css';

// 导入组件
import NavBar from './components/NavBar'
import Dashboard from './pages/Dashboard'
import Reports from './pages/Reports'
import ReportDetail from './pages/ReportDetail'
import Measurements from './pages/Measurements'
import XmlImport from './pages/XmlImport'

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        <NavBar />
        <main className="flex-grow py-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/reports/:id" element={<ReportDetail />} />
            <Route path="/measurements" element={<Measurements />} />
            <Route path="/xml-import" element={<XmlImport />} />
          </Routes>
        </main>
        <footer className="bg-gray-100 py-4 border-t">
          <div className="container mx-auto px-4 text-center text-gray-600">
            <p>© {new Date().getFullYear()} 测试报告系统 | Version 1.0</p>
          </div>
        </footer>
      </div>
    </Router>
  )
}

export default App
