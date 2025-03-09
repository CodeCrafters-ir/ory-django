import { Configuration, FrontendApi } from '@ory/kratos-client';
import axios from 'axios';

// Configure the Kratos client
const kratosPublicUrl = process.env.REACT_APP_KRATOS_PUBLIC_URL || 'http://localhost:4433';

export const kratos = new FrontendApi(
    new Configuration({
      basePath: kratosPublicUrl,
      baseOptions: {
        withCredentials: true,
      }
    })
);

// Helper functions for common Kratos operations
export const getSession = async () => {
  try {
    const { data } = await kratos.toSession();
    return data;
  } catch (error) {
    console.error('Session error:', error);
    return null;
  }
};

export const logout = async () => {
  try {
    const { data } = await kratos.createBrowserLogoutFlow();
    const logoutUrl = data.logout_url;

    // Execute the logout
    await axios.get(logoutUrl, { withCredentials: true });

    // Redirect to home after logout
    window.location.href = '/';
  } catch (error) {
    console.error('Logout error:', error);
  }
};