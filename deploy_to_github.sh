#!/usr/bin/env bash
# 🚀 One-Click GitHub Deployment Helper
set -e

echo "======================================================="
echo "  🚀 Facebook Reels Auto Uploader -> GitHub Setup"
echo "======================================================="

# Check if origin already exists
if git remote | grep -q "origin"; then
    echo "Current remote origin:"
    git remote -v
else
    echo "👉 कृपया आफ्नो GitHub Repository को URL हाल्नुहोस्:"
    echo "   (उदाहरण: https://github.com/your-username/facebook-reels-uploader.git)"
    read -r REPO_URL
    if [ -n "$REPO_URL" ]; then
        git remote add origin "$REPO_URL"
        echo "✅ Remote origin थपियो!"
    fi
fi

echo ""
echo "📤 GitHub मा कोड पुश गर्दैछ..."
git push -u origin main || echo "⚠️ Push failed. Please verify repository URL and permissions."

echo ""
echo "======================================================="
echo "📋 GitHub Secrets मा राख्नुपर्ने डेटा (FB_STORAGE_STATE):"
echo "======================================================="
cat facebook_session.json
echo ""
echo "======================================================="
echo "🎉 माथिको सम्पूर्ण JSON टेक्स्टलाई GitHub Repository को:"
echo "   Settings -> Secrets and variables -> Actions -> 'New repository secret'"
echo "   - Name: FB_STORAGE_STATE"
echo "   - Value: (माथिको JSON पेस्ट गर्नुहोस्)"
echo "======================================================="
