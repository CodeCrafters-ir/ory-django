import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { kratos } from '../../services/ory';
import { RegistrationFlow, UiNode, UpdateRegistrationFlowBody } from '@ory/kratos-client';
import { useAuth } from '../../contexts/AuthContext';
import { TextField, Button, Paper, Typography, Box, Alert } from '@mui/material';

const Registration: React.FC = () => {
  const [flow, setFlow] = useState<RegistrationFlow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    'traits.name.first': '',
    'traits.name.last': '',
  });

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
      kratos.getRegistrationFlow({ id: flowId })
          .then(({ data }) => setFlow(data))
          .catch((err: Error) => {
            setError('The registration flow expired, please try again.');
            initializeFlow();
          });
    } else {
      initializeFlow();
    }
  }, [isAuthenticated, navigate]);

  const initializeFlow = () => {
    kratos.createBrowserRegistrationFlow()
        .then(({ data }) => setFlow(data))
        .catch((err: Error) => setError('Could not initialize registration flow. Please try again.'));
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
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

      const submitBody: UpdateRegistrationFlowBody = {
        method: 'password',
        password: formData.password,
        traits: {
          email: formData.email,
          name: {
            first: formData['traits.name.first'],
            last: formData['traits.name.last'],
          },
        },
        csrf_token: csrfToken,
      };

      await kratos.updateRegistrationFlow({
        flow: flow.id,
        updateRegistrationFlowBody: submitBody
      });

      await refreshSession();
      navigate('/dashboard');
    } catch (err: any) {
      if (err.response?.data?.ui) {
        // We received a new flow
        setFlow(err.response.data);
        setError('Registration failed. Please check your information.');
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
            Sign Up
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <form onSubmit={handleSubmit}>
            <TextField
                fullWidth
                margin="normal"
                label="Email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
                required
            />

            <TextField
                fullWidth
                margin="normal"
                label="First Name"
                name="traits.name.first"
                value={formData['traits.name.first']}
                onChange={handleInputChange}
                required
            />

            <TextField
                fullWidth
                margin="normal"
                label="Last Name"
                name="traits.name.last"
                value={formData['traits.name.last']}
                onChange={handleInputChange}
                required
            />

            <TextField
                fullWidth
                margin="normal"
                label="Password"
                name="password"
                type="password"
                value={formData.password}
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
              Sign Up
            </Button>

            <Button
                fullWidth
                variant="text"
                onClick={() => navigate('/login')}
            >
              Already have an account? Sign In
            </Button>
          </form>
        </Paper>
      </Box>
  );
};

export default Registration;