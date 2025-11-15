'use client'

import { useState, useEffect } from 'react'
import { PullerNav } from '@/components/puller-nav'
import { RideAlerts } from '@/components/ride-alerts'
import { PullerProfile } from '@/components/puller-profile'
import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useRouter } from 'next/navigation'

export default function PullerPage() {
  const router = useRouter()
  const [pullerId, setPullerId] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const role = localStorage.getItem('role')

    if (!token || role !== 'puller') {
      router.push('/login')
      return
    }

    const userId = localStorage.getItem('user_id')
    setPullerId(`puller_${userId?.split('_')[1] || ''}`)
    setLoading(false)
  }, [router])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <p className="text-lg text-slate-400">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <PullerNav />
      
      <Tabs defaultValue="alerts" className="space-y-4">
        <TabsList className="bg-slate-800 border-slate-700">
          <TabsTrigger value="alerts" className="data-[state=active]:bg-blue-600">
            Ride Alerts
          </TabsTrigger>
          <TabsTrigger value="profile" className="data-[state=active]:bg-blue-600">
            Profile
          </TabsTrigger>
        </TabsList>

        <TabsContent value="alerts" className="space-y-4">
          <RideAlerts pullerId={pullerId} />
        </TabsContent>

        <TabsContent value="profile" className="space-y-4">
          <PullerProfile pullerId={pullerId} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
