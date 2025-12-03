#!/usr/bin/env python3
"""
OptionScope Deployment Script
Handles deployment to various platforms with monetization setup
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path

class OptionScopeDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.platforms = {
            'vercel': self.deploy_vercel,
            'heroku': self.deploy_heroku,
            'railway': self.deploy_railway,
            'render': self.deploy_render
        }
    
    def deploy_vercel(self):
        """Deploy to Vercel (Recommended for free tier)"""
        print("🚀 Deploying OptionScope to Vercel...")
        
        # Check if Vercel CLI is installed
        try:
            subprocess.run(['vercel', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Vercel CLI not found. Installing...")
            subprocess.run(['npm', 'install', '-g', 'vercel'], check=True)
        
        # Copy production requirements
        subprocess.run(['cp', 'requirements-vercel.txt', 'requirements.txt'], check=True)
        
        # Set up environment variables
        env_vars = self.get_production_env_vars()
        
        print("📝 Setting up environment variables...")
        for key, value in env_vars.items():
            if value and value != 'your-key-here':
                subprocess.run(['vercel', 'env', 'add', key], input=value.encode(), check=True)
        
        # Deploy
        print("🚀 Deploying to Vercel...")
        result = subprocess.run(['vercel', '--prod'], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Extract URL from output
            lines = result.stdout.split('\n')
            url = None
            for line in lines:
                if 'https://' in line and 'vercel.app' in line:
                    url = line.strip()
                    break
            
            print(f"✅ Deployment successful!")
            print(f"🌐 Your OptionScope is live at: {url}")
            print(f"💰 Set up Stripe webhooks at: {url}/auth/webhook/stripe")
            
            return url
        else:
            print(f"❌ Deployment failed: {result.stderr}")
            return None
    
    def deploy_heroku(self):
        """Deploy to Heroku"""
        print("🚀 Deploying OptionScope to Heroku...")
        
        # Check if Heroku CLI is installed
        try:
            subprocess.run(['heroku', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Heroku CLI not found. Please install it first.")
            return None
        
        # Create Heroku app
        app_name = input("Enter Heroku app name (or press Enter for auto-generated): ").strip()
        if app_name:
            subprocess.run(['heroku', 'create', app_name], check=True)
        else:
            subprocess.run(['heroku', 'create'], check=True)
        
        # Add PostgreSQL addon
        subprocess.run(['heroku', 'addons:create', 'heroku-postgresql:hobby-dev'], check=True)
        
        # Set environment variables
        env_vars = self.get_production_env_vars()
        for key, value in env_vars.items():
            if value and value != 'your-key-here':
                subprocess.run(['heroku', 'config:set', f'{key}={value}'], check=True)
        
        # Deploy
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Deploy OptionScope'], check=True)
        subprocess.run(['git', 'push', 'heroku', 'main'], check=True)
        
        # Get app URL
        result = subprocess.run(['heroku', 'info'], capture_output=True, text=True)
        url = None
        for line in result.stdout.split('\n'):
            if 'Web URL:' in line:
                url = line.split('Web URL:')[1].strip()
                break
        
        print(f"✅ Deployment successful!")
        print(f"🌐 Your OptionScope is live at: {url}")
        return url
    
    def deploy_railway(self):
        """Deploy to Railway"""
        print("🚀 Deploying OptionScope to Railway...")
        
        # Check if Railway CLI is installed
        try:
            subprocess.run(['railway', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Railway CLI not found. Installing...")
            subprocess.run(['npm', 'install', '-g', '@railway/cli'], check=True)
        
        # Login and create project
        subprocess.run(['railway', 'login'], check=True)
        subprocess.run(['railway', 'init'], check=True)
        
        # Set environment variables
        env_vars = self.get_production_env_vars()
        for key, value in env_vars.items():
            if value and value != 'your-key-here':
                subprocess.run(['railway', 'variables', 'set', f'{key}={value}'], check=True)
        
        # Deploy
        subprocess.run(['railway', 'up'], check=True)
        
        print("✅ Deployment successful!")
        print("🌐 Check Railway dashboard for your app URL")
        return "Check Railway dashboard"
    
    def deploy_render(self):
        """Deploy to Render"""
        print("🚀 Setting up Render deployment...")
        
        # Create render.yaml
        render_config = {
            "services": [
                {
                    "type": "web",
                    "name": "optionscope",
                    "env": "python",
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "gunicorn app:server",
                    "envVars": [
                        {"key": "FLASK_ENV", "value": "production"},
                        {"key": "SECRET_KEY", "generateValue": True},
                    ]
                }
            ]
        }
        
        with open('render.yaml', 'w') as f:
            json.dump(render_config, f, indent=2)
        
        print("✅ render.yaml created!")
        print("🌐 Connect your GitHub repo to Render dashboard to deploy")
        return "Manual setup required"
    
    def get_production_env_vars(self):
        """Get production environment variables"""
        env_vars = {}
        
        print("\n💰 Setting up monetization (Stripe)...")
        print("Get your Stripe keys from: https://dashboard.stripe.com/apikeys")
        
        stripe_publishable = input("Stripe Publishable Key (pk_live_...): ").strip()
        stripe_secret = input("Stripe Secret Key (sk_live_...): ").strip()
        stripe_webhook = input("Stripe Webhook Secret (whsec_...): ").strip()
        
        env_vars.update({
            'FLASK_ENV': 'production',
            'SECRET_KEY': self.generate_secret_key(),
            'STRIPE_PUBLISHABLE_KEY': stripe_publishable,
            'STRIPE_SECRET_KEY': stripe_secret,
            'STRIPE_WEBHOOK_SECRET': stripe_webhook,
        })
        
        # Optional API keys
        print("\n📊 Optional: Market Data API Keys (press Enter to skip)")
        alpha_vantage = input("Alpha Vantage API Key: ").strip()
        iex_key = input("IEX Cloud API Key: ").strip()
        
        if alpha_vantage:
            env_vars['ALPHA_VANTAGE_API_KEY'] = alpha_vantage
        if iex_key:
            env_vars['IEX_API_KEY'] = iex_key
        
        return env_vars
    
    def generate_secret_key(self):
        """Generate a secure secret key"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def setup_stripe_products(self):
        """Set up Stripe products and prices"""
        print("\n💳 Setting up Stripe products...")
        
        stripe_secret = input("Enter your Stripe Secret Key: ").strip()
        if not stripe_secret:
            print("⚠️  Skipping Stripe setup. You can do this later in Stripe Dashboard.")
            return
        
        import stripe
        stripe.api_key = stripe_secret
        
        try:
            # Create Pro product
            pro_product = stripe.Product.create(
                name="OptionScope Pro",
                description="Advanced options trading analytics for serious traders"
            )
            
            # Create Pro prices
            pro_monthly = stripe.Price.create(
                product=pro_product.id,
                unit_amount=2999,  # $29.99
                currency='usd',
                recurring={'interval': 'month'}
            )
            
            pro_yearly = stripe.Price.create(
                product=pro_product.id,
                unit_amount=29999,  # $299.99
                currency='usd',
                recurring={'interval': 'year'}
            )
            
            # Create Enterprise product
            enterprise_product = stripe.Product.create(
                name="OptionScope Enterprise",
                description="Full-featured solution for institutions"
            )
            
            # Create Enterprise prices
            enterprise_monthly = stripe.Price.create(
                product=enterprise_product.id,
                unit_amount=9999,  # $99.99
                currency='usd',
                recurring={'interval': 'month'}
            )
            
            enterprise_yearly = stripe.Price.create(
                product=enterprise_product.id,
                unit_amount=99999,  # $999.99
                currency='usd',
                recurring={'interval': 'year'}
            )
            
            print("✅ Stripe products created successfully!")
            print(f"📝 Add these to your environment variables:")
            print(f"STRIPE_PRO_MONTHLY={pro_monthly.id}")
            print(f"STRIPE_PRO_YEARLY={pro_yearly.id}")
            print(f"STRIPE_ENTERPRISE_MONTHLY={enterprise_monthly.id}")
            print(f"STRIPE_ENTERPRISE_YEARLY={enterprise_yearly.id}")
            
        except Exception as e:
            print(f"❌ Error setting up Stripe: {e}")
    
    def deploy(self, platform='vercel'):
        """Main deployment function"""
        print(f"🚀 OptionScope Deployment to {platform.title()}")
        print("=" * 50)
        
        if platform not in self.platforms:
            print(f"❌ Unsupported platform: {platform}")
            print(f"Supported platforms: {', '.join(self.platforms.keys())}")
            return
        
        # Setup Stripe products first
        setup_stripe = input("Set up Stripe products? (y/N): ").strip().lower()
        if setup_stripe == 'y':
            self.setup_stripe_products()
        
        # Deploy to platform
        url = self.platforms[platform]()
        
        if url:
            print("\n🎉 Deployment Complete!")
            print("=" * 50)
            print(f"🌐 Live URL: {url}")
            print(f"💰 Pricing Page: {url}/pricing")
            print(f"📊 Dashboard: {url}/dashboard")
            print(f"🔐 Admin: {url}/auth/profile")
            
            print("\n📋 Next Steps:")
            print("1. Set up your Stripe webhook endpoint")
            print("2. Configure your domain (optional)")
            print("3. Set up monitoring and analytics")
            print("4. Test the payment flow")
            print("5. Launch your marketing campaign!")
            
            print("\n💡 Monetization Tips:")
            print("• Start with freemium model to build user base")
            print("• Offer 14-day free trial for paid plans")
            print("• Add usage-based pricing for API calls")
            print("• Create enterprise features for institutions")
            print("• Consider affiliate/referral program")

