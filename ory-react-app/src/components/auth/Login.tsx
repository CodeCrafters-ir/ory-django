import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { kratos } from '../../services/ory';
import { LoginFlow, UiNode, UpdateLoginFlowBody } from '@ory/kratos-client';
import { useAuth } from '../../contexts/AuthContext';
import { TextField, Button, Paper, Typography, Box, Alert, Divider } from '@mui/material';
import OAuthLoginButton from './OAuthLoginButton';

const Login: React.FC = () => {
  const [flow, setFlow] = useState<LoginFlow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [credentials, setCredentials] = useState({ identifier: '', password: '' });
  const navigate = useNavigate();
  const { isAuthenticated, refreshSession } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
      return;
    }

    // Get flow from URL or initialize a new one
    const flowId = new URLSearchParams(window.location.search).get('flow');

    if (flowId) {
      // If we have a flow ID, get the flow
      kratos.getLoginFlow({ id: flowId })
          .then(({ data }) => setFlow(data))
          .catch((err: Error) => {
            setError('The login flow expired, please try again.');
            initializeFlow();
          });
    } else {
      initializeFlow();
    }
  }, [isAuthenticated, navigate]);

  const initializeFlow = () => {
    kratos.createBrowserLoginFlow()
        .then(({ data }) => setFlow(data))
        .catch((err: Error) => setError('Could not initialize login flow. Please try again.'));
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!flow) return;

    try {
      // Find the CSRF token in a type-safe way
      let csrfToken = '';
      for (const node of flow.ui.nodes) {
        if (
            node.attributes.node_type === 'input' &&
            'name' in node.attributes &&
            node.attributes.name === 'csrf_token' &&
            'value' in node.attributes
        ) {
          csrfToken = node.attributes.value as string;
          break;
        }
      }

      const submitBody: UpdateLoginFlowBody = {
        method: 'password',
        password: credentials.password,
        identifier: credentials.identifier,
        csrf_token: csrfToken,
      };

      await kratos.updateLoginFlow({
        flow: flow.id,
        updateLoginFlowBody: submitBody
      });

      await refreshSession();
      navigate('/dashboard');
    } catch (err: any) {
      if (err.response?.data?.ui) {
        // We received a new flow
        setFlow(err.response.data);
        setError('Authentication failed. Please check your credentials.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    }
  };

  if (!flow) {
    return <Typography>Loading...</Typography>;
  }

  return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Paper sx={{ p: 4, maxWidth: 400, width: '100%' }}>
          <Typography variant="h5" component="h1" gutterBottom>
            Login
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <form onSubmit={handleSubmit}>
            <TextField
                fullWidth
                margin="normal"
                label="Email or Username"
                name="identifier"
                value={credentials.identifier}
                onChange={handleInputChange}
                required
            />

            <TextField
                fullWidth
                margin="normal"
                label="Password"
                name="password"
                type="password"
                value={credentials.password}
                onChange={handleInputChange}
                required
            />

            <Button
                type="submit"
                fullWidth
                variant="contained"
                color="primary"
                sx={{ mt: 3, mb: 2 }}
            >
              Sign In
            </Button>
          </form>

          <Divider sx={{ my: 2 }}>OR</Divider>

          {/* OAuth Login Button */}
          <OAuthLoginButton fullWidth />

          <Button
              fullWidth
              variant="text"
              onClick={() => navigate('/registration')}
              sx={{ mt: 2 }}
          >
            Don't have an account? Sign Up
          </Button>
        </Paper>
      </Box>
  );
};

export default Login;