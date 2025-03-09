import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { logout } from '../services/ory';
import { Container, Typography, Button, Box, Paper, Grid } from '@mui/material';

const Dashboard: React.FC = () => {
  const { session } = useAuth();

  const handleLogout = () => {
    logout();
  };

  if (!session) {
    return (
        <Container maxWidth="sm">
          <Typography variant="h5" component="h1" align="center" gutterBottom>
            Loading user data...
          </Typography>
        </Container>
    );
  }

  const identity = session.identity;

  if (!identity) {
    return (
        <Container maxWidth="sm">
          <Typography variant="h5" component="h1" align="center" gutterBottom>
            Error: Identity information not available
          </Typography>
          <Button variant="contained" color="primary" onClick={handleLogout}>
            Logout
          </Button>
        </Container>
    );
  }

  return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
            <Typography variant="h4" component="h1">
              Welcome, {identity.traits?.name?.first || 'User'}!
            </Typography>
            <Button variant="contained" color="primary" onClick={handleLogout}>
              Logout
            </Button>
          </Box>

          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>User Information</Typography>
                <Typography><strong>ID:</strong> {identity.id}</Typography>
                <Typography><strong>Email:</strong> {identity.traits?.email || 'N/A'}</Typography>
                <Typography>
                  <strong>Name:</strong> {identity.traits?.name?.first || 'N/A'} {identity.traits?.name?.last || ''}
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>Session Details</Typography>
                <Typography>
                  <strong>Authentication Method:</strong> {session.authentication_methods?.[0]?.method || 'Unknown'}
                </Typography>
                <Typography>
                  <strong>Authenticated At:</strong> {new Date(session.authenticated_at || '').toLocaleString()}
                </Typography>
                <Typography>
                  <strong>Expires At:</strong> {new Date(session.expires_at || '').toLocaleString()}
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>Account Management</Typography>
                <Button
                    variant="outlined"
                    color="primary"
                    fullWidth
                    sx={{ mb: 2 }}
                    onClick={() => window.location.href = '/settings'}
                >
                  Account Settings
                </Button>
                <Button
                    variant="outlined"
                    color="secondary"
                    fullWidth
                    onClick={() => window.location.href = '/security'}
                >
                  Security Settings
                </Button>
              </Paper>
            </Grid>
          </Grid>
        </Paper>
      </Container>
  );
};

export default Dashboard;