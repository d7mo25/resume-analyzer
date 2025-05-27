import streamlit as st
import base64
import pandas as pd
import io
import pymysql
import re
from pymysql.cursors import DictCursor
import nltk
import spacy
import configparser
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
import matplotlib.pyplot as plt
import numpy as np
import hashlib
import time
import firebase_admin
from firebase_admin import credentials, auth
import requests
import json

# Page configuration
st.set_page_config(
    page_title="AIU Smart Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Firebase configuration - Replace with your actual config
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyAtcGf6D0sOJaX7YxouzMd13NzlwibbNkU",
    "authDomain": "test-login-page-506b6.firebaseapp.com",
    "projectId": "test-login-page-506b6",
    "storageBucket": "test-login-page-506b6.firebasestorage.app",
    "messagingSenderId": "548551326383",
    "appId": "1:548551326383:web:419f60c2935157a6a5f25a"
}

# Initialize Firebase Admin SDK (you'll need to add your service account key)
# Replace 'path/to/serviceAccountKey.json' with your actual service account key path
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate('C:\\Users\\ABDELRAHMAN\\OneDrive\\سطح المكتب\\stramlit app\\serviceAccountKey.json')  # Replace with your path
        firebase_admin.initialize_app(cred)
except Exception as e:
    st.error(f"Firebase initialization error: {e}")

# Custom CSS for styling
def load_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .success-message {
        background: linear-gradient(45deg, #56ab2f, #a8e6cf);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
    }
    
    .error-message {
        background: linear-gradient(45deg, #ff416c, #ff4b2b);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
    }
    
    .otp-input {
        width: 60px;
        height: 60px;
        text-align: center;
        font-size: 24px;
        border: 2px solid #ddd;
        border-radius: 8px;
        margin: 0 5px;
    }
    
    .keyword-badge {
        display: inline-block;
        padding: 8px 15px;
        margin: 5px;
        border-radius: 20px;
        color: white;
        font-weight: 500;
        font-size: 0.9em;
    }
    
    .profile-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .ats-score {
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        color: #667eea;
        margin: 1rem 0;
    }
    
    .admin-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 2rem 0;
        color: white;
    }
    
    .danger-zone {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def init_session_state():                                                                
 if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'
if 'user_email' not in st.session_state:
    st.session_state.user_email = ''
if 'user_id' not in st.session_state:
    st.session_state.user_id = ''
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = ''
if 'otp_timestamp' not in st.session_state:
    st.session_state.otp_timestamp = 0
if 'reset_phone' not in st.session_state:
    st.session_state.reset_phone = ''
    if 'demo_user_data' not in st.session_state:
        st.session_state.demo_user_data = [
            {
                'id': 1,
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'phone': '+1234567890',
                'address': '123 Main St, City, State',
                'linkedin': 'linkedin.com/in/johndoe',
                'github': 'github.com/johndoe',
                'ats_score': 75.5,
                'upload_date': '2024-01-15'
            },
            {
                'id': 2,
                'name': 'Jane Smith',
                'email': 'jane.smith@example.com',
                'phone': '+1987654321',
                'address': '456 Oak Ave, City, State',
                'linkedin': 'linkedin.com/in/janesmith',
                'github': 'github.com/janesmith',
                'ats_score': 82.3,
                'upload_date': '2024-01-16'
            }
        ]

# Firebase Authentication functions
def sign_in_with_email_password(email, password):
    """Sign in user with email and password using Firebase REST API"""
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_CONFIG['apiKey']}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            user_data = response.json()
            return True, user_data
        else:
            error_data = response.json()
            return False, error_data.get('error', {}).get('message', 'Login failed')
    except Exception as e:
        return False, str(e)

def send_otp_via_firebase(phone_number):
    """Send OTP using Firebase Authentication with phone number"""
    try:
        # This uses Firebase REST API for sending OTP
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendVerificationCode?key={FIREBASE_CONFIG['apiKey']}"
        
        payload = {
            "phoneNumber": phone_number,
            "recaptchaToken": "test"  # In production, you'll need proper reCAPTCHA token
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            session_info = result.get('sessionInfo')
            st.session_state.firebase_session_info = session_info
            st.session_state.otp_sent = True
            st.session_state.otp_timestamp = time.time()
            return True, "OTP sent successfully via Firebase"
        else:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Failed to send OTP')
            
            # Fallback to demo OTP if Firebase fails
            import random
            otp = str(random.randint(100000, 999999))
            st.session_state.generated_otp = otp
            st.session_state.otp_timestamp = time.time()
            st.session_state.otp_sent = True
            return True, f"Firebase error: {error_message}. Demo OTP: {otp}"
            
    except Exception as e:
        # Fallback to demo OTP
        import random
        otp = str(random.randint(100000, 999999))
        st.session_state.generated_otp = otp
        st.session_state.otp_timestamp = time.time()
        st.session_state.otp_sent = True
        return True, f"Connection error. Demo OTP: {otp}"

def verify_otp_with_firebase(phone_number, otp_code):
    """Verify OTP using Firebase Authentication"""
    try:
        # If we have Firebase session info, use Firebase verification
        if hasattr(st.session_state, 'firebase_session_info') and st.session_state.firebase_session_info:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPhoneNumber?key={FIREBASE_CONFIG['apiKey']}"
            
            payload = {
                "sessionInfo": st.session_state.firebase_session_info,
                "code": otp_code
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                return True, "OTP verified successfully with Firebase"
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Invalid OTP')
                return False, error_message
        
        # Fallback to demo OTP verification
        else:
            return verify_demo_otp(otp_code)
            
    except Exception as e:
        # Fallback to demo OTP verification
        return verify_demo_otp(otp_code)

def verify_demo_otp(entered_otp):
    """Verify demo OTP for fallback"""
    if not st.session_state.otp_sent:
        return False, "No OTP sent"
    
    # Check if OTP is expired (5 minutes)
    if time.time() - st.session_state.otp_timestamp > 300:
        return False, "OTP expired"
    
    if hasattr(st.session_state, 'generated_otp') and entered_otp == st.session_state.generated_otp:
        return True, "OTP verified successfully"
    
    return False, "Invalid OTP"

# Login page (simplified - only login, no registration)
def login_page():
    st.markdown('<div class="main-header"><h1>🎓 AIU Smart Resume Analyzer</h1><p>Login to access the resume analysis system</p></div>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            
            st.markdown("### 🔐  Login")
            
            with st.form("login_form"):
                email = st.text_input("📧 Email Address", placeholder="Enter your email")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                remember_me = st.checkbox("Remember Me")
                
                col_login, col_forgot = st.columns(2)
                with col_login:
                    login_submitted = st.form_submit_button("Login")
                with col_forgot:
                    if st.form_submit_button("Forgot Password?"):
                        st.session_state.current_page = 'forgot_password'
                        st.rerun()
            
            if login_submitted:
                if not email or not password:
                    st.markdown('<div class="error-message">❌ Please fill in all fields</div>', unsafe_allow_html=True)
                elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    st.markdown('<div class="error-message">❌ Please enter a valid email address</div>', unsafe_allow_html=True)
                else:
                    with st.spinner("🔐 Signing in..."):
                        success, result = sign_in_with_email_password(email, password)
                        
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.user_id = result.get('localId', '')
                            st.session_state.current_page = 'main_dashboard'
                            st.markdown('<div class="success-message">✅ Login successful! Redirecting to Dashboard...</div>', unsafe_allow_html=True)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="error-message">❌ {result}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# Forgot password page with Firebase OTP - MODIFIED TO LOGIN DIRECTLY AFTER OTP
def forgot_password_page():
    st.markdown('<div class="main-header"><h1>🔑 Account Recovery</h1><p>Enter your phone number to verify your identity</p></div>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            
            if not st.session_state.otp_sent:
                st.markdown("### 📱 Enter Phone Number")
                st.markdown("We'll send you an OTP via Firebase to verify your identity and log you in")
                
                with st.form("phone_reset_form"):
                    phone = st.text_input("Phone Number", placeholder="+1234567890", help="Include country code (e.g., +60123456789)")
                    submitted = st.form_submit_button("Send OTP via Firebase")
                
                if submitted:
                    if not phone:
                        st.markdown('<div class="error-message">❌ Please enter your phone number</div>', unsafe_allow_html=True)
                    elif not re.match(r'^\+[1-9]\d{1,14}$', phone):
                        st.markdown('<div class="error-message">❌ Please enter a valid phone number with country code</div>', unsafe_allow_html=True)
                    else:
                        st.session_state.reset_phone = phone
                        with st.spinner("📱 Sending OTP via Firebase..."):
                            success, message = send_otp_via_firebase(phone)
                            if success:
                                st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
            
            else:
                st.markdown("### ⏰ Enter Verification Code")
                st.markdown(f"We've sent a 6-digit code to **{st.session_state.reset_phone}**")
                st.markdown("*After verification, you'll be logged in automatically*")
                
                with st.form("otp_reset_form"):
                    otp_input = st.text_input("Enter 6-digit OTP", max_chars=6, help="Check your SMS messages")
                    
                    col_verify, col_resend = st.columns(2)
                    with col_verify:
                        verify_submitted = st.form_submit_button("Verify & Login")
                    with col_resend:
                        resend_submitted = st.form_submit_button("Resend OTP")
                
                if verify_submitted:
                    if len(otp_input) != 6:
                        st.markdown('<div class="error-message">❌ Please enter a complete 6-digit OTP</div>', unsafe_allow_html=True)
                    else:
                        with st.spinner("🔍 Verifying OTP and logging you in..."):
                            success, message = verify_otp_with_firebase(st.session_state.reset_phone, otp_input)
                            if success:
                                # Directly log the user in instead of asking for new password
                                st.session_state.authenticated = True
                                st.session_state.user_email = f"user_{st.session_state.reset_phone}"  # Use phone as identifier
                                st.session_state.user_id = hashlib.md5(st.session_state.reset_phone.encode()).hexdigest()
                                st.session_state.current_page = 'main_dashboard'
                                
                                # Reset OTP states
                                st.session_state.otp_sent = False
                                st.session_state.generated_otp = ''
                                st.session_state.reset_phone = ''
                                if hasattr(st.session_state, 'firebase_session_info'):
                                    del st.session_state.firebase_session_info
                                
                                st.markdown('<div class="success-message">✅ OTP Verified! Logging you in...</div>', unsafe_allow_html=True)
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
                
                if resend_submitted:
                    with st.spinner("📱 Resending OTP via Firebase..."):
                        success, message = send_otp_via_firebase(st.session_state.reset_phone)
                        if success:
                            st.markdown('<div class="success-message">📱 New OTP sent via Firebase!</div>', unsafe_allow_html=True)
                            st.rerun()
                
                if st.button("← Use Different Phone Number"):
                    st.session_state.otp_sent = False
                    st.session_state.generated_otp = ''
                    if hasattr(st.session_state, 'firebase_session_info'):
                        del st.session_state.firebase_session_info
                    st.rerun()
            
            if st.button("← Back to Login"):
                st.session_state.current_page = 'login'
                st.session_state.otp_sent = False
                st.session_state.generated_otp = ''
                if hasattr(st.session_state, 'firebase_session_info'):
                    del st.session_state.firebase_session_info
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# Resume analysis functions (keeping the original functions)
keyword_categories = {
    "Technical Skills": [
        "Python", "Java", "C++", "SQL", "JavaScript", "HTML", "CSS", "Git", "GitHub",
        "Docker", "AWS", "Azure", "Linux", "TensorFlow", "PyTorch", "Power BI",
        "Excel", "Kubernetes", "MongoDB", "MySQL", "React", "Node.js", "Flask",
        "Django", "REST", "API", "GraphQL", "Jenkins", "Terraform", "Ansible",
        "Linux Shell", "Bash", "Scala", "Perl", "Ruby", "Swift", "Objective-C",
        "Firebase", "Spark", "Hadoop", "Kafka", "RabbitMQ", "Redis", "Elasticsearch",
        "C#", ".NET", "Visual Studio", "Android", "iOS", "Unity", "Xamarin",
        "MATLAB", "Tableau", "SAS", "PowerShell"
    ],
    "Soft Skills": [
        "Communication", "Teamwork", "Leadership", "Time Management", "Adaptability",
        "Critical Thinking", "Problem Solving", "Creativity", "Conflict Resolution",
        "Decision Making", "Empathy", "Collaboration", "Organization", "Integrity",
        "Negotiation", "Flexibility", "Responsibility", "Patience", "Work Ethic",
        "Attention to Detail", "Active Listening", "Multitasking", "Positive Attitude",
        "Self-motivation", "Stress Management", "Persuasion", "Public Speaking",
        "Mentoring", "Coaching", "Emotional Intelligence", "Open-mindedness",
        "Analytical Thinking", "Resilience", "Dependability", "Accountability",
        "Initiative", "Creativity", "Adaptability", "Conflict Management",
        "Cultural Awareness", "Leadership Development", "Customer Service",
        "Collaboration Tools", "Presentation Skills", "Team Building",
        "Organizational Skills", "Strategic Planning", "Critical Observation"
    ],
    "Work Experience": [
        "Intern", "Manager", "Engineer", "Developer", "Team Lead", "Supervisor",
        "Analyst", "Architect", "Consultant", "Co-Founder", "Project", "Freelancer",
        "Research Assistant", "Trainee", "Coordinator", "Mentor", "Start-up",
        "Contract", "Volunteer", "Full-time", "Part-time", "Temporary", "Permanent",
        "Associate", "Executive", "Officer", "Specialist", "Advisor", "Technician",
        "Designer", "Quality Assurance", "Product Owner", "Scrum Master",
        "Business Analyst", "Operations Manager", "Customer Support",
        "Sales Manager", "Marketing Manager", "Account Manager", "Financial Analyst",
        "Human Resources", "Recruiter", "Trainer", "Project Manager",
        "Software Tester", "Data Scientist", "Systems Administrator",
        "Network Engineer", "Database Administrator"
    ],
    "Language Proficiency": [
        "English", "French", "Spanish", "Mandarin", "Arabic", "German", "Tamil",
        "Hindi", "Malay", "Japanese", "Proficient", "Fluent", "Beginner",
        "Intermediate", "Native", "IELTS", "TOEFL", "Language", "Multilingual",
        "Bilingual", "Conversational", "Basic", "Advanced", "Reading", "Writing",
        "Speaking", "Listening", "Translation", "Interpretation", "Language Skills",
        "Dialect", "Accent", "Grammar", "Vocabulary", "Communication Skills",
        "Cantonese", "Russian", "Portuguese", "Italian", "Dutch", "Korean",
        "Swahili", "Hebrew", "Turkish", "Vietnamese", "Persian", "Bengali",
        "Urdu", "Polish", "Ukrainian", "Greek", "Latin", "Norwegian", "Swedish"
    ],
    "Achievements": [
        "Award", "Winner", "Runner-up", "Finalist", "Rank", "Competition",
        "Hackathon", "Published", "Patent", "Top 10%", "Scholarship", "Merit",
        "Distinction", "Leadership Award", "Star Performer", "Recognition",
        "Promotion", "Presented", "Excellence", "Dean's List", "Certificate",
        "Certification", "Honors", "Fellowship", "Nominee", "Best Paper",
        "Best Presentation", "Outstanding", "Employee of the Month", "Innovator",
        "Contributor", "Volunteer Award", "Research Grant", "Keynote Speaker",
        "Panelist", "Reviewer", "Editor", "Finalist Award", "Community Service",
        "Publication", "Conference Speaker", "Training Completed", "Accreditation",
        "Performance Bonus", "Customer Satisfaction", "Successful Project Delivery"
    ]
}

CATEGORY_COLORS = {
    "Technical Skills": "#1f77b4",
    "Soft Skills": "#ff7f0e", 
    "Work Experience": "#2ca02c",
    "Language Proficiency": "#d62728",
    "Achievements": "#9467bd"
}

def pdf_reader(file_buffer):
    try:
        resource_manager = PDFResourceManager()
        output_string = io.StringIO()
        converter = TextConverter(resource_manager, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(resource_manager, converter)
        file_buffer.seek(0)
        for page in PDFPage.get_pages(file_buffer, caching=True, check_extractable=True):
            interpreter.process_page(page)
        converter.close()
        text = output_string.getvalue()
        output_string.close()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""

def extract_full_name(text):
    lines = text.split('\n')[:10]
    for line in lines:
        line = line.strip()
        if len(line.split()) >= 2 and len(line.split()) <= 4:
            if all(word.replace('.', '').isalpha() for word in line.split()):
                return line
    return "N/A"

def extract_basic_info_from_text(text):
    name = extract_full_name(text)
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?(?:\d{2,4}[-.\s]?){2,3}", text)
    address_match = re.search(r"Address\s*[:\-]?\s*(.+)", text, re.IGNORECASE)
    linkedin_match = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
    github_match = re.search(r"(https?://)?(www\.)?github\.com/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
    
    return {
        'name': name,
        'email': email_match.group(0) if email_match else "N/A",
        'phone': phone_match.group(0).strip() if phone_match else "N/A",
        'address': address_match.group(1).strip() if address_match else "N/A",
        'linkedin': linkedin_match.group(0) if linkedin_match else "N/A",
        'github': github_match.group(0) if github_match else "N/A",
    }

def extract_keywords(text, keywords):
    text_lower = text.lower()
    found = []
    for kw in keywords:
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(kw)
    return found

def calculate_ats_score(extraction_results):
    total_found = sum(len(words) for words in extraction_results.values())
    total_possible = sum(len(keyword_categories[cat]) for cat in extraction_results.keys())
    if total_possible == 0:
        return 0
    return round((total_found / total_possible) * 100, 2)

def render_colored_keywords(words, category):
    color = CATEGORY_COLORS.get(category, "#444444")
    badges_html = ""
    for kw in sorted(words):
        badges_html += f'<span class="keyword-badge" style="background-color:{color};">{kw}</span>'
    return badges_html

def show_detailed_analysis(extraction_results):
    for category, found_keywords in extraction_results.items():
        color = CATEGORY_COLORS.get(category, "#444444")
        st.markdown(f"### <span style='color:{color}'>{category}</span>", unsafe_allow_html=True)
        
        if found_keywords:
            st.markdown(render_colored_keywords(found_keywords, category), unsafe_allow_html=True)
            st.markdown(f"**Found {len(found_keywords)} keywords**")
        else:
            st.markdown("❌ No keywords found in this category.")
        
        st.markdown("---")

def plot_keyword_comparison(extraction_results):
    categories = list(extraction_results.keys())
    found_counts = [len(extraction_results[cat]) for cat in categories]
    total_keywords = [len(keyword_categories[cat]) for cat in categories]

    fig, ax = plt.subplots(figsize=(12, 8))
    y_pos = np.arange(len(categories))

    bars1 = ax.barh(y_pos, found_counts, color='#667eea', alpha=0.8, label='Keywords Found')
    bars2 = ax.barh(y_pos, total_keywords, color='#e0e0e0', alpha=0.5, label='Total Available')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.invert_yaxis()
    ax.set_xlabel('Number of Keywords')
    ax.set_title('Resume Keywords Analysis by Category', fontsize=16, fontweight='bold')
    ax.legend()

    for i, (found, total) in enumerate(zip(found_counts, total_keywords)):
        ax.text(found + 0.5, i, f'{found}/{total}', va='center', fontweight='bold')

    plt.tight_layout()
    return fig

def show_pdf(file_buffer):
    file_buffer.seek(0)
    pdf_bytes = file_buffer.read()
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    
    pdf_display = f'''
    <div style="width: 100%; height: 600px; overflow: auto; border: 2px solid #ddd; border-radius: 10px;">
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" height="600px" type="application/pdf"
                style="border: none;">
        </iframe>
    </div>
    '''
    st.markdown(pdf_display, unsafe_allow_html=True)

# Resume upload and analysis page
def resume_upload_page():
    st.markdown('<div class="main-header"><h1>📄 Resume Analysis</h1><p>Upload your resume for comprehensive analysis</p></div>', unsafe_allow_html=True)
    
    # Logout button
    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    with col3:
        if st.button("🚪 Logout"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
       
    # File upload
    pdf_file = st.file_uploader("📎 Upload your Resume (PDF only)", type=["pdf"], 
                               help="Select a PDF file containing your resume")
    
    if pdf_file:
        # Show PDF preview
        st.markdown("### 👀 Resume Preview")
        pdf_bytes = pdf_file.read()
        pdf_buffer = io.BytesIO(pdf_bytes)
        show_pdf(pdf_buffer)
        
        # Extract and analyze text
        with st.spinner("🔍 Analyzing your resume..."):
            pdf_buffer.seek(0)
            resume_text = pdf_reader(pdf_buffer)
            
            if not resume_text.strip():
                st.error("❌ Could not extract text from the PDF. Please ensure it's a readable PDF file.")
                return
            
            # Extract basic information
            basic_info = extract_basic_info_from_text(resume_text)
            
            # Extract keywords by category
            extraction_results = {}
            for category, keywords in keyword_categories.items():
                extraction_results[category] = extract_keywords(resume_text, keywords)
            
            # Calculate ATS score
            ats_score = calculate_ats_score(extraction_results)
        
        # Display results
        st.markdown("---")
        
        # Candidate Profile
        st.markdown("### 👤 Candidate Profile")
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**👤 Full Name:** {basic_info.get('name', 'N/A')}")
            st.markdown(f"**📧 Email:** {basic_info.get('email', 'N/A')}")
            st.markdown(f"**📱 Phone:** {basic_info.get('phone', 'N/A')}")
        with col2:
            st.markdown(f"**🏠 Address:** {basic_info.get('address', 'N/A')}")
            st.markdown(f"**💼 LinkedIn:** {basic_info.get('linkedin', 'N/A')}")
            st.markdown(f"**💻 GitHub:** {basic_info.get('github', 'N/A')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ATS Score
        st.markdown("---")
        st.markdown('<div class="ats-score">🎯 ATS Score</div>', unsafe_allow_html=True)
        
        # Score gauge
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            score_color = "#e74c3c" if ats_score < 30 else "#f39c12" if ats_score < 60 else "#27ae60"
            st.markdown(f'''
            <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, {score_color}20, {score_color}10); 
                        border-radius: 20px; border: 3px solid {score_color};">
                <h1 style="color: {score_color}; font-size: 4rem; margin: 0;">{ats_score}%</h1>
                <p style="font-size: 1.2rem; margin: 0;">Resume Compatibility Score</p>
            </div>
            ''', unsafe_allow_html=True)
        
        # Detailed Analysis
        st.markdown("---")
        st.markdown("### 🔍 Detailed Keyword Analysis")
        show_detailed_analysis(extraction_results)
        
        # Visualization
        st.markdown("### 📊 Keywords Visualization")
        fig = plot_keyword_comparison(extraction_results)
        st.pyplot(fig)
        
        # Summary and Recommendations
        st.markdown("---")
        st.markdown("### 💡 Recommendations")
        
        total_keywords_found = sum(len(words) for words in extraction_results.values())
        
        if ats_score < 30:
            st.error("🔴 **Low ATS Score**: Your resume needs significant improvement to pass ATS systems.")
        elif ats_score < 60:
            st.warning("🟡 **Moderate ATS Score**: Your resume has potential but could benefit from more relevant keywords.")
        else:
            st.success("🟢 **Good ATS Score**: Your resume is well-optimized for ATS systems!")
        
        # Category-specific recommendations
        for category, keywords in extraction_results.items():
            if len(keywords) == 0:
                st.info(f"💭 Consider adding relevant **{category}** to strengthen your resume.")

# Admin panel
# Admin panel function continuation
def admin_panel():
    st.markdown('<div class="main-header"><h1>🔧 Admin Panel</h1><p>Manage system data and user records</p></div>', unsafe_allow_html=True)
    
    # Admin authentication
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="auth-container">', unsafe_allow_html=True)
                st.markdown("### 🔐 Admin Login")
                
                with st.form("admin_login_form"):
                    admin_user = st.text_input("👤 Username", placeholder="Enter admin username")
                    admin_password = st.text_input("🔒 Password", type="password", placeholder="Enter admin password")
                    submitted = st.form_submit_button("Login as Admin")
                
                if submitted:
                    if admin_user == "Masliza" and admin_password == "Masliza123":
                        st.session_state.authenticated = True
                        st.markdown('<div class="success-message">✅ Welcome Madam Masliza!</div>', unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.markdown('<div class="error-message">❌ Invalid admin credentials</div>', unsafe_allow_html=True)
                
                if st.button("← Back to Login"):
                    st.session_state.current_page = 'login'
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Admin dashboard
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("### 📊 Admin Dashboard")
        with col2:
            if st.button("🚪 Admin Logout"):
                st.session_state.authenticated = False
                st.rerun()
        
        # Demo data for admin panel (simulating database records)
        if 'demo_user_data' not in st.session_state:
            st.session_state.demo_user_data = [
                {
                    'id': 1,
                    'name': 'John Doe',
                    'email': 'john.doe@example.com',
                    'phone': '+1234567890',
                    'address': '123 Main St, City, State',
                    'linkedin': 'linkedin.com/in/johndoe',
                    'github': 'github.com/johndoe',
                    'ats_score': 75.5,
                    'upload_date': '2024-01-15'
                },
                {
                    'id': 2,
                    'name': 'Jane Smith',
                    'email': 'jane.smith@example.com',
                    'phone': '+1987654321',
                    'address': '456 Oak Ave, City, State',
                    'linkedin': 'linkedin.com/in/janesmith',
                    'github': 'github.com/janesmith',
                    'ats_score': 82.3,
                    'upload_date': '2024-01-16'
                }
            ]
        
        # Display user data
        if st.session_state.demo_user_data:
            st.markdown("### 📋 User Data Records")
            df = pd.DataFrame(st.session_state.demo_user_data)
            st.dataframe(df, use_container_width=True)
            
            # Download CSV functionality
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV Report",
                data=csv,
                file_name="User_Data_Report.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Delete all data button
            st.markdown("---")
            st.markdown("### ⚠️ Danger Zone")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Delete All User Data", type="secondary"):
                    st.session_state.show_delete_confirmation = True
            
            # Confirmation dialog
            if st.session_state.get('show_delete_confirmation', False):
                with col2:
                    st.warning("⚠️ This action cannot be undone!")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("✅ Confirm Delete", type="primary"):
                            st.session_state.demo_user_data = []
                            st.session_state.show_delete_confirmation = False
                            st.success("🗑️ All user data has been deleted!")
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ Cancel", type="secondary"):
                            st.session_state.show_delete_confirmation = False
                            st.rerun()
        else:
            st.info("📝 No user data found in the system.")

# Main application flow
def main():
    load_css()
    init_session_state()
    
    # Route to appropriate page
    if not st.session_state.authenticated:
        if st.session_state.current_page == 'forgot_password':
            forgot_password_page()
        elif st.session_state.current_page == 'new_password':
            new_password_page()
        else:
            login_page()
    else:
      resume_upload_page()

# Save uploaded resume data (simulation of database insert)
def save_resume_data(basic_info, ats_score):
    """Simulate saving resume data to database"""
    if 'demo_user_data' not in st.session_state:
        st.session_state.demo_user_data = []
    
    # Generate new ID
    new_id = len(st.session_state.demo_user_data) + 1
    
    # Add current timestamp
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Create new record
    new_record = {
        'id': new_id,
        'name': basic_info.get('name', 'N/A'),
        'email': basic_info.get('email', 'N/A'),
        'phone': basic_info.get('phone', 'N/A'),
        'address': basic_info.get('address', 'N/A'),
        'linkedin': basic_info.get('linkedin', 'N/A'),
        'github': basic_info.get('github', 'N/A'),
        'ats_score': ats_score,
        'upload_date': current_date
    }
    
    # Add to session state (simulating database insert)
    st.session_state.demo_user_data.append(new_record)

# Update resume_upload_page to save data
def save_analysis_data(basic_info, ats_score):
    """Save analysis data when resume is processed"""
    try:
        save_resume_data(basic_info, ats_score)
        st.success("✅ Resume analysis data saved successfully!")
    except Exception as e:
        st.warning(f"⚠️ Could not save analysis data: {str(e)}")

# Run the application
if __name__ == "__main__":
    main()