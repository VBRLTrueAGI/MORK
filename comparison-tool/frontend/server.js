const express = require('express');
const cors = require('cors');
const path = require('path');
const WebSocket = require('ws');
const http = require('http');

const app = express();
const port = process.env.PORT || 3000;
const backendUrl = process.env.BACKEND_URL || 'http://backend:8080';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Create HTTP server
const server = http.createServer(app);

// WebSocket server for real-time updates
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
    console.log('Client connected to WebSocket');
    
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            console.log('WebSocket message:', data);
            
            // Handle different message types
            if (data.type === 'subscribe_benchmark') {
                // Subscribe to benchmark updates
                ws.benchmarkId = data.benchmarkId;
            }
        } catch (error) {
            console.error('WebSocket message error:', error);
        }
    });
    
    ws.on('close', () => {
        console.log('Client disconnected from WebSocket');
    });
});

// Load axios at the top
const axios = require('axios');

// Proxy API calls to backend
app.use('/api', (req, res) => {
    
    const url = `${backendUrl}${req.originalUrl}`;
    const method = req.method.toLowerCase();
    
    const config = {
        method,
        url,
        headers: req.headers,
        data: req.body
    };
    
    axios(config)
        .then(response => {
            res.status(response.status).json(response.data);
        })
        .catch(error => {
            console.error('API proxy error:', error.message);
            res.status(error.response?.status || 500).json({
                error: error.message,
                details: error.response?.data
            });
        });
});

// Serve main application
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Start server
server.listen(port, () => {
    console.log(`Frontend server running on port ${port}`);
    console.log(`Backend URL: ${backendUrl}`);
});

// Handle graceful shutdown
process.on('SIGTERM', () => {
    console.log('Shutting down frontend server...');
    server.close(() => {
        console.log('Frontend server closed');
        process.exit(0);
    });
});