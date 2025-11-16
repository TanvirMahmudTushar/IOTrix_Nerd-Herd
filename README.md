# IoTrix E-Rickshaw Tracking System

A comprehensive IoT-based E-Rickshaw tracking and management platform with real-time GPS tracking, performance analytics, and automated alerts.

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and **pnpm**
- **Python** 3.8+
- **Git**

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/TanvirMahmudTushar/IOTrix_Nerd-Herd.git
   cd IOTrix_Nerd_Herd_Updated
   ```

2. **Install Frontend Dependencies**
   ```bash
   pnpm install
   ```

3. **Install Backend Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Running the Application

#### Start Backend Server
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be running at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

#### Start Frontend Server
Open a new terminal:
```bash
pnpm dev
```

The frontend will be running at:
- **Frontend**: http://localhost:3000

## 📱 Access the Application

- **Admin Dashboard**: http://localhost:3000/admin
- **Puller Dashboard**: http://localhost:3000/puller
- **Login**: http://localhost:3000/login
- **Signup**: http://localhost:3000/signup

## 🔧 Configuration

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=sqlite:///./aeras.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📦 Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python
- **Database**: SQLAlchemy ORM
- **Authentication**: JWT + bcrypt




