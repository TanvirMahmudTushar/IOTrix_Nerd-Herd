'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, MapPin, Clock, Award } from 'lucide-react'

interface RideAlert {
  ride_id: string
  pickup: string
  destination: string
  distance_to_pickup: number  // MVP: meters to pickup
  potential_points: number    // MVP: points if perfect dropoff
  expires_in: number         // MVP: seconds until timeout
  requested_at: string
  local_expires_at?: number  // Client-side: timestamp when alert expires
}

export function RideAlerts({ pullerId }: { pullerId: string }) {
  const [alerts, setAlerts] = useState<RideAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [acceptedRide, setAcceptedRide] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(Date.now())

  // Fetch alerts from backend every 5 seconds
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/pullers/${pullerId}/alerts`
        )
        if (response.ok) {
          const data = await response.json()
          // MVP: Backend returns {alerts: [...]}
          // Add local expiration timestamp for client-side countdown
          const now = Date.now()
          const alertsWithTimestamp = (data.alerts || []).map((alert: RideAlert) => ({
            ...alert,
            local_expires_at: now + (alert.expires_in * 1000)
          }))
          setAlerts(alertsWithTimestamp)
          setError(null)
        } else {
          setError('Failed to fetch alerts')
        }
      } catch (err) {
        console.error('Failed to fetch alerts:', err)
        setError('Connection error')
      } finally {
        setLoading(false)
      }
    }

    fetchAlerts()
    const interval = setInterval(fetchAlerts, 5000) // Poll every 5 seconds
    return () => clearInterval(interval)
  }, [pullerId])

  // Update countdown every second for smooth UI
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now())
      
      // Remove expired alerts
      setAlerts(prevAlerts => 
        prevAlerts.filter(alert => {
          if (!alert.local_expires_at) return true
          const remaining = Math.floor((alert.local_expires_at - Date.now()) / 1000)
          return remaining > 0
        })
      )
    }, 1000) // Update every second

    return () => clearInterval(interval)
  }, [])

  const handleAcceptRide = async (rideId: string) => {
    try {
      // MVP: Accept endpoint is in pullers router
      const response = await fetch(
        `http://localhost:8000/api/pullers/${rideId}/accept?puller_id=${pullerId}`,
        { method: 'POST' }
      )

      if (response.ok) {
        setAcceptedRide(rideId)
        setAlerts(alerts.filter(alert => alert.ride_id !== rideId))
        setError(null)
      } else {
        const data = await response.json()
        setError(data.detail || 'Failed to accept ride')
      }
    } catch (err) {
      console.error('Failed to accept ride:', err)
      setError('Connection error')
    }
  }

  const handleRejectRide = async (rideId: string) => {
    try {
      // MVP: Reject endpoint is in pullers router
      const response = await fetch(
        `http://localhost:8000/api/pullers/${rideId}/reject?puller_id=${pullerId}`,
        { method: 'POST' }
      )
      
      // Remove from list regardless of response
      setAlerts(alerts.filter(alert => alert.ride_id !== rideId))
      setError(null)
    } catch (err) {
      console.error('Failed to reject ride:', err)
      // Still remove from UI
      setAlerts(alerts.filter(alert => alert.ride_id !== rideId))
    }
  }

  if (loading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="pt-6">
          <p className="text-slate-400">Loading alerts...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {error && (
        <Card className="bg-red-900 border-red-700">
          <CardContent className="pt-6">
            <p className="text-red-300">⚠ {error}</p>
          </CardContent>
        </Card>
      )}

      {acceptedRide && (
        <Card className="bg-green-900 border-green-700">
          <CardContent className="pt-6">
            <p className="text-green-300">✓ Ride {acceptedRide} accepted! User will confirm shortly.</p>
          </CardContent>
        </Card>
      )}

      {alerts.length === 0 ? (
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="mx-auto mb-2 text-slate-500" />
            <p className="text-slate-400">No ride alerts at the moment</p>
            <p className="text-slate-500 text-sm mt-2">Alerts appear when riders request nearby rides</p>
          </CardContent>
        </Card>
      ) : (
        alerts.map(alert => {
          // Calculate remaining time from local timestamp
          const remainingSeconds = alert.local_expires_at 
            ? Math.max(0, Math.floor((alert.local_expires_at - currentTime) / 1000))
            : alert.expires_in
          
          return (
            <Card key={alert.ride_id} className="bg-slate-800 border-slate-700 hover:border-slate-600 transition-colors">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg flex items-center gap-2">
                      {alert.pickup} → {alert.destination}
                      {remainingSeconds < 15 && (
                        <Badge variant="destructive" className="text-xs animate-pulse">
                          Expiring soon!
                        </Badge>
                      )}
                    </CardTitle>
                    <div className="flex flex-col gap-1 mt-2">
                      <CardDescription className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {(alert.distance_to_pickup / 1000).toFixed(1)} km to pickup
                      </CardDescription>
                      <CardDescription className="flex items-center gap-1">
                        <Award className="w-4 h-4 text-yellow-500" />
                        Up to {alert.potential_points} points
                      </CardDescription>
                      <CardDescription className={`flex items-center gap-1 font-semibold ${
                        remainingSeconds < 15 ? 'text-red-400' : 
                        remainingSeconds < 30 ? 'text-yellow-400' : 
                        'text-blue-400'
                      }`}>
                        <Clock className="w-4 h-4" />
                        Expires in {remainingSeconds}s
                      </CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleAcceptRide(alert.ride_id)}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                    disabled={remainingSeconds === 0}
                  >
                    Accept Ride
                  </Button>
                  <Button
                    onClick={() => handleRejectRide(alert.ride_id)}
                    variant="outline"
                    className="flex-1 hover:bg-red-900/20"
                    disabled={remainingSeconds === 0}
                  >
                    Reject
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })
      )}
    </div>
  )
}
