import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Container, Typography, Button, Box, Grid, Paper } from '@mui/material';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Welcome to Our Secure Application
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Built with React and Ory Kratos for secure identity management
        </Typography>
        
        {isLoading ? (
          <Typography>Loading...</Typography>
        ) : isAuthenticated ? (
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={() => navigate('/dashboard')}
            sx={{ mt: 2 }}
          >
            Go to Dashboard
          </Button>
        ) : (
          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              color="primary"
              size="large"
              onClick={() => navigate('/login')}
              sx={{ mr: 2 }}
            >
              Sign In
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/registration')}
            >
              Sign Up
            </Button>
          </Box>
        )}
      </Box>
      
      <Grid container spacing={4} sx={{ mt: 4 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h5" component="h2" gutterBottom>
              Secure Authentication
            </Typography>
            <Typography>
              Our application uses Ory Kratos to provide secure, modern authentication flows with support for password policies, MFA, and more.
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h5" component="h2" gutterBottom>
              Identity Management
            </Typography>
            <Typography>
              Manage your profile, security settings, and preferences all in one place with our easy-to-use interface.
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h5" component="h2" gutterBottom>
              Data Privacy
            </Typography>
            <Typography>
              Your data remains yours. We follow best practices for data security and comply with privacy regulations.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Home;
