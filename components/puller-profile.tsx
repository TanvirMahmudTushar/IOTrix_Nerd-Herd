'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Award, TrendingUp } from 'lucide-react'

interface PullerProfile {
  puller_id: string
  name: string
  points: number
  total_rides: number
  rating: number
  status: string
}

export function PullerProfile({ pullerId }: { pullerId: string }) {
  const [profile, setProfile] = useState<PullerProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/pullers/${pullerId}/profile`
        )
        if (response.ok) {
          const data = await response.json()
          setProfile(data)
        }
      } catch (err) {
        console.error('Failed to fetch profile:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
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

  if (!profile) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="pt-6">
          <p className="text-red-400">Failed to load profile</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="w-5 h-5 text-yellow-500" />
            Points
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold text-yellow-400">{profile.points}</p>
          <p className="text-slate-400 text-sm mt-1">Total points earned</p>
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
          <p className="text-4xl font-bold text-green-400">{profile.total_rides}</p>
          <p className="text-slate-400 text-sm mt-1">Total rides completed</p>
        </CardContent>
      </Card>

      <Card className="md:col-span-2 bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle>Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm">
            <span className="text-slate-400">Current Status:</span>{' '}
            <span className="capitalize text-blue-400 font-medium">{profile.status}</span>
          </p>
          <p className="text-sm">
            <span className="text-slate-400">Rating:</span>{' '}
            <span className="text-blue-400 font-medium">{profile.rating.toFixed(1)} ⭐</span>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
