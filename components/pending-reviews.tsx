'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { AlertCircle, CheckCircle, MapPin } from 'lucide-react'

interface PendingRide {
  ride_id: string
  puller_name: string
  destination: string
  distance_error: number  // MVP: meters from destination
  calculated_points: number
}

export function PendingReviews() {
  const [rides, setRides] = useState<PendingRide[]>([])
  const [loading, setLoading] = useState(true)
  const [adjustPoints, setAdjustPoints] = useState<{[key: string]: number}>({})

  useEffect(() => {
    const fetchPendingRides = async () => {
      try {
        // MVP: New endpoint
        const response = await fetch('http://localhost:8000/api/admin/reviews/pending')
        if (response.ok) {
          const data = await response.json()
          // MVP: Backend returns {rides: [...]}
          setRides(data.rides || [])
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
      // MVP: New resolve endpoint with action: "approve"
      const response = await fetch(
        `http://localhost:8000/api/admin/reviews/${rideId}/resolve`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'approve' })
        }
      )

      if (response.ok) {
        setRides(rides.filter(ride => ride.ride_id !== rideId))
      }
    } catch (err) {
      console.error('Failed to approve ride:', err)
    }
  }

  const handleAdjust = async (rideId: string) => {
    try {
      const points = adjustPoints[rideId]
      if (points === undefined || points < 0) {
        alert('Please enter valid points')
        return
      }

      // MVP: Adjust action with custom points
      const response = await fetch(
        `http://localhost:8000/api/admin/reviews/${rideId}/resolve`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            action: 'adjust',
            points_override: points
          })
        }
      )

      if (response.ok) {
        setRides(rides.filter(ride => ride.ride_id !== rideId))
        // Clear adjustment input
        const newAdjust = {...adjustPoints}
        delete newAdjust[rideId]
        setAdjustPoints(newAdjust)
      }
    } catch (err) {
      console.error('Failed to adjust ride:', err)
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
              <div className="flex-1">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <AlertCircle className="w-5 h-5 text-yellow-500" />
                  Destination: {ride.destination}
                </CardTitle>
                <CardDescription className="mt-2 space-y-1">
                  <p>Ride ID: {ride.ride_id}</p>
                  <p>Puller: {ride.puller_name}</p>
                  <p className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    Dropoff accuracy: {(ride.distance_error || 0).toFixed(1)}m from destination
                  </p>
                  {ride.distance_error > 100 && (
                    <p className="text-orange-400 font-medium">
                      ⚠ Distance exceeds 100m threshold
                    </p>
                  )}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Approve with 0 points */}
            <div className="flex gap-2">
              <Button
                onClick={() => handleApprove(ride.ride_id)}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                Approve (0 points)
              </Button>
            </div>
            
            {/* Adjust points */}
            <div className="space-y-2">
              <p className="text-sm text-slate-400">Or adjust points manually:</p>
              <div className="flex gap-2">
                <Input
                  type="number"
                  min="0"
                  max="10"
                  placeholder="Points (0-10)"
                  value={adjustPoints[ride.ride_id] || ''}
                  onChange={(e) => setAdjustPoints({
                    ...adjustPoints,
                    [ride.ride_id]: parseInt(e.target.value) || 0
                  })}
                  className="flex-1 bg-slate-700 border-slate-600"
                />
                <Button
                  onClick={() => handleAdjust(ride.ride_id)}
                  variant="outline"
                  className="bg-blue-600/20 hover:bg-blue-600/40"
                  disabled={!adjustPoints[ride.ride_id] && adjustPoints[ride.ride_id] !== 0}
                >
                  Adjust & Approve
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
