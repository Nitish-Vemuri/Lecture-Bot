"""
AWS Cognito Authentication Module
Direct integration with Cognito User Pools using boto3
"""
import boto3
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any, Tuple
from botocore.exceptions import ClientError

from config import settings
from utils.logger import log


class CognitoAuth:
    """Handle AWS Cognito authentication"""
    
    def __init__(self):
        self.region = settings.aws_region
        self.user_pool_id = settings.cognito_user_pool_id
        self.client_id = settings.cognito_app_client_id
        self.client_secret = settings.cognito_app_client_secret
        
        # Initialize Cognito client
        self.client = boto3.client('cognito-idp', region_name=self.region)
    
    def _get_secret_hash(self, username: str) -> str:
        """Calculate secret hash for Cognito API calls"""
        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def sign_up(
        self, 
        username: str, 
        password: str, 
        email: str, 
        name: str
    ) -> Tuple[bool, str]:
        """Register a new user"""
        try:
            response = self.client.sign_up(
                ClientId=self.client_id,
                SecretHash=self._get_secret_hash(username),
                Username=username,
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'name', 'Value': name}
                ]
            )
            log.info(f"User registered: {username}")
            return True, "Registration successful! Please check your email for verification code."
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            log.warning(f"Sign up failed for {username}: {error_code}")
            
            if error_code == 'UsernameExistsException':
                return False, "Username already exists"
            elif error_code == 'InvalidPasswordException':
                return False, f"Invalid password: {error_msg}"
            elif error_code == 'InvalidParameterException':
                return False, f"Invalid parameter: {error_msg}"
            else:
                return False, f"Registration failed: {error_msg}"
    
    def confirm_sign_up(self, username: str, confirmation_code: str) -> Tuple[bool, str]:
        """Confirm user registration with verification code"""
        try:
            self.client.confirm_sign_up(
                ClientId=self.client_id,
                SecretHash=self._get_secret_hash(username),
                Username=username,
                ConfirmationCode=confirmation_code
            )
            log.info(f"User confirmed: {username}")
            return True, "Email verified successfully! You can now log in."
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            log.warning(f"Confirmation failed for {username}: {error_code}")
            
            if error_code == 'CodeMismatchException':
                return False, "Invalid verification code"
            elif error_code == 'ExpiredCodeException':
                return False, "Verification code expired. Please request a new one."
            else:
                return False, f"Verification failed: {error_msg}"
    
    def resend_confirmation_code(self, username: str) -> Tuple[bool, str]:
        """Resend verification code"""
        try:
            self.client.resend_confirmation_code(
                ClientId=self.client_id,
                SecretHash=self._get_secret_hash(username),
                Username=username
            )
            return True, "Verification code sent! Check your email."
        
        except ClientError as e:
            error_msg = e.response['Error']['Message']
            return False, f"Failed to resend code: {error_msg}"
    
    def sign_in(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate user and return tokens"""
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password,
                    'SECRET_HASH': self._get_secret_hash(username)
                }
            )
            
            # Get tokens
            auth_result = response.get('AuthenticationResult', {})
            
            # Get user info
            user_info = self.get_user_info(auth_result.get('AccessToken'))
            
            log.info(f"User signed in: {username}")
            return True, "Login successful!", {
                'access_token': auth_result.get('AccessToken'),
                'id_token': auth_result.get('IdToken'),
                'refresh_token': auth_result.get('RefreshToken'),
                'user_info': user_info
            }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            log.warning(f"Sign in failed for {username}: {error_code}")
            
            if error_code == 'NotAuthorizedException':
                return False, "Incorrect username or password", None
            elif error_code == 'UserNotConfirmedException':
                return False, "Please verify your email first", None
            elif error_code == 'UserNotFoundException':
                return False, "User not found", None
            else:
                return False, f"Login failed: {error_msg}", None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user attributes from access token"""
        try:
            response = self.client.get_user(AccessToken=access_token)
            
            # Parse user attributes
            user_info = {'username': response.get('Username')}
            for attr in response.get('UserAttributes', []):
                user_info[attr['Name']] = attr['Value']
            
            return user_info
        
        except ClientError as e:
            log.error(f"Failed to get user info: {e}")
            return None
    
    def refresh_tokens(self, refresh_token: str, username: str) -> Tuple[bool, Optional[Dict]]:
        """Refresh access tokens"""
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token,
                    'SECRET_HASH': self._get_secret_hash(username)
                }
            )
            
            auth_result = response.get('AuthenticationResult', {})
            return True, {
                'access_token': auth_result.get('AccessToken'),
                'id_token': auth_result.get('IdToken')
            }
        
        except ClientError as e:
            log.warning(f"Token refresh failed: {e}")
            return False, None
    
    def sign_out(self, access_token: str) -> bool:
        """Sign out user (invalidate tokens)"""
        try:
            self.client.global_sign_out(AccessToken=access_token)
            log.info("User signed out")
            return True
        except ClientError as e:
            log.warning(f"Sign out failed: {e}")
            return False
    
    def forgot_password(self, username: str) -> Tuple[bool, str]:
        """Initiate forgot password flow"""
        try:
            self.client.forgot_password(
                ClientId=self.client_id,
                SecretHash=self._get_secret_hash(username),
                Username=username
            )
            return True, "Password reset code sent to your email"
        
        except ClientError as e:
            error_msg = e.response['Error']['Message']
            return False, f"Failed: {error_msg}"
    
    def confirm_forgot_password(
        self, 
        username: str, 
        confirmation_code: str, 
        new_password: str
    ) -> Tuple[bool, str]:
        """Confirm password reset with code"""
        try:
            self.client.confirm_forgot_password(
                ClientId=self.client_id,
                SecretHash=self._get_secret_hash(username),
                Username=username,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            return True, "Password reset successful! You can now log in."
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            if error_code == 'CodeMismatchException':
                return False, "Invalid reset code"
            elif error_code == 'ExpiredCodeException':
                return False, "Reset code expired. Please request a new one."
            else:
                return False, f"Password reset failed: {error_msg}"
