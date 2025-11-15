'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertCircle, CheckCircle } from 'lucide-react'

interface PendingRide {
  ride_id: string
  user_id: string
  pickup: string
  destination: string
  status: string
}

export function PendingReviews() {
  const [rides, setRides] = useState<PendingRide[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPendingRides = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/admin/rides/pending-review')
        if (response.ok) {
          const data = await response.json()
          setRides(data)
        }
      } catch (err) {
        console.error('Failed to fetch pending rides:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchPendingRides()
    const interval = setInterval(fetchPendingRides, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleApprove = async (rideId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/admin/rides/${rideId}/approve`,
        { method: 'POST' }
      )

      if (response.ok) {
        setRides(rides.filter(ride => ride.ride_id !== rideId))
      }
    } catch (err) {
      console.error('Failed to approve ride:', err)
    }
  }

  if (loading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="pt-6">
          <p className="text-slate-400">Loading pending reviews...</p>
        </CardContent>
      </Card>
    )
  }

  if (rides.length === 0) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="pt-6 text-center">
          <CheckCircle className="mx-auto mb-2 text-green-500" />
          <p className="text-slate-400">No pending reviews</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {rides.map(ride => (
        <Card key={ride.ride_id} className="bg-slate-800 border-slate-700">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <AlertCircle className="w-5 h-5 text-yellow-500" />
                  {ride.pickup} → {ride.destination}
                </CardTitle>
                <CardDescription className="mt-1">
                  Ride ID: {ride.ride_id}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Button
                onClick={() => handleApprove(ride.ride_id)}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                Approve
              </Button>
              <Button
                variant="outline"
                className="flex-1"
              >
                Reject
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
