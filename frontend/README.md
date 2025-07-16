# VaPtER Frontend

React frontend for the VaPtER Vulnerability Assessment Platform.

## Features

- **Customer Management**: Create and manage customers with CRUD operations
- **Target Management**: Add and manage scan targets (IP addresses and domains)
- **Scan Management**: Start, monitor, and manage vulnerability scans
- **Real-time Updates**: Auto-refresh for running scans
- **Detailed Results**: View comprehensive scan results with port information
- **Modern UI**: Clean, responsive interface with Tailwind CSS

## Technology Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Headless UI** for components
- **React Router** for navigation
- **React Hook Form** for form management
- **Axios** for API communication
- **Heroicons** for icons

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Docker Development

The frontend is also available as a Docker container:

```bash
docker-compose up frontend
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Common/         # Common components (ErrorBoundary, ConfirmDialog)
│   ├── Layout/         # Layout components (Sidebar, Header, etc.)
│   └── Modals/         # Modal components
├── context/            # React context for state management
├── pages/              # Page components
├── services/           # API services
├── types/              # TypeScript type definitions
├── App.tsx             # Main app component
└── index.tsx           # Entry point
```

## API Integration

The frontend communicates with the VaPtER API Gateway at `http://vapter.szini.it:8080`.

Key API endpoints:
- `/api/orchestrator/customers/` - Customer management
- `/api/orchestrator/targets/` - Target management
- `/api/orchestrator/scans/` - Scan management
- `/api/orchestrator/scan-types/` - Scan type configuration

## Features

### Customer Management
- Create, edit, and delete customers
- Customer selector with persistent selection
- Customer-specific data filtering

### Target Management
- Add targets with IP addresses or domain names
- Input validation for IP/FQDN formats
- Target-specific scan history

### Scan Management
- Start scans with different scan types
- Real-time scan status monitoring
- Detailed scan results viewing
- Scan cancellation and restart functionality

### User Interface
- Modern, responsive design
- Dark/light theme support
- Modal-based forms
- Loading states and error handling
- Auto-refresh for real-time updates

## Environment Variables

- `REACT_APP_API_URL` - API Gateway URL (default: http://localhost:8080)

## Development

### Code Style
- TypeScript for type safety
- Functional components with hooks
- Consistent naming conventions
- Proper error handling

### Testing
Run tests with:
```bash
npm test
```

### Build
Create production build:
```bash
npm run build
```

## Deployment

The frontend is deployed as a Docker container alongside the backend services.

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for new features
3. Include proper error handling
4. Test thoroughly before submitting

## License

This project is part of the VaPtER Vulnerability Assessment Platform.