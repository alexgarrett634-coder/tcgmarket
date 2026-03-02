import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />
      <main className="flex-1 ml-56 p-6 overflow-y-auto page-enter">
        <Outlet />
      </main>
    </div>
  )
}
