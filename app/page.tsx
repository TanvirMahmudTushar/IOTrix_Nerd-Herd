'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function Home() {
  const router = useRouter()
  
  useEffect(() => {
    const token = localStorage.getItem('token')
    const role = localStorage.getItem('role')
    
    if (token) {
      if (role === 'admin') {
        router.push('/admin')
      } else {
        router.push('/puller')
      }
    } else {
      router.push('/login')
    }
  }, [router])
  
  return null
}
