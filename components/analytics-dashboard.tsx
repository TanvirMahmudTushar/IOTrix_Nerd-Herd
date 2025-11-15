'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Zap, Users, TrendingUp, Activity, AlertCircle } from 'lucide-react'

interface Analytics {
  total_rides: number
  completed_rides: number
  completion_rate: number
}

interface Overview {
  active_rides: number
  online_pullers: number
  pending_reviews: number
}

export function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [overview, setOverview] = useState<Overview | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        // MVP: Fetch both analytics and overview
        const [analyticsRes, overviewRes] = await Promise.all([
          fetch('http://localhost:8000/api/admin/analytics'),
          fetch('http://localhost:8000/api/admin/overview')
        ])
        
        if (analyticsRes.ok) {
          const data = await analyticsRes.json()
          setAnalytics(data)
        }
        
        if (overviewRes.ok) {
          const data = await overviewRes.json()
          setOverview(data)
        }
      } catch (err) {
        console.error('Failed to fetch analytics:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 10000) // Update every 10 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="pt-6">
          <p className="text-slate-400">Loading analytics...</p>
        </CardContent>
      </Card>
    )
  }

  if (!analytics) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="pt-6">
          <p className="text-red-400">Failed to load analytics</p>
        </CardContent>
      </Card>
    )
  }

  const pieData = [
    { name: 'Completed', value: analytics.completed_rides },
    { name: 'Pending', value: analytics.total_rides - analytics.completed_rides },
  ]

  return (
    <div className="space-y-4">
      {/* Real-time Overview (MVP: New) */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-blue-900/20 border-blue-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Activity className="w-4 h-4 text-blue-500" />
                Active Rides
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-blue-400">{overview.active_rides}</p>
              <p className="text-xs text-slate-400 mt-1">In progress now</p>
            </CardContent>
          </Card>

          <Card className="bg-green-900/20 border-green-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Users className="w-4 h-4 text-green-500" />
                Online Pullers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-green-400">{overview.online_pullers}</p>
              <p className="text-xs text-slate-400 mt-1">Available or busy</p>
            </CardContent>
          </Card>

          <Card className="bg-orange-900/20 border-orange-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <AlertCircle className="w-4 h-4 text-orange-500" />
                Pending Reviews
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-orange-400">{overview.pending_reviews}</p>
              <p className="text-xs text-slate-400 mt-1">Need admin approval</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Historical Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-blue-500" />
              Total Rides
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-400">{analytics.total_rides}</p>
            <p className="text-xs text-slate-400 mt-1">All time</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-500" />
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-400">{analytics.completed_rides}</p>
            <p className="text-xs text-slate-400 mt-1">Successfully finished</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-500" />
              Completion Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-purple-400">{analytics.completion_rate.toFixed(1)}%</p>
            <p className="text-xs text-slate-400 mt-1">Success percentage</p>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle>Ride Status Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                <Cell fill="#10b981" />
                <Cell fill="#ef4444" />
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
