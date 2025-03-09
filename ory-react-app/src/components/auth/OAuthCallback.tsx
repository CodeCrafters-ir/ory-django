import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { CircularProgress, Container, Typography, Alert, Paper, Box } from '@mui/material';
import { exchangeCodeForTokens } from '../../services/oauth';

const OAuthCallback: React.FC = () => {
    const [status, setStatus] = useState('processing');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();
    const location = useLocation();

    console.log('OAuthCallback component rendered');
    console.log('Current location:', location);
    console.log('Query params:', new URLSearchParams(location.search).toString());

    useEffect(() => {
        console.log('OAuthCallback useEffect triggered');

        const handleCallback = async () => {
            try {
                console.log('Starting callback handler...');
                const query = new URLSearchParams(location.search);
                const code = query.get('code');
                const state = query.get('state');
                const storedState = localStorage.getItem('oauth_state');

                console.log('Code from URL:', code);
                console.log('State from URL:', state);
                console.log('State from localStorage:', storedState);

                if (!code) {
                    console.error('No authorization code received in the URL');
                    setStatus('error');
                    setError('No authorization code received');
                    return;
                }

                if (state !== storedState) {
                    console.error('State mismatch. Possible CSRF attack');
                    setStatus('error');
                    setError('Security validation failed');
                    return;
                }

                console.log('Exchanging code for tokens...');

                try {
                    const tokens = await exchangeCodeForTokens(code);

                    console.log('Tokens received successfully:', tokens);

                    // Store in localStorage for demo purposes (NOT secure for production)
                    localStorage.setItem('access_token', tokens.access_token);
                    localStorage.setItem('refresh_token', tokens.refresh_token);
                    if (tokens.id_token) {
                        localStorage.setItem('id_token', tokens.id_token);
                    }

                    setStatus('success');

                    console.log('Tokens stored, redirecting to dashboard in 2 seconds');
                    // Redirect to dashboard after short delay
                    setTimeout(() => navigate('/dashboard'), 2000);
                } catch (error: any) {
                    console.error('Error during token exchange API call:', error);
                    console.error('Error response:', error.response?.data);
                    throw error;
                }
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

                    <Typography variant="body1" paragraph>
                        Current status: {status}
                    </Typography>

                    <Typography variant="body2" paragraph>
                        URL: {window.location.href}
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