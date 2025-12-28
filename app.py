from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from translations import TRANSLATIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key' # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mncposte_v4.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Context Processor for Translations
@app.context_processor
def inject_get_text():
    def get_text(key):
        lang = session.get('lang', 'en')
        return TRANSLATIONS.get(lang, TRANSLATIONS['fr']).get(key, key)
    return dict(get_text=get_text)

# Language Route
@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in TRANSLATIONS:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('home'))

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)

class Tracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(100), default="En cours de livraison")
    location = db.Column(db.String(100), default="Pays d'expédition")
    custom_message = db.Column(db.Text, nullable=True)
    weight = db.Column(db.String(20), default="PENDING")
    date_sent = db.Column(db.String(20), default=lambda: datetime.utcnow().strftime('%d/%m/%Y'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Editable History Steps
    step1_label = db.Column(db.String(100), default="Prise en charge")
    step1_date = db.Column(db.String(50), default=lambda: datetime.utcnow().strftime('%d/%m/%Y'))
    step1_loc = db.Column(db.String(100), default="Bureau de poste")
    
    step2_label = db.Column(db.String(100), default="En transit")
    step2_date = db.Column(db.String(50), default="--/--/----")
    step2_loc = db.Column(db.String(100), default="Plateforme logistique")

    step3_label = db.Column(db.String(100), default="Arrivé à Ville d'expédition")
    step3_date = db.Column(db.String(50), default="--/--/----")
    step3_loc = db.Column(db.String(100), default="Centre de tri")

    step4_label = db.Column(db.String(100), default="En cours de livraison")
    step4_date = db.Column(db.String(50), default="--/--/----")
    step4_loc = db.Column(db.String(100), default="Facteur")

    def __repr__(self):
        return f'<Tracking {self.code}>'

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Link to user if logged in
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open') # Open, Closed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    replies = db.relationship('TicketReply', backref='ticket', lazy=True)

class TicketReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('contact_message.id'), nullable=False)
    sender = db.Column(db.String(20), nullable=False) # 'user' or 'admin'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize DB
with app.app_context():
    db.create_all()
    # Create default admin if not exists
    if not User.query.filter_by(username='admin').first():
        new_user = User(username='admin', password='admin', is_admin=True)
        db.session.add(new_user)
        db.session.commit()

# --- Routes ---

# 1. Home Page (Search)
@app.route('/')
def home():
    return render_template('index.html')

# Handle legacy /suivi access (redirect to home)
@app.route('/suivi')
def suivi_legacy():
    return redirect(url_for('home'))

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('dashboard'))
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            login_user(user)
            if user.is_admin:
                return redirect(url_for('dashboard'))
            return redirect(url_for('home'))
        else:
            flash('Identifiant ou mot de passe incorrect.')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Cet identifiant est déjà pris.')
        else:
            user = User(username=username, password=password, is_admin=False)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('home'))
            
    return render_template('register.html')

# Handle Search Post
@app.route('/track', methods=['POST'])
def track_post():
    code = request.form.get('code')
    if code:
        # Normalize to upper case
        code = code.upper().strip()
        
        # Validation: 10 chars, ends with 'M'
        if len(code) != 10 or not code.endswith('M'):
            flash('Numéro de suivi invalide. Le format doit être de 10 caractères et se terminer par "M".', 'error')
            return redirect(url_for('home'))
            
        return redirect(url_for('track_result', code=code))
    return redirect(url_for('home'))

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if name and email and message:
            new_message = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message,
                user_id=current_user.id
            )
            db.session.add(new_message)
            db.session.commit()
            flash('Votre message a bien été envoyé. Nos équipes vous répondront sous 24h.')
            return redirect(url_for('contact'))
        else:
            flash('Veuillez remplir tous les champs obligatoires.')
            
    return render_template('contact.html')

# USER Ticket Management
@app.route('/mes-tickets')
@login_required
def my_tickets():
    tickets = ContactMessage.query.filter_by(user_id=current_user.id).order_by(ContactMessage.timestamp.desc()).all()
    return render_template('my_tickets.html', tickets=tickets)

@app.route('/ticket/<int:id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(id):
    ticket = ContactMessage.query.get_or_404(id)
    
    # Security: Ensure user owns this ticket (or is admin)
    if not current_user.is_admin and ticket.user_id != current_user.id:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        reply_msg = request.form.get('message')
        if reply_msg:
            sender_type = 'admin' if current_user.is_admin else 'user'
            reply = TicketReply(ticket_id=ticket.id, sender=sender_type, message=reply_msg)
            db.session.add(reply)
            
            # If user replies, reopen ticket maybe? status logic can go here
            if sender_type == 'user':
                ticket.status = 'Open'
            
            db.session.commit()
            flash('Réponse envoyée.')
            return redirect(url_for('ticket_detail', id=ticket.id))
            
    return render_template('ticket_detail.html', ticket=ticket)

# 2. Tracking Page (Result)
@app.route('/suivi/<code>')
def track_result(code):
    tracking = Tracking.query.filter_by(code=code).first()
    
    # If not exists, create it with "En attente" as per requirements
    if not tracking:
        tracking = Tracking(code=code)
        db.session.add(tracking)
        db.session.commit()
        
    return render_template('tracking.html', tracking=tracking)

# 4. Admin Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return redirect(url_for('home')) # Protect dashboard
        
    all_tracking = Tracking.query.order_by(Tracking.timestamp.desc()).all()
    return render_template('admin_dashboard.html', tracking_list=all_tracking)

@app.route('/dashboard/tickets')
@login_required
def admin_tickets():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    messages = ContactMessage.query.order_by(ContactMessage.timestamp.desc()).all()
    return render_template('admin_tickets.html', messages=messages)

@app.route('/dashboard/ticket/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_ticket_detail(id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
        
    # Re-use the shared ticket detail view or redirect to the same logic
    # Since ticket_detail handles admin permissions logic already, we can just redirect or use it.
    # However, having a separate route helps URL structure consistency.
    return ticket_detail(id)

# Admin Action: Update
@app.route('/dashboard/update/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    tracking = Tracking.query.get_or_404(id)
    tracking.status = request.form.get('status')
    tracking.location = request.form.get('location')
    tracking.custom_message = request.form.get('custom_message')
    
    # 1. Capture Form Inputs for Labels/Locs (Always update these)
    tracking.step1_label = request.form.get('step1_label')
    tracking.step1_loc = request.form.get('step1_loc')
    
    tracking.step2_label = request.form.get('step2_label')
    tracking.step2_loc = request.form.get('step2_loc')
    
    tracking.step3_label = request.form.get('step3_label')
    tracking.step3_loc = request.form.get('step3_loc')
    
    tracking.step4_label = request.form.get('step4_label')
    tracking.step4_loc = request.form.get('step4_loc')

    # 2. Handle Dates with Slider Logic + Manual Override
    # Start with what's in the form
    d1 = request.form.get('step1_date')
    d2 = request.form.get('step2_date')
    d3 = request.form.get('step3_date')
    d4 = request.form.get('step4_date')
    
    progress_level = request.form.get('progress_level')
    if progress_level is not None:
        level = int(progress_level)
        today = datetime.utcnow().strftime('%d/%m/%Y')
        
        # Helper to set date if empty/default, or clear if level < step
        def resolve_date(current_val, step_num, current_level):
            if step_num <= current_level:
                # Active step: If form val is empty or default, auto-fill today
                if not current_val or current_val == '--/--/----':
                    return today
                return current_val # Keep manual input
            else:
                # Future step: Force clear
                return '--/--/----'

        d1 = resolve_date(d1, 1, level)
        d2 = resolve_date(d2, 2, level)
        d3 = resolve_date(d3, 3, level)
        d4 = resolve_date(d4, 4, level)

    # 3. Assign Final Dates
    tracking.step1_date = d1
    tracking.step2_date = d2
    tracking.step3_date = d3
    tracking.step4_date = d4
    
    db.session.commit()
    flash(f'Mise à jour réussie pour {tracking.code}')
    return redirect(url_for('dashboard'))

# Admin Action: Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home')) # Redirect to home to keep admin hidden

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
