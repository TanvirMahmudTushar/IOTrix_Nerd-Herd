'use client'

import { useState, useEffect } from 'react'
import { AdminNav } from '@/components/admin-nav'
import { AnalyticsDashboard } from '@/components/analytics-dashboard'
import { PendingReviews } from '@/components/pending-reviews'
import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useRouter } from 'next/navigation'

export default function AdminPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const role = localStorage.getItem('role')

    if (!token || role !== 'admin') {
      router.push('/login')
      return
    }

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
      <AdminNav />
      
      <Tabs defaultValue="analytics" className="space-y-4">
        <TabsList className="bg-slate-800 border-slate-700">
          <TabsTrigger value="analytics" className="data-[state=active]:bg-blue-600">
            Analytics
          </TabsTrigger>
          <TabsTrigger value="pending" className="data-[state=active]:bg-blue-600">
            Pending Reviews
          </TabsTrigger>
        </TabsList>

        <TabsContent value="analytics" className="space-y-4">
          <AnalyticsDashboard />
        </TabsContent>

        <TabsContent value="pending" className="space-y-4">
          <PendingReviews />
        </TabsContent>
      </Tabs>
    </div>
  )
}
