# 🦊 GitLab Sharing Guide - Power System Visualization App

## 🎯 **Step-by-Step GitLab Setup**

### **Step 1: Create GitLab Account (if needed)**
1. Go to [https://gitlab.com](https://gitlab.com)
2. Click **"Sign up"** or **"Register"**
3. Fill in your details:
   - Username (e.g., `your-username`)
   - Email address
   - Password
4. Verify your email address
5. Complete any additional setup steps

---

### **Step 2: Create New GitLab Repository**
1. **Log in to GitLab**
2. Click the **"+"** button (top-right) → **"New project/repository"**
3. Choose **"Create blank project"**
4. **Fill in project details:**
   ```
   Project name: power-system-visualization
   Project URL: https://gitlab.com/your-username/power-system-visualization
   Project slug: power-system-visualization
   Visibility Level: Public (or Private if you want restricted access)
   Description: Interactive Power System Visualization with AI Assistant and SLR vs DLR Analysis
   ```
5. **Uncheck "Initialize repository with a README"** (we'll add our own)
6. Click **"Create project"**

---

### **Step 3: Prepare Your Local Repository**

#### **3.1: Open Terminal/Command Prompt**
```bash
# Navigate to your project directory
cd c:\Projects\dlr-database-project
```

#### **3.2: Initialize Git Repository**
```bash
# Initialize git repository
git init

# Check current status
git status
```

#### **3.3: Configure Git (First Time Only)**
```bash
# Set your name and email (replace with your info)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --global --list
```

---

### **Step 4: Prepare Files for GitLab**

#### **4.1: Create .gitignore File**
```bash
# Create .gitignore to exclude unnecessary files
echo "# Python" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "*.pyo" >> .gitignore
echo "*.pyd" >> .gitignore
echo ".Python" >> .gitignore
echo "build/" >> .gitignore
echo "develop-eggs/" >> .gitignore
echo "dist/" >> .gitignore
echo "downloads/" >> .gitignore
echo "eggs/" >> .gitignore
echo ".eggs/" >> .gitignore
echo "lib/" >> .gitignore
echo "lib64/" >> .gitignore
echo "parts/" >> .gitignore
echo "sdist/" >> .gitignore
echo "var/" >> .gitignore
echo "wheels/" >> .gitignore
echo "*.egg-info/" >> .gitignore
echo ".installed.cfg" >> .gitignore
echo "*.egg" >> .gitignore
echo "" >> .gitignore
echo "# Environment" >> .gitignore
echo ".env" >> .gitignore
echo ".venv/" >> .gitignore
echo "venv/" >> .gitignore
echo "ENV/" >> .gitignore
echo "env/" >> .gitignore
echo "" >> .gitignore
echo "# IDE" >> .gitignore
echo ".vscode/" >> .gitignore
echo ".idea/" >> .gitignore
echo "*.swp" >> .gitignore
echo "*.swo" >> .gitignore
echo "" >> .gitignore
echo "# Project specific" >> .gitignore
echo "*.log" >> .gitignore
echo "temp/" >> .gitignore
echo "test_output/" >> .gitignore
echo "*.backup" >> .gitignore
```

#### **4.2: Create README.md for GitLab**
```bash
# Create a comprehensive README
echo "# 🔌 Power System Visualization Application" > README.md
echo "" >> README.md
echo "An interactive web application for power system analysis with AI assistant capabilities." >> README.md
echo "" >> README.md
echo "## ✨ Features" >> README.md
echo "" >> README.md
echo "- 🌐 **Interactive Network Visualization**: IEEE 118-bus power system topology" >> README.md
echo "- 📊 **SLR vs DLR Comparison**: Static vs Dynamic Line Rating analysis for 5 scenarios" >> README.md
echo "- 🤖 **AI Assistant**: Chat interface with power system knowledge and data completion" >> README.md
echo "- 📈 **Multi-Case Analysis**: Base case 42 with contingencies 56, 90, 123, 124, 158" >> README.md
echo "- 🔍 **Intelligent Data Completion**: AI fills missing data using physics-based algorithms" >> README.md
echo "" >> README.md
echo "## 🚀 Quick Start" >> README.md
echo "" >> README.md
echo "1. **Clone the repository:**" >> README.md
echo "   \`\`\`bash" >> README.md
echo "   git clone https://gitlab.com/your-username/power-system-visualization.git" >> README.md
echo "   cd power-system-visualization" >> README.md
echo "   \`\`\`" >> README.md
echo "" >> README.md
echo "2. **Install dependencies:**" >> README.md
echo "   \`\`\`bash" >> README.md
echo "   pip install -r requirements.txt" >> README.md
echo "   \`\`\`" >> README.md
echo "" >> README.md
echo "3. **Run the application:**" >> README.md
echo "   \`\`\`bash" >> README.md
echo "   python power_viz_with_database.py" >> README.md
echo "   \`\`\`" >> README.md
echo "" >> README.md
echo "4. **Open in browser:**" >> README.md
echo "   [http://127.0.0.1:8054](http://127.0.0.1:8054)" >> README.md
echo "" >> README.md
echo "## 📋 System Requirements" >> README.md
echo "" >> README.md
echo "- Python 3.8+" >> README.md
echo "- 4GB RAM (8GB recommended)" >> README.md
echo "- Modern web browser" >> README.md
echo "" >> README.md
echo "## 📖 Documentation" >> README.md
echo "" >> README.md
echo "- [Complete Setup Guide](APPLICATION_SETUP_GUIDE.md)" >> README.md
echo "- [Sharing Instructions](SHARING_GUIDE.md)" >> README.md
echo "- [File Verification](verify_setup.py)" >> README.md
echo "" >> README.md
echo "## 🎯 Key Features to Try" >> README.md
echo "" >> README.md
echo "1. **SLR vs DLR Analysis**: Select Base Case 42 → \"🔄 SLR vs DLR (5 Scenarios)\"" >> README.md
echo "2. **AI Chat**: Click 🤖 icon → Ask \"Check data quality\" or \"Explain SLR vs DLR\"" >> README.md
echo "3. **Network Graphs**: Explore \"🌐 Network Graph\" with different contingencies" >> README.md
echo "4. **Data Completion**: Click \"🔍 Analyze Data Quality\" for intelligent gap filling" >> README.md
echo "" >> README.md
echo "## 🤝 Contributing" >> README.md
echo "" >> README.md
echo "Contributions are welcome! Please read the setup guide and test your changes locally." >> README.md
echo "" >> README.md
echo "## 📄 License" >> README.md
echo "" >> README.md
echo "This project is for educational and research purposes." >> README.md
```

---

### **Step 5: Add Files to Git**

#### **5.1: Add Essential Files**
```bash
# Check what files you have
dir

# Add essential files (adjust based on what you have)
git add power_viz_with_database.py
git add data.db
git add requirements.txt
git add APPLICATION_SETUP_GUIDE.md
git add SHARING_GUIDE.md
git add verify_setup.py
git add README.md
git add .gitignore

# Add Python modules
git add data_viz_fall.py
git add branch_analysis.py
git add bus_analysis.py
git add generator_analysis_functions.py
git add database_manager.py
git add multi_database_manager.py
git add dynamic_case_management.py
git add data_availability.py

# Add AI features (if available)
git add simple_rag.py
git add intelligent_data_completion.py
git add entity_extraction.py

# Add analysis features (if available)
git add enhanced_network_graphs.py
git add case_comparison.py
git add network_comparison.py
git add comprehensive_trend_analyzer.py
git add individual_analysis.py
git add network_comparison_helper.py
git add direct_network_integration.py

# Add configuration files (if available)
git add config.json
git add start_app.bat
```

#### **5.2: Check Status and Commit**
```bash
# Check what's staged
git status

# Commit the files
git commit -m "Initial commit: Power System Visualization Application

- Interactive IEEE 118-bus power system visualization
- SLR vs DLR comparison analysis (5 scenarios)
- AI assistant with data completion capabilities
- Network graph visualization with violation detection
- Multi-case contingency analysis
- Comprehensive setup and sharing documentation"
```

---

### **Step 6: Connect to GitLab**

#### **6.1: Add GitLab Remote**
```bash
# Add GitLab as remote origin (replace 'your-username' with your actual GitLab username)
git remote add origin https://gitlab.com/your-username/power-system-visualization.git

# Verify remote was added
git remote -v
```

#### **6.2: Push to GitLab**
```bash
# Push to GitLab (main branch)
git branch -M main
git push -u origin main
```

**Note**: You'll be prompted for GitLab credentials:
- **Username**: Your GitLab username
- **Password**: Your GitLab password (or access token)

---

### **Step 7: Configure GitLab Repository Settings**

#### **7.1: Access Repository Settings**
1. Go to your GitLab repository: `https://gitlab.com/your-username/power-system-visualization`
2. Click **"Settings"** → **"General"**

#### **7.2: Update Repository Description**
```
Description: Interactive Power System Visualization with AI Assistant - IEEE 118-bus system analysis, SLR vs DLR comparison, network graphs, and intelligent data completion
Topics: power-systems, visualization, ai, ieee-118-bus, dlr, slr, dash, plotly
```

#### **7.3: Set Visibility**
- **Public**: Anyone can see and clone
- **Internal**: GitLab users can see
- **Private**: Only you and invited users

---

### **Step 8: Create GitLab Pages (Optional Website)**

#### **8.1: Enable GitLab Pages**
1. In your repository, go to **"Settings"** → **"Pages"**
2. Create `.gitlab-ci.yml` file:

```yaml
# Create .gitlab-ci.yml for GitLab Pages
pages:
  stage: deploy
  script:
    - mkdir public
    - cp APPLICATION_SETUP_GUIDE.md public/
    - cp SHARING_GUIDE.md public/
    - cp README.md public/index.md
  artifacts:
    paths:
      - public
  only:
    - main
```

#### **8.2: Add and Push GitLab Pages Config**
```bash
# Create the GitLab CI file
echo "pages:" > .gitlab-ci.yml
echo "  stage: deploy" >> .gitlab-ci.yml
echo "  script:" >> .gitlab-ci.yml
echo "    - mkdir public" >> .gitlab-ci.yml
echo "    - cp *.md public/" >> .gitlab-ci.yml
echo "  artifacts:" >> .gitlab-ci.yml
echo "    paths:" >> .gitlab-ci.yml
echo "      - public" >> .gitlab-ci.yml
echo "  only:" >> .gitlab-ci.yml
echo "    - main" >> .gitlab-ci.yml

# Add and commit
git add .gitlab-ci.yml
git commit -m "Add GitLab Pages configuration"
git push origin main
```

---

### **Step 9: Share Your GitLab Repository**

#### **9.1: Get Repository URL**
Your repository will be available at:
```
https://gitlab.com/your-username/power-system-visualization
```

#### **9.2: Clone Instructions for Others**
```bash
# Anyone can clone your repository with:
git clone https://gitlab.com/your-username/power-system-visualization.git
cd power-system-visualization
python verify_setup.py
pip install -r requirements.txt
python power_viz_with_database.py
```

#### **9.3: Share Message Template**
```
🔌 Power System Visualization Application on GitLab!

I've shared my interactive power system analysis application:
https://gitlab.com/your-username/power-system-visualization

Features:
✅ IEEE 118-bus system visualization
✅ SLR vs DLR comparison (5 scenarios)  
✅ AI assistant with data completion
✅ Interactive network graphs
✅ Multi-case contingency analysis

Quick Start:
1. git clone https://gitlab.com/your-username/power-system-visualization.git
2. cd power-system-visualization
3. pip install -r requirements.txt
4. python power_viz_with_database.py
5. Open: http://127.0.0.1:8054

Complete setup guide included in the repository!
```

---

### **Step 10: Manage Your Repository**

#### **10.1: Update Your Code**
```bash
# When you make changes locally:
git add .
git commit -m "Description of your changes"
git push origin main
```

#### **10.2: Create Branches for Features**
```bash
# Create a new branch for features
git checkout -b feature-name
# Make changes, commit, and push
git push origin feature-name
# Then create merge request on GitLab
```

#### **10.3: Track Issues and Collaboration**
- Use GitLab **Issues** to track bugs/features
- Use **Merge Requests** for code review
- Use **Wiki** for additional documentation

---

## 🎉 **Your Application is Now on GitLab!**

**Repository URL**: `https://gitlab.com/your-username/power-system-visualization`

**Next Steps**:
1. ✅ Share the GitLab URL with colleagues
2. ✅ Add collaborators if needed (Settings → Members)
3. ✅ Star your own repository
4. ✅ Add topics/tags for discoverability
5. ✅ Monitor clone/download statistics

**Your power system visualization application is now accessible to the world! 🚀**