# Proxy Dashboard Frontend

Internal dashboard for Proxy - Autonomous Complaint Resolution System for MCIPP (MSME Competitiveness and Industrial Productivity Program).

## Overview

This React-based dashboard provides staff at MCIPP with real-time insights into complaint handling metrics and AI-generated management reports. The main WhatsApp interface handles incoming complaints, while this dashboard supports internal monitoring and reporting.

## Features

- **Dashboard**: Real-time stats on complaints and resolutions
- **Management Report**: AI-generated analysis of complaints and actions using the backend agent
- **Data Feed**: Browse raw complaints and actions from the past month
- **Filtering**: Filter reports by complaint type and status
- **Export**: Download reports as JSON

## Setup

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Backend running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:
```
VITE_API_URL=http://localhost:8000
```

### Development Server

```bash
npm run dev
```

The app will start at `http://localhost:3000` and automatically proxy API requests to the backend.

### Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

## Authentication

The dashboard requires a valid webhook token to access. This token is configured via the `WEBHOOK_TOKEN` environment variable on the backend.

On first login, you'll be asked to enter your token. It's stored securely in browser localStorage.

## API Integration

The dashboard connects to three backend endpoints:

- `GET /api/pipeline/data` - Fetch raw data feed
- `POST /api/pipeline/report` - Generate full management report
- `POST /api/pipeline/report/filtered` - Generate filtered report

All requests require bearer token authentication.

## Pages

### Dashboard
Overview of complaint metrics:
- Total complaints
- Open/Resolved/Escalated counts
- Total actions taken
- Resolution and escalation rates

### Management Report
AI-powered analysis of complaint data:
- Filter by complaint type and status
- View AI agent analysis
- Download report as JSON

### Data Feed
Raw data browser:
- Search complaints by business name, type, or message
- View detailed complaint information
- Browse all actions taken in the period

## Technology Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js          # API configuration and methods
│   ├── components/
│   │   └── Layout.jsx          # Main layout with navigation
│   ├── pages/
│   │   ├── Login.jsx           # Authentication page
│   │   ├── Dashboard.jsx       # Overview dashboard
│   │   ├── ManagementReport.jsx # Report generation and viewing
│   │   └── DataFeed.jsx        # Raw data browser
│   ├── App.jsx                # Main app component
│   ├── main.jsx               # React entry point
│   └── index.css              # Global styles
├── index.html                 # HTML template
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # Tailwind CSS configuration
└── package.json               # Dependencies and scripts
```

## Notes

- This is an internal tool for MCIPP staff only
- The main user interface is via WhatsApp
- All data shown is from the past month
- Timestamps are in UTC

## License

Internal use only
