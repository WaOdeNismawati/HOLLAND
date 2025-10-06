# Decision Support System for College Major Recommendation

## Overview
A comprehensive Decision Support System (DSS) that helps students determine their interests and talents to recommend suitable college majors using the RIASEC Holland test integrated with Analytic Network Process (ANP) methodology.

## Features

### 🎓 User Management
- **Student Login & Authentication**: Secure user accounts with role-based access
- **Student Dashboard**: Personalized interface showing test progress and results
- **Admin Panel**: Test monitoring and data management capabilities

### 📝 RIASEC Holland Test
- **Comprehensive Assessment**: 18 carefully designed questions covering all 6 Holland personality types:
  - **R** - Realistic: Practical, hands-on, tool/machine oriented
  - **I** - Investigative: Analytical, scientific, problem-solving oriented  
  - **A** - Artistic: Creative, expressive, aesthetic oriented
  - **S** - Social: Helping, teaching, people oriented
  - **E** - Enterprising: Leading, persuading, business oriented
  - **C** - Conventional: Organizing, data-processing, detail oriented

- **Interactive Interface**: User-friendly 5-point Likert scale assessment
- **Progress Tracking**: Real-time progress monitoring during test completion

### 🧠 Advanced ANP (Analytic Network Process) Integration
- **Sophisticated Decision Making**: Replaces simple rule-based recommendations with mathematical decision analysis
- **Comprehensive Major Database**: 37+ college majors with detailed RIASEC characteristic mappings
- **Multi-Criteria Analysis**: 
  - Uses student's RIASEC scores as criteria weights
  - Evaluates major-student fit through pairwise comparisons
  - Generates stable priority rankings through supermatrix calculation

### 📊 Enhanced Results & Visualization
- **ANP-Based Rankings**: Top 5 recommended majors with confidence scores
- **Interactive Charts**: 
  - RIASEC profile radar charts
  - Major ranking bar charts with ANP scores
  - Comparative analysis visualizations
- **Detailed Analysis**: 
  - Major-specific RIASEC requirement breakdowns
  - Alignment analysis between student profile and major requirements
  - Comprehensive career development suggestions

### 🎯 Comprehensive Major Coverage
**Engineering & Technology**: Teknik Mesin, Teknik Informatika, Teknik Elektro, Teknik Sipil, Arsitektur, Teknik Industri

**Health Sciences**: Kedokteran, Farmasi, Keperawatan, Kesehatan Masyarakat

**Business & Economics**: Manajemen, Akuntansi, Ekonomi, Administrasi Bisnis, Keuangan dan Perbankan

**Social Sciences & Education**: Psikologi, Pendidikan, Sosiologi, Hubungan Internasional, Ilmu Komunikasi

**Arts & Creative**: Desain Komunikasi Visual, Seni Rupa, Desain Interior, Musik, Film dan Televisi

**Science & Research**: Matematika, Fisika, Kimia, Biologi, Statistika

**Law & Public Service**: Ilmu Hukum, Administrasi Publik, Ilmu Politik

**Agriculture & Environment**: Pertanian, Kehutanan, Lingkungan

**Language & Literature**: Sastra Indonesia, Sastra Inggris, Bahasa dan Sastra

## Technical Architecture

### Backend
- **Framework**: Python with Streamlit
- **Database**: SQLite with comprehensive schema
- **ANP Engine**: Custom implementation using NumPy and SciPy
- **Authentication**: Secure bcrypt password hashing

### Frontend
- **Interactive UI**: Streamlit-based responsive interface
- **Data Visualization**: Plotly for interactive charts and graphs
- **User Experience**: Intuitive navigation with progress tracking

### ANP Implementation
- **Mathematical Foundation**: 
  - Eigenvalue method for priority calculation
  - Supermatrix construction with criteria-alternative relationships
  - Limit matrix calculation for stable weights
- **Integration Strategy**: 
  - 70% weight on RIASEC alignment
  - 30% weight on ANP priority scores
  - Equal weighting (1/6) for all RIASEC criteria

## Installation & Setup

```bash
# Clone repository
git clone [repository-url]
cd decision-support-system

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

## Usage

1. **Login**: Students log in with provided credentials
2. **Take Test**: Complete 18 RIASEC assessment questions
3. **View Results**: 
   - See RIASEC personality profile
   - Review ANP-based major rankings
   - Explore detailed career guidance
4. **Career Planning**: Use comprehensive recommendations for academic and career decisions

## RIASEC + ANP Integration Methodology

### Traditional Approach Limitations
- Simple rule-based matching
- Limited major coverage
- No quantitative scoring
- Inflexible recommendation logic

### ANP Enhancement Benefits
- **Multi-criteria Decision Analysis**: Considers complex relationships between personality traits and major requirements
- **Quantitative Rankings**: Provides confidence scores for each recommendation
- **Comprehensive Coverage**: Evaluates 37+ majors simultaneously
- **Adaptive Framework**: Easy to add new majors or adjust criteria weights
- **Mathematical Rigor**: Uses established decision science methodology

### ANP Process Flow
1. **Input**: Student's RIASEC scores from assessment
2. **Normalization**: Scale scores to 0-1 range for comparison
3. **Supermatrix Construction**: Build relationships between RIASEC criteria and major alternatives
4. **Priority Calculation**: Use eigenvalue method for stable weights
5. **Composite Scoring**: Combine RIASEC alignment with ANP priorities
6. **Ranking**: Generate ordered list of best-fit majors

## Future Enhancements
- Machine learning integration for improved predictions
- Extended major database with international programs
- Career outcome tracking and validation
- Mobile application development
- Multi-language support

## Contributors
Developed as part of educational technology initiative to improve student academic guidance and career decision-making processes.