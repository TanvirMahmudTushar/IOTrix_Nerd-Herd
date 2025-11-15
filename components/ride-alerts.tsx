'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertCircle, MapPin } from 'lucide-react'

interface RideAlert {
  ride_id: string
  user_id: string
  pickup: string
  destination: string
  distance_meters: number
}

export function RideAlerts({ pullerId }: { pullerId: string }) {
  const [alerts, setAlerts] = useState<RideAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [acceptedRide, setAcceptedRide] = useState<string | null>(null)

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/pullers/${pullerId}/alerts`
        )
        if (response.ok) {
          const data = await response.json()
          setAlerts(data)
        }
      } catch (err) {
        console.error('Failed to fetch alerts:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchAlerts()
    const interval = setInterval(fetchAlerts, 5000)
    return () => clearInterval(interval)
  }, [pullerId])

  const handleAcceptRide = async (rideId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/pullers/${rideId}/accept?puller_id=${pullerId}`,
        { method: 'POST' }
      )

      if (response.ok) {
        setAcceptedRide(rideId)
        setAlerts(alerts.filter(alert => alert.ride_id !== rideId))
      }
    } catch (err) {
      console.error('Failed to accept ride:', err)
    }
  }

  const handleRejectRide = async (rideId: string) => {
    setAlerts(alerts.filter(alert => alert.ride_id !== rideId))
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
      {acceptedRide && (
        <Card className="bg-green-900 border-green-700">
          <CardContent className="pt-6">
            <p className="text-green-300">✓ Ride {acceptedRide} accepted!</p>
          </CardContent>
        </Card>
      )}

      {alerts.length === 0 ? (
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="mx-auto mb-2 text-slate-500" />
            <p className="text-slate-400">No ride alerts at the moment</p>
          </CardContent>
        </Card>
      ) : (
        alerts.map(alert => (
          <Card key={alert.ride_id} className="bg-slate-800 border-slate-700">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{alert.pickup} → {alert.destination}</CardTitle>
                  <CardDescription className="flex items-center gap-1 mt-1">
                    <MapPin className="w-4 h-4" />
                    {(alert.distance_meters / 1000).toFixed(1)} km away
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button
                  onClick={() => handleAcceptRide(alert.ride_id)}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  Accept
                </Button>
                <Button
                  onClick={() => handleRejectRide(alert.ride_id)}
                  variant="outline"
                  className="flex-1"
                >
                  Reject
                </Button>
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  )
}
