import axios from 'axios';

// Configuration constants
const HYDRA_PUBLIC_URL = 'http://localhost:4444';
const REDIRECT_URI = 'http://localhost:3000/callback'; // Correct redirect URI
const CLIENT_ID = process.env.REACT_APP_CLIENT_ID || 'client-id'; // Set this in your .env file
const CLIENT_SECRET = process.env.REACT_APP_CLIENT_SECRET || 'client-secret'; // Set this in your .env file

// Generate random string without crypto dependencies
const generateRandomString = (length: number): string => {
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let text = '';

    // Using Math.random() for simplicity
    for (let i = 0; i < length; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }

    return text;
};

// Start OAuth2 flow by redirecting to authorization endpoint
export const initiateOAuth2Flow = () => {
    // Generate and store state and code verifier
    const state = generateRandomString(16);
    const codeVerifier = generateRandomString(64);

    console.log("Generated state:", state);
    console.log("Generated code verifier:", codeVerifier);

    // Store in localStorage (in a real app, consider more secure storage options)
    localStorage.setItem('oauth_state', state);
    localStorage.setItem('oauth_code_verifier', codeVerifier);

    // Create authorization URL
    const authURL = new URL(`${HYDRA_PUBLIC_URL}/oauth2/auth`);
    authURL.searchParams.append('response_type', 'code');
    authURL.searchParams.append('client_id', CLIENT_ID);
    authURL.searchParams.append('redirect_uri', REDIRECT_URI);
    authURL.searchParams.append('scope', 'openid offline');
    authURL.searchParams.append('state', state);
    authURL.searchParams.append('code_challenge_method', 'plain');
    authURL.searchParams.append('code_challenge', codeVerifier);

    console.log("Redirecting to authorization URL:", authURL.toString());

    // Redirect to authorization URL
    window.location.href = authURL.toString();
};

// Exchange authorization code for tokens
export const exchangeCodeForTokens = async (code: string) => {
    try {
        const codeVerifier = localStorage.getItem('oauth_code_verifier');
        console.log("Using code verifier from localStorage:", codeVerifier);

        const tokenData = new URLSearchParams();
        tokenData.append('grant_type', 'authorization_code');
        tokenData.append('code', code);
        tokenData.append('redirect_uri', REDIRECT_URI);
        tokenData.append('client_id', CLIENT_ID);
        tokenData.append('client_secret', CLIENT_SECRET);
        tokenData.append('code_verifier', codeVerifier || '');

        console.log("Token request data:", tokenData.toString());

        const response = await axios.post(
            `${HYDRA_PUBLIC_URL}/oauth2/token`,
            tokenData,
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            }
        );

        console.log("Token response:", response.data);
        return response.data;
    } catch (error) {
        console.error('Error exchanging code for tokens:', error);
        throw error;
    }
};

// Refresh access token using refresh token
export const refreshAccessToken = async (refreshToken: string) => {
    try {
        const tokenData = new URLSearchParams();
        tokenData.append('grant_type', 'refresh_token');
        tokenData.append('refresh_token', refreshToken);
        tokenData.append('client_id', CLIENT_ID);
        tokenData.append('client_secret', CLIENT_SECRET);

        const response = await axios.post(
            `${HYDRA_PUBLIC_URL}/oauth2/token`,
            tokenData,
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            }
        );

        return response.data;
    } catch (error) {
        console.error('Error refreshing access token:', error);
        throw error;
    }
};

// Revoke token (logout)
export const revokeToken = async (token: string) => {
    try {
        const data = new URLSearchParams();
        data.append('token', token);
        data.append('client_id', CLIENT_ID);
        data.append('client_secret', CLIENT_SECRET);

        await axios.post(
            `${HYDRA_PUBLIC_URL}/oauth2/revoke`,
            data,
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            }
        );

        return true;
    } catch (error) {
        console.error('Error revoking token:', error);
        throw error;
    }
};