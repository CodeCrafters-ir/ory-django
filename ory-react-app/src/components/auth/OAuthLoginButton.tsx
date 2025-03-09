import React from 'react';
import { Button } from '@mui/material';
import { initiateOAuth2Flow } from '../../services/oauth';

interface OAuthButtonProps {
    variant?: 'text' | 'outlined' | 'contained';
    color?: 'inherit' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
    fullWidth?: boolean;
    className?: string;
}

const OAuthLoginButton: React.FC<OAuthButtonProps> = ({
                                                          variant = 'contained',
                                                          color = 'primary',
                                                          fullWidth = false,
                                                          className,
                                                      }) => {
    const handleOAuthLogin = () => {
        alert("OAuth login button clicked!");
        console.log("Initiating OAuth flow...");
        initiateOAuth2Flow();
    };

    return (
        <Button
            variant={variant}
            color={color}
            fullWidth={fullWidth}
            className={className}
            onClick={handleOAuthLogin}
            sx={{ mt: 1, mb: 1 }}
        >
            Sign in with OAuth
        </Button>
    );
};

export default OAuthLoginButton;