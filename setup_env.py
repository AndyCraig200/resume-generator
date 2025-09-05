#!/usr/bin/env python3
"""
Setup script to help configure the .env file with your OpenAI API key.
"""

import os
from pathlib import Path


def setup_env():
    """Interactive setup for .env file."""
    env_file = Path(".env")

    print("🔧 Resume Generator Environment Setup")
    print("=" * 40)

    if env_file.exists():
        print(f"✅ Found existing .env file at: {env_file.absolute()}")

        # Check if API key is already set
        with env_file.open('r') as f:
            content = f.read()
            if 'OPENAI_API_KEY=' in content and 'your_openai_api_key_here' not in content:
                print("✅ OpenAI API key appears to be already configured!")

                # Test if we can load it
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    api_key = os.getenv('OPENAI_API_KEY')
                    if api_key and len(api_key) > 10:
                        print(
                            f"✅ API key loaded successfully (starts with: {api_key[:8]}...)")
                        return True
                except Exception as e:
                    print(f"⚠️  Error loading API key: {e}")
    else:
        print("❌ No .env file found. Creating one...")
        # Copy from example
        example_file = Path("env.example")
        if example_file.exists():
            with example_file.open('r') as f:
                content = f.read()
            with env_file.open('w') as f:
                f.write(content)
            print(f"✅ Created .env file from template")
        else:
            print("❌ No env.example file found!")
            return False

    print("\n🔑 OpenAI API Key Setup")
    print("You can get your API key from: https://platform.openai.com/api-keys")

    while True:
        api_key = input(
            "\nEnter your OpenAI API key (or 'skip' to configure manually): ").strip()

        if api_key.lower() == 'skip':
            print(f"\n📝 Please manually edit {env_file.absolute()}")
            print("Replace 'your_openai_api_key_here' with your actual API key")
            return False

        if not api_key:
            print("❌ API key cannot be empty!")
            continue

        if len(api_key) < 20:
            print("❌ API key seems too short. Please check and try again.")
            continue

        if not api_key.startswith('sk-'):
            print(
                "⚠️  OpenAI API keys typically start with 'sk-'. Are you sure this is correct? (y/n)")
            confirm = input().strip().lower()
            if confirm not in ['y', 'yes']:
                continue

        # Update the .env file
        try:
            with env_file.open('r') as f:
                content = f.read()

            # Replace the placeholder
            content = content.replace(
                'OPENAI_API_KEY=your_openai_api_key_here', f'OPENAI_API_KEY={api_key}')

            with env_file.open('w') as f:
                f.write(content)

            print(f"✅ API key saved to {env_file.absolute()}")
            print(f"✅ Key starts with: {api_key[:8]}...")
            return True

        except Exception as e:
            print(f"❌ Error saving API key: {e}")
            return False


def test_setup():
    """Test that everything is working."""
    print("\n🧪 Testing Setup")
    print("-" * 20)

    try:
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return False

        if api_key == 'your_openai_api_key_here':
            print("❌ API key is still the placeholder value")
            return False

        print(f"✅ API key loaded: {api_key[:8]}...")

        # Test OpenAI import
        try:
            import openai
            client = openai.OpenAI()
            print("✅ OpenAI client initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Error initializing OpenAI client: {e}")
            return False

    except Exception as e:
        print(f"❌ Error testing setup: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Welcome to Resume Generator Setup!\n")

    # Check if we're in the right directory
    if not Path("scripts/resume_pipeline.py").exists():
        print("❌ Please run this script from the resume-generator root directory")
        return 1

    # Setup environment
    if setup_env():
        print("\n" + "=" * 40)
        if test_setup():
            print("\n🎉 Setup completed successfully!")
            print("\nYou can now run:")
            print(
                "  python scripts/resume_pipeline.py job-applications/example_software_engineer.txt")
            return 0
        else:
            print("\n⚠️  Setup completed but testing failed. Please check your API key.")
            return 1
    else:
        print("\n⚠️  Setup incomplete. Please configure your API key manually.")
        return 1


if __name__ == "__main__":
    exit(main())
