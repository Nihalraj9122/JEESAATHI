from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import numpy as np
import pandas as pd
import os

# AI Model ko server start hote hi memory me load kar lo (Examiner ke liye)
try:
    with open('model.pkl', 'rb') as f:
        ai_data = pickle.load(f)
        josaa_ml_model = ai_data['model']
        cat_encoder = ai_data['cat_encoder']
        quota_encoder = ai_data['quota_encoder']
        print("✅ 100% ASLI Saathi AI Model Loaded!")
except Exception as e:
    print("⚠️ ML Model load nahi hua:", e)


# 1. PEHLE APP BANEGA
app = Flask(__name__)

# 2. PHIR UPLOAD FOLDER KI SETTING HOGI (app banne ke theek baad)
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Secret key session aur error messages (flash) dikhane ke kaam aati hai
app.secret_key = 'tera_koi_bhi_secret_password' 

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# --- DATABASE MODEL ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    # --- NAYA COLUMN PFP KE LIYE ---
    profile_pic = db.Column(db.String(100), default='default.png')


class Mentor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    jee_score = db.Column(db.String(50), nullable=True)
    batch_year = db.Column(db.String(20), nullable=True)
    college = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.String(250), nullable=True)
    
    # --- NAYE COLUMNS ---
    profile_pic = db.Column(db.String(100), default='default_mentor.png') 
    work_status = db.Column(db.String(50), default='Student') # e.g., 'Current Student' or 'Working Professional'
    

class Doubt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Kis bacche ne pucha
    student_name = db.Column(db.String(100), nullable=False)
    mentor_name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    query_text = db.Column(db.Text, nullable=False)
    reply_text = db.Column(db.Text, nullable=True) # Shuru me khali rahega
    status = db.Column(db.String(20), default='Pending') # Pending ya Replied

# Server start hone par database aur table create karega
with app.app_context():
    db.create_all()


# --- ROUTES (Pages) ---

@app.route('/')
def index():
    # Check karega ki user logged in hai ya nahi
    if 'user_id' in session:
        return render_template('index.html', logged_in=True, user_name=session['user_name'])
    return render_template('index.html', logged_in=False)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email'].lower()
        password = request.form['password']

        # Check agar email pehle se database me hai
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists! Please log in.', 'danger')
            return redirect(url_for('signup'))

        # Password ko secure (hash) karna
        hashed_password = generate_password_hash(password)

        # Naya user database me save karna
        new_user = User(fullname=fullname, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


from werkzeug.security import check_password_hash

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email'].lower()
#         password = request.form['password']
        
#         # Naya Role input check (Default student manega agar form me issue hua)
#         role = request.form.get('login_role', 'student') 

#         # ---- STUDENT LOGIN LOGIC ----
#         if role == 'student':
#             user = User.query.filter_by(email=email).first()

#             # Agar user mila AUR password hash match kiya
#             if user and check_password_hash(user.password, password):
#                 session['user_id'] = user.id
#                 session['user_name'] = user.fullname # Tune fullname use kiya hai, which is great
                
#                 # Tune index pe redirect rakha hai. Agar seedhe dashboard bhejna ho toh 'dashboard' kar dena
#                 return redirect(url_for('index')) 
#             else:
#                 flash('Invalid Student email or password. Try again.', 'danger')

#         # ---- MENTOR LOGIN LOGIC ----
#         elif role == 'mentor':
#             mentor = Mentor.query.filter_by(email=email).first()

#             # Note: Agar tune Mentors ka password bhi hash karke save kiya hai, toh yahan bhi 'check_password_hash(mentor.password, password)' use karna. 
#             # Abhi ke liye simple '==' rakha hai assuming manual entry hogi database me.
#             if mentor and mentor.password == password:
#                 session['mentor_id'] = mentor.id
#                 session['mentor_name'] = mentor.name 
#                 return redirect(url_for('mentor_dashboard'))
#             else:
#                 flash('Invalid Mentor credentials. Try again.', 'danger')

#     return render_template('login.html')

# --- 1. STUDENT LOGIN ROUTE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()

        # Agar user mila aur password hash match kiya
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.fullname 
            return redirect(url_for('dashboard')) # Seedha dashboard bhejo
        else:
            flash('Invalid Student email or password. Try again.', 'danger')

    return render_template('login.html')

# --- 2. MENTOR LOGIN ROUTE (NAYA) ---
@app.route('/mentor_login', methods=['GET', 'POST'])
def mentor_login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        
        mentor = Mentor.query.filter_by(email=email).first()

        if mentor and mentor.password == password:
            session['mentor_id'] = mentor.id
            session['mentor_name'] = mentor.name 
            flash(f'Welcome to your workspace, {mentor.name}!', 'success')
            return redirect(url_for('mentor_dashboard'))
        else:
            flash('Invalid Mentor credentials. Try again.', 'danger')

    return render_template('mentor_login.html')




@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    current_user = User.query.get(user_id) 
    
    # --- YE 3 LINE KA NAYA SECURITY CHECK HAI ---
    # Agar session me ID hai par user database me nahi hai, toh logout maro
    if not current_user:
        session.clear()
        flash('Session expired or database reset. Please login again.', 'warning')
        return redirect(url_for('login'))
    # ---------------------------------------------
        
    real_email = current_user.email
    student_doubts = Doubt.query.filter_by(user_id=user_id).order_by(Doubt.id.desc()).all()
    
    return render_template('dashboard.html', 
                           logged_in=True, 
                           user_name=session['user_name'], 
                           user_email=real_email, 
                           current_user=current_user, 
                           doubts=student_doubts)


@app.route('/update_profile_pic', methods=['POST'])
def update_profile_pic():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file.filename != '':
            # Photo ka naam user ki ID se save karenge (e.g., user_1.jpg)
            ext = file.filename.split('.')[-1]
            filename = f"user_{session['user_id']}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save file to folder
            file.save(filepath)
            
            # Update database
            user = User.query.get(session['user_id'])
            user.profile_pic = filename
            db.session.commit()
            flash('Profile picture updated magically!', 'success')
            
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    return redirect(url_for('index'))

@app.route('/predictor')
def predictor_page():
    # Sirf logged in users hi predictor use kar sakte hain
    if 'user_id' in session:
        # YAHAN logged_in=True MISSING THA, ab add kar diya hai!
        return render_template('predictor.html', logged_in=True, user_name=session['user_name'])
    
    flash('Please log in first to use the predictor.', 'danger')
    return redirect(url_for('login'))

@app.route('/resources')
def resources_page():
    if 'user_id' in session:
        return render_template('resources.html', logged_in=True, user_name=session['user_name'])
    return render_template('resources.html', logged_in=False)


#========================================================================




@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # 1. Inputs
    rank = int(request.form['jee_rank'])
    category = request.form['category']
    state = request.form['home_state']
    gender = request.form['gender']
    
    college_type_filter = request.form.get('college_type', 'All')
    state_filter = request.form.get('state_filter', 'All')
    
    master_df = pd.read_csv('complete_data_state.csv')
    real_results = {} 
    
    # 2. Base Category & Gender Ratio
    categories_ratios = {'OPEN': 1.0, 'EWS': 1.3, 'OBC-NCL': 1.5, 'SC': 3.2, 'ST': 4.5}
    gender_modifier = 1.2 if gender == 'Female-Only' else 1.0
    base_ratio = categories_ratios.get(category, 1.0) * gender_modifier
    
    # State Home State Bonus
    STATE_HS_BONUS = {
        'Rajasthan': 1.05, 'Telangana': 1.05, 'Andhra Pradesh': 1.05, 'Uttar Pradesh': 1.1, 'Bihar': 1.1, 'Delhi': 1.1,
        'Jharkhand': 1.25, 'Madhya Pradesh': 1.2, 'Maharashtra': 1.2, 'West Bengal': 1.2, 'Karnataka': 1.15, 'Tamil Nadu': 1.15, 'Odisha': 1.2, 'Chhattisgarh': 1.25,
        'Mizoram': 2.0, 'Nagaland': 2.0, 'Manipur': 2.0, 'Arunachal Pradesh': 2.0, 'Sikkim': 2.0, 'Tripura': 1.8, 'Meghalaya': 1.8, 'Assam': 1.5,
        'Jammu & Kashmir': 1.6, 'Himachal Pradesh': 1.4, 'Uttarakhand': 1.3, 'Goa': 1.5
    }
    
    # 3. Core Logic Loop
    for index, row in master_df.iterrows():
        c_name = row['College_Name']
        branch = row['Branch']
        csv_quota = row['Quota'] 
        base_closing = int(row['Closing_Rank'])
        
        # Filter 1: College Type
        if 'NIT' in c_name or 'IIEST' in c_name:
            c_type = 'NIT'
        elif 'IIIT' in c_name:
            c_type = 'IIIT'
        else:
            c_type = 'GFTI'
            
        if college_type_filter != 'All' and c_type != college_type_filter:
            continue
            
        college_home_state = row['State'] 
        is_home_state_match = (college_home_state == state)
        
        if state_filter == 'Home State Only' and not is_home_state_match:
            continue
            
        final_ratio = base_ratio
        
        if is_home_state_match:
            if csv_quota == 'OS':
                state_specific_bonus = STATE_HS_BONUS.get(college_home_state, 1.2)
                final_ratio = base_ratio * state_specific_bonus 
        else:
            if csv_quota == 'HS':
                continue

        predicted_cutoff = int(base_closing * final_ratio)
        
        # 🔥 THE REAL ML PROBABILITY CALCULATION 🔥
        rank_ratio = rank / max(1, predicted_cutoff)
        
        try:
            encoded_cat = cat_encoder.transform([category])[0]
            safe_quota = csv_quota if csv_quota in quota_encoder.classes_ else 'OS'
            encoded_quota = quota_encoder.transform([safe_quota])[0]
            
            probabilities = josaa_ml_model.predict_proba([[encoded_cat, encoded_quota, rank_ratio]])[0]
            chance = int(probabilities[1] * 100)
            
        except Exception as e:
            base_margin = (predicted_cutoff - rank) / max(1, predicted_cutoff)
            chance = max(1, min(99, int(82 + base_margin * 45)))        # Sirf tabhi display karenge jab admission ka chance kam se kam 50% ho

        # 🚨 THE REALITY CHECK FIX (Reviewer ka Steep Decay Algorithm) 🚨
        rank_diff = rank - predicted_cutoff

        if rank_diff > 0: 
            # Agar bacche ki rank cutoff se kharab hai (Deficit)
            if rank_diff <= 2000:
                # 0 se 2000 ka gap: Chance 60% - 75% ke beech limit karo
                chance = min(chance, 75 - int((rank_diff / 2000) * 15)) 
            elif rank_diff <= 5000:
                # 2000 se 5000 ka gap: Chance seedha 30% - 50% par gira do
                chance = min(chance, 50 - int(((rank_diff - 2000) / 3000) * 20))
            else:
                # 5000 se bada gap: No chance (Miracle round only)
                chance = 10 
        else:
            # Safe zone: Agar rank cutoff se acchi hai, toh chance ko 85% se 99% ke beech strong rakho
            chance = max(85, min(99, chance))


       # Sirf tabhi display karenge jab admission ka chance kam se kam 20% ho
        if chance >= 20:
            if chance >= 85:
                status, color = "High Chance", "success"
            elif chance >= 70:
                status, color = "Good Chance", "primary"
            elif chance >= 50:
                status, color = "Borderline", "warning"
            else:
                status, color = "Tough Chance", "danger"
            
            # 🔥 YEH LINE MISSING THI YA GALAT INDENT THI 🔥
            unique_key = f"{c_name}_{branch}"
            
            data_payload = {
                'name': c_name,
                'branch': branch,
                'closing_rank': predicted_cutoff,
                'status': status,
                'color': color,
                'chance': chance,
                'is_home_state': is_home_state_match, 
                'type': c_type
            }
            
            if unique_key not in real_results or chance > real_results[unique_key]['chance']:
                real_results[unique_key] = data_payload

    # 4. Final Sorting
    final_list = list(real_results.values())
    final_list = sorted(final_list, key=lambda x: (-x['chance'], x['type'] != 'NIT', not x['is_home_state'], x['closing_rank']))[:12]
    
    current_user = session.get('user_name', 'Student')
    
    return render_template('results.html', 
                            logged_in=True,
                            user_name=current_user,
                            user_rank=rank,
                            user_category=category,
                            user_state=state,
                            user_gender=gender,
                            predicted_colleges=final_list,
                            selected_type=college_type_filter,
                            selected_state_filter=state_filter)

#=============================================================================


@app.route('/mentorship')
def mentorship_page():
    # DATABASE SE SAARE ACTIVE MENTORS NIKAALO
    active_mentors = Mentor.query.all()
    
    if 'user_id' in session:
        return render_template('mentorship.html', 
                               logged_in=True, 
                               user_name=session['user_name'],
                               mentors=active_mentors) # Yahan mentors pass kar diye
                               
    return render_template('mentorship.html', 
                           logged_in=False, 
                           mentors=active_mentors)


@app.route('/submit_doubt', methods=['POST'])
def submit_doubt():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Form se data nikalna
    mentor = request.form.get('mentor_choice')
    subject = request.form.get('subject')
    query = request.form.get('query_text')
    
    # Database me save karna
    new_doubt = Doubt(
        user_id=session['user_id'],
        student_name=session['user_name'],
        mentor_name=mentor,
        subject=subject,
        query_text=query
    )
    db.session.add(new_doubt)
    db.session.commit()
    
    flash('Bhai tera doubt portal par submit ho gaya hai! Dashboard par reply check karte rehna.', 'success')
    return redirect(url_for('dashboard')) # Seedhe dashboard par bhejo taaki status dikhe


# --- ADMIN DASHBOARD ROUTE ---
# --- 1. ADMIN LOGIN PAGE ---
# --- 1. ADMIN LOGIN PAGE ---
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 🔥 SECURE ADMIN LOGIN (Password ab Render se aayega) 🔥
        real_admin_pass = os.environ.get("ADMIN_PASSWORD")
        
        # Agar local laptop pe test kar raha hai, toh ye default password chalega
        if not real_admin_pass:
            real_admin_pass = "admin123"

        if username == 'nihalraj' and password == real_admin_pass:
            session['is_admin'] = True  
            flash('Welcome Mentor! You are logged in.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid Admin Credentials!', 'danger')
            
    return render_template('admin_login.html')
# --- 2. ADMIN LOGOUT ---

@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin', None) # Admin session delete kar diya
    flash('Admin Logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

# --- UPGRADED SECURE SUPER ADMIN DASHBOARD SYSTEM CONTROL ---
@app.route('/admin')
def admin_dashboard():
    # Security Validation Check
    if not session.get('is_admin'):
        flash('Access Denied! Management authorization credentials required.', 'danger')
        return redirect(url_for('admin_login'))
        
    # 1. Fetching all Metrics for Top Grid Layout Counters
    students_count = User.query.count()
    mentors_count = Mentor.query.count()
    pending_count = Doubt.query.filter_by(status='Pending').count()
    resolved_count = Doubt.query.filter_by(status='Resolved').count() + Doubt.query.filter_by(status='Replied').count()
    
    # 2. Extracting Lists for the Tab Panels
    all_doubts_list = Doubt.query.order_by(Doubt.id.desc()).all()
    all_mentors_list = Mentor.query.all()
    all_students_list = User.query.all()
    
    return render_template('admin_dashboard.html', 
                           total_students=students_count,
                           total_mentors=mentors_count,
                           pending_count=pending_count,
                           resolved_count=resolved_count,
                           doubts=all_doubts_list,
                           mentors_list=all_mentors_list,
                           students_list=all_students_list)

# --- SUPER ADMIN ACTION: INTERVENTION OVERRIDE REPLY ---
@app.route('/admin_reply', methods=['POST'])
def admin_reply():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
        
    doubt_id = request.form.get('doubt_id')
    reply_msg = request.form.get('reply_msg')
    
    doubt = Doubt.query.get(doubt_id)
    if doubt:
        doubt.reply_text = reply_msg
        doubt.status = 'Resolved'
        db.session.commit()
        flash('Super Admin override resolution reply pushed successfully!', 'success')
        
    return redirect(url_for('admin_dashboard'))

# --- SUPER ADMIN ACTION: ONBOARD MENTOR DIRECTLY FROM CARD ---
@app.route('/admin_add_mentor', methods=['POST'])
def admin_add_mentor():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
        
    m_name = request.form.get('mentor_name')
    m_email = request.form.get('mentor_email').lower()
    m_pass = request.form.get('mentor_password')
    m_score = request.form.get('mentor_score')
    m_year = request.form.get('mentor_year')
    m_college = request.form.get('mentor_college')
    m_bio = request.form.get('mentor_bio')
    m_status = request.form.get('work_status') # Naya field
    
    # PHOTO UPLOAD LOGIC
    pic_filename = 'default_mentor.png'
    if 'mentor_pic' in request.files:
        file = request.files['mentor_pic']
        if file.filename != '':
            # Unique filename (e.g., mentor_rahul.jpg)
            pic_filename = f"mentor_{m_email.split('@')[0]}.{file.filename.split('.')[-1]}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_filename))

    existing = Mentor.query.filter_by(email=m_email).first()
    if existing:
        flash('Mentor already exists!', 'danger')
    else:
        new_mentor = Mentor(name=m_name, email=m_email, password=m_pass, 
                            jee_score=m_score, batch_year=m_year, 
                            college=m_college, bio=m_bio,
                            work_status=m_status, profile_pic=pic_filename) # Sab save kar diya
        db.session.add(new_mentor)
        db.session.commit()
        flash(f'Mentor {m_name} added successfully!', 'success')
        
    return redirect(url_for('admin_dashboard'))


# --- SUPER ADMIN ACTION: PERMANENT TERMINATION BAN/DELETE STUDENT USER ---
@app.route('/admin_delete_student/<int:id>', methods=['POST'])
def admin_delete_student(id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
        
    student = User.query.get(id)
    if student:
        # Also clean up doubts raised by student to maintain relational integrity
        Doubt.query.filter_by(user_id=id).delete()
        db.session.delete(student)
        db.session.commit()
        flash('Student security profile account terminated from central index registry.', 'success')
        
    return redirect(url_for('admin_dashboard'))

# --- SUPER ADMIN ACTION: OFFBOARD/DELETE MENTOR PROFILE ACCOUNT ---
@app.route('/admin_delete_mentor/<int:id>', methods=['POST'])
def admin_delete_mentor(id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
        
    mentor = Mentor.query.get(id)
    if mentor:
        db.session.delete(mentor)
        db.session.commit()
        flash('Mentor security clearance profile offboarded from system database directory.', 'success')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/mentor_dashboard')
def mentor_dashboard():
    if 'mentor_id' not in session:
        flash('Please log in as a mentor first.', 'danger')
        return redirect(url_for('login'))
        
    m_name = session['mentor_name']
    
    # MAGIC QUERY: Sirf is mentor ke liye bheje gaye doubts YA jo sabke liye ('Anyone') hain
    my_doubts = Doubt.query.filter(
        (Doubt.mentor_name == m_name) | (Doubt.mentor_name == 'Anyone')
    ).order_by(Doubt.id.desc()).all()
    
    return render_template('mentor_dashboard.html', doubts=my_doubts, mentor_name=m_name)
# MENTOR REPLY SUBMISSION
@app.route('/mentor_reply', methods=['POST'])
def mentor_reply():
    if 'mentor_id' not in session:
        return redirect(url_for('login'))
        
    doubt_id = request.form.get('doubt_id')
    reply_msg = request.form.get('reply_msg')
    
    doubt = Doubt.query.get(doubt_id)
    if doubt:
        doubt.reply_text = reply_msg
        doubt.status = 'Resolved' # Ya 'Replied', jo tune dashboard HTML me conditions rakhi hain
        db.session.commit()
        flash('Solution sent to the student successfully!', 'success')
        
    return redirect(url_for('mentor_dashboard'))


# --- TEMPORARY ROUTE TO ADD MENTORS ---
@app.route('/add_mentors')
def add_mentors():
    # Pehle check karte hain ki kahin already mentors added toh nahi hain
    if Mentor.query.first():
        return "Mentors are already in the database! Go to /login"
    
    # 2 Naye mentors banate hain
    mentor1 = Mentor(name='Rahul Sharma', email='rahul@jeesaathi.com', password='rahul')
    mentor2 = Mentor(name='Aman Singh', email='aman@jeesaathi.com', password='aman')
    
    # Database me save kar dete hain
    db.session.add(mentor1)
    db.session.add(mentor2)
    db.session.commit()
    
    return "Mentors added successfully! Ab login page par ja kar test kar."

@app.route('/about')
def about_page():
    if 'user_id' in session:
        return render_template('about.html', logged_in=True, user_name=session['user_name'])
    return render_template('about.html', logged_in=False)


from flask import jsonify, request
from groq import Groq  
import os

# 1. Pehle code try karega live server (Render) ki settings se key lene ki
groq_api_key = os.environ.get("GROQ_API_KEY")

# 2. Agar wahan nahi mili, toh exact usi folder me dhoondhega jahan app.py hai
if not groq_api_key:
    # 🔥 YEH HAI NAYA JADOO: Exact folder ka rasta nikalna 🔥
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(BASE_DIR, "secret_key.txt")
    
    try:
        with open(key_path, "r") as f:
            groq_api_key = f.read().strip()
    except FileNotFoundError:
        print(f"\n⚠️ ERROR BHAI: Mujhe is exact jagah par file nahi mili -> {key_path}\n")
        groq_api_key = None

if groq_api_key:
    client = Groq(api_key=groq_api_key)
else:
    print("⚠️ WARNING: API Key nahi mili! Server par set karo ya secret_key.txt banao.")
    client = None

@app.route("/ai-query", methods=["POST"])
def ai_query():
    data = request.get_json()
    chat_history = data.get("history", []) 

    system_prompt = (
        "You are 'Saathi AI', a smart, sensible, and supportive elder brother mentor for the 'JEE Saathi' platform. "
        "TONE RULES: Speak in natural Indian Hinglish. Address the user as 'Bhai' or 'Dost'. Strictly NO 'Beta', NO robotic/pure Hindi. Keep answers short, crisp, and directly to the point. "
        "--- CORE BEHAVIOR (HOW TO ANSWER) --- "
        "1. GENERAL KNOWLEDGE & STUDY HELP: If the user asks about physics, chemistry, maths, time tables, study strategies, or motivation, YOU MUST ANSWER directly with smart, practical elder-brotherly advice or solutions. Do NOT ask 'kya help chahiye', just give the help! "
        "2. PREDICTOR LINK TRIGGER: If the user explicitly asks for college prediction, says 'prediction karna hai', 'predictor link', or 'best college', reply with this EXACT HTML line: "
        "<br><br>🎯 <b><a href='/predictor' style='color:#185adb; text-decoration:underline;'>Click Here to open College Predictor</a></b> "
        "3. WEBSITE BUGS & UNSOLVABLE TECH ISSUES: If the user reports a core website crash, database error, or asks something you cannot do as an AI, ask them: "
        "'<br><br>Bhai, ye technical dikkat mere control me nahi hai. Kya tum developer/admin (Nihal Raj) se contact karna chahte ho?' "
        "4. SHARED CONTACT TRIGGER: ONLY if the user explicitly says 'yes', 'haan', 'contact do', 'admin se baat karni hai', or 'Nihal se baat karni hai', THEN output this EXACT HTML: "
        "<br><br>👉 <b>Reach out to Admin (Nihal Raj):</b> <br>💼 <a href='https://in.linkedin.com/in/nihal-raj9122' target='_blank' style='color:#0077b5;'>LinkedIn</a> <br>📧 <a href='mailto:rvnihal9122@gmail.com' style='color:#ea4335;'>Email</a> "
        "5. NO SPAM: Never share admin links or ask about the admin for normal study/physics/chemistry questions."
    )

    try:
        if not client:
            return jsonify({"response": "Bhai, server par AI ki API Key set nahi hai. Admin ko bol set karne!"})

        messages_for_ai = [{"role": "system", "content": system_prompt}]
        
        for msg in chat_history:
            messages_for_ai.append(msg)

        chat_completion = client.chat.completions.create(
            messages=messages_for_ai,
            model="llama-3.3-70b-versatile",
        )

        return jsonify({"response": chat_completion.choices[0].message.content})

    except Exception as e:
        print("AI ERROR BHAI:", e)
        return jsonify(
            {
                "response": "Bhai abhi network issue hai, thodi der baad try kar!"
            }
        )
if __name__ == '__main__':
    app.run(debug=True)
