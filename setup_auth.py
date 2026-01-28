"""
Authentication Setup Script
Run this once to create initial user credentials
"""
import yaml
import bcrypt
from pathlib import Path


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def setup_demo_user():
    """Setup the demo user with a proper hashed password"""
    config_path = Path(__file__).parent / "auth_config.yaml"
    
    # Load existing config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Hash the demo password
    demo_password = "demo123"  # Default demo password
    hashed = hash_password(demo_password)
    
    # Update the config
    config['credentials']['usernames']['demo']['password'] = hashed
    
    # Save back
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("✅ Demo user configured!")
    print(f"   Username: demo")
    print(f"   Password: {demo_password}")
    print("\n⚠️  Change the password after first login!")


def add_user(username: str, name: str, email: str, password: str):
    """Add a new user to the auth config"""
    config_path = Path(__file__).parent / "auth_config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    hashed = hash_password(password)
    
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': hashed
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ User '{username}' added successfully!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # Just setup demo user
        setup_demo_user()
    elif len(sys.argv) == 5:
        # Add new user: python setup_auth.py username name email password
        add_user(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Usage:")
        print("  python setup_auth.py                           # Setup demo user")
        print("  python setup_auth.py username name email pass  # Add new user")
