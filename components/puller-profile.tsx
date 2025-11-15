'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Award, TrendingUp, Clock } from 'lucide-react'

interface RecentRide {
  ride_id: string
  date: string
  pickup: string
  destination: string
  points_earned: number
  duration: number
}

interface PullerDashboard {
  name: string
  points: number
  points_expiring_soon?: number
  total_rides: number
  status: string
  recent_rides: RecentRide[]
}

export function PullerProfile({ pullerId }: { pullerId: string }) {
  const [dashboard, setDashboard] = useState<PullerDashboard | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        // MVP: Use dashboard endpoint
        const response = await fetch(
          `http://localhost:8000/api/pullers/${pullerId}/dashboard`
        )
        if (response.ok) {
          const data = await response.json()
          setDashboard(data)
        }
      } catch (err) {
        console.error('Failed to fetch dashboard:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboard, 30000)
    return () => clearInterval(interval)
  }, [pullerId])

  if (loading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="pt-6">
          <p className="text-slate-400">Loading profile...</p>
        </CardContent>
      </Card>
    )
  }

  if (!dashboard) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="pt-6">
          <p className="text-red-400">Failed to load dashboard</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="w-5 h-5 text-yellow-500" />
              Points
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-yellow-400">{dashboard.points}</p>
            <p className="text-slate-400 text-sm mt-1">Total points earned</p>
            {dashboard.points_expiring_soon && dashboard.points_expiring_soon > 0 && (
              <p className="text-orange-400 text-xs mt-2">
                ⚠ {dashboard.points_expiring_soon} points expiring soon
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-500" />
              Rides
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-green-400">{dashboard.total_rides}</p>
            <p className="text-slate-400 text-sm mt-1">Total rides completed</p>
          </CardContent>
        </Card>
      </div>

      {/* Status Card */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm">
            <span className="text-slate-400">Name:</span>{' '}
            <span className="text-blue-400 font-medium">{dashboard.name}</span>
          </p>
          <p className="text-sm">
            <span className="text-slate-400">Current Status:</span>{' '}
            <span className="capitalize text-blue-400 font-medium">{dashboard.status}</span>
          </p>
        </CardContent>
      </Card>

      {/* Recent Rides */}
      {dashboard.recent_rides && dashboard.recent_rides.length > 0 && (
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle>Recent Rides</CardTitle>
            <CardDescription>Last {Math.min(dashboard.recent_rides.length, 10)} completed rides</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboard.recent_rides.slice(0, 10).map((ride) => (
                <div key={ride.ride_id} className="flex justify-between items-center p-3 bg-slate-700 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium">{ride.pickup} → {ride.destination}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <p className="text-xs text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {ride.duration ? `${Math.floor(ride.duration / 60)}min` : 'N/A'}
                      </p>
                      <p className="text-xs text-slate-400">{new Date(ride.date).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-yellow-400">+{ride.points_earned}</p>
                    <p className="text-xs text-slate-400">points</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