def main():
    if len(sys.argv) > 1:
        platform = sys.argv[1].lower()
    else:
        print("🚀 OptionScope Deployment")
        print("Choose deployment platform:")
        print("1. Vercel (Recommended - Free tier)")
        print("2. Heroku (Full-stack)")
        print("3. Railway (Modern)")
        print("4. Render (Simple)")
        
        choice = input("Enter choice (1-4): ").strip()
        platforms = {'1': 'vercel', '2': 'heroku', '3': 'railway', '4': 'render'}
        platform = platforms.get(choice, 'vercel')
    
    deployer = OptionScopeDeployer()
    deployer.deploy(platform)

if __name__ == '__main__':
    main()
Your deployment script for OptionScope looks comprehensive and well-structured, covering multiple platforms with monetization setup via Stripe. To finish your project, consider the following steps:

1. **Test Deployment Flows:**  
   - Run deployments on each supported platform (Vercel, Heroku, Railway, Render) to verify the automation works as intended.  
   - Check environment variable setups and that the app launches correctly on each platform.

2. **Complete Stripe Integration:**  
   - Ensure the Stripe products and prices are created successfully using `setup_stripe_products()`.  
   - Verify webhook endpoints handle Stripe events properly in your app code (not shown here).  

To get started, here’s a list of what you need to do, the sites to visit, programs to download, and accounts to create:

1. Define your goal or project to determine specific needs.
2. Research relevant websites for information or services (e.g., educational resources, marketplaces, or tools).
3. Identify and download necessary programs or apps (e.g., productivity software, design tools, or communication platforms).
4. Create accounts on essential platforms (e.g., email services, social media, or project management tools).
5. Set up any required hardware or peripherals.
6. Organize your workflow with calendars, to-do lists, or collaboration tools.
7. Regularly update software and accounts for security and functionality.

If you provide more details about your specific goal, I can tailor this list further.
   - Test payment flows end-to-end, including subscriptions and webhooks.

3. **Finalize Environment Variables:**  
   - Securely store and manage all required keys and secrets, especially Stripe keys and any API keys.  
   - Avoid committing sensitive data to version control.

4. **Add Domain Configuration:**  
   - If you plan to use custom domains, prepare DNS settings and platform-specific domain linking steps.

5. **Monitoring and Analytics:**  
   - Integrate error monitoring (e.g., Sentry) and usage analytics to track app health and user behavior.

6. **Documentation and User Guides:**  
   - Write clear README and deployment instructions for users and contributors.  
   - Document monetization plans and how to manage Stripe products.

7. **Marketing and Launch:**  
   - Prepare your marketing materials and campaigns as suggested in your script's next steps.  
   - Consider onboarding flows and customer support setup.

8. **Code Review and Security Audit:**  
   - Review your codebase for security best practices, especially around secret management and API usage.  
   - Perform testing for edge cases and error handling.

By completing these steps, you will solidify your deployment and monetization pipeline and be ready to launch OptionScope successfully.

     
