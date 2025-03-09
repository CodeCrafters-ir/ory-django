import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { CircularProgress, Container, Typography, Alert, Paper, Box } from '@mui/material';

// Configuration constants - match these with your backend
const HYDRA_PUBLIC_URL = 'http://localhost:4444';
const REDIRECT_URI = 'http://localhost:3000/callback';
const CLIENT_ID = process.env.REACT_APP_CLIENT_ID; // Set this in your .env file

const OAuthCallback = () => {
    const [status, setStatus] = useState('processing');
    const [error, setError] = useState<string | null>(null);
    const [tokens, setTokens] = useState(null);
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const handleCallback = async () => {
            try {
                const query = new URLSearchParams(location.search);
                const code = query.get('code');
                const state = query.get('state');

                if (!code) {
                    setStatus('error');
                    setError('No authorization code received');
                    return;
                }

                // Exchange code for tokens
                const tokenData = new URLSearchParams();
                tokenData.append('grant_type', 'authorization_code');
                tokenData.append('code', code);
                tokenData.append('redirect_uri', REDIRECT_URI);
                tokenData.append('client_id', CLIENT_ID || '');

                // Note: In a production app, you'd want to exchange the code on your backend
                // to avoid exposing the client secret in the frontend
                const response = await axios.post(
                    `${HYDRA_PUBLIC_URL}/oauth2/token`,
                    tokenData,
                    {
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded'
                        }
                    }
                );

                // Store tokens securely
                const receivedTokens = response.data;

                // In a real app, you'd store these tokens securely (e.g., httpOnly cookies via your backend)
                // For this demo, we're just setting in state (NOT recommended for production)
                setTokens(receivedTokens);
                setStatus('success');

                // Store in localStorage for demo purposes (NOT secure for production)
                localStorage.setItem('access_token', receivedTokens.access_token);
                localStorage.setItem('refresh_token', receivedTokens.refresh_token);
                localStorage.setItem('id_token', receivedTokens.id_token);

                // Redirect to dashboard after short delay
                setTimeout(() => navigate('/dashboard'), 2000);
            } catch (err: any) {
                console.error('Token exchange error:', err);
                setStatus('error');
                setError(err.response?.data?.error_description || err.message || 'Failed to exchange code for tokens');
            }
        };

        handleCallback();
    }, [location, navigate]);

    return (
        <Container maxWidth="sm">
            <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Paper sx={{ p: 4, width: '100%' }}>
                    <Typography variant="h5" component="h1" gutterBottom align="center">
                        OAuth Authorization
                    </Typography>

                    {status === 'processing' && (
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 3 }}>
                            <CircularProgress sx={{ mb: 2 }} />
                            <Typography>Processing authorization...</Typography>
                        </Box>
                    )}

                    {status === 'success' && (
                        <Alert severity="success" sx={{ mt: 2 }}>
                            Authorization successful! Redirecting to dashboard...
                        </Alert>
                    )}

                    {status === 'error' && (
                        <Alert severity="error" sx={{ mt: 2 }}>
                            {error || 'An unknown error occurred during authorization'}
                        </Alert>
                    )}
                </Paper>
            </Box>
        </Container>
    );
};

export default OAuthCallback;