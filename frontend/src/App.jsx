import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'

import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import ForgotPassword from './pages/ForgotPassword.jsx'
import Dashboard from './pages/Dashboard.jsx'
import ComplaintList from './pages/ComplaintList.jsx'
import ComplaintNew from './pages/ComplaintNew.jsx'
import ComplaintDetail from './pages/ComplaintDetail.jsx'
import AgentQueue from './pages/AgentQueue.jsx'
import Escalations from './pages/Escalations.jsx'
import Reports from './pages/Reports.jsx'
import Users from './pages/Users.jsx'
import Categories from './pages/Categories.jsx'
import Notifications from './pages/Notifications.jsx'

const withLayout = (el) => (
  <ProtectedRoute>
    <Layout>{el}</Layout>
  </ProtectedRoute>
)

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      <Route path="/dashboard" element={withLayout(<Dashboard />)} />
      <Route path="/complaints" element={withLayout(<ComplaintList />)} />
      <Route path="/complaints/new" element={withLayout(<ComplaintNew />)} />
      <Route path="/complaints/:id" element={withLayout(<ComplaintDetail />)} />
      <Route path="/my-queue" element={withLayout(<AgentQueue />)} />
      <Route path="/escalations" element={withLayout(<Escalations />)} />
      <Route path="/notifications" element={withLayout(<Notifications />)} />

      <Route path="/reports" element={
        <ProtectedRoute roles={['Admin', 'Supervisor']}>
          <Layout><Reports /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/users" element={
        <ProtectedRoute roles={['Admin']}>
          <Layout><Users /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/categories" element={
        <ProtectedRoute roles={['Admin']}>
          <Layout><Categories /></Layout>
        </ProtectedRoute>
      } />

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
