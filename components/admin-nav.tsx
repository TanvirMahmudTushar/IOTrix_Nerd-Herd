'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export function AdminNav() {
  const router = useRouter()

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('user_id')
    router.push('/login')
  }

  return (
    <Card className="bg-slate-800 border-slate-700 p-4 mb-6 flex justify-between items-center">
      <div>
        <h1 className="text-2xl font-bold">AERAS Admin</h1>
        <p className="text-sm text-slate-400">Dashboard & Management</p>
      </div>
      <Button
        onClick={handleLogout}
        variant="destructive"
      >
        Logout
      </Button>
    </Card>
  )
}
