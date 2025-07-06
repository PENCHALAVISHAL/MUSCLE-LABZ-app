# Fitness Tracker - Production Ready Web Application

A modern, full-stack fitness tracking web application built with Flask and PostgreSQL.

## 🚀 Features

- **User Authentication**: Secure login/registration with password hashing
- **Profile Management**: Store and update personal fitness information
- **Exercise Library**: Comprehensive database of exercises by muscle group
- **Workout Tracking**: Log and track your workouts
- **Weight & Body Composition Tracking**: Monitor your progress
- **Hydration Tracking**: Track daily water intake
- **Responsive Design**: Modern UI that works on all devices
- **Production Ready**: Built for scalability and deployment

## 🛠️ Technology Stack

### Frontend
- **HTML5** with Jinja2 templating
- **CSS3** with modern features (Flexbox, Grid, Backdrop filters)
- **Vanilla JavaScript**
- **Responsive Design** with mobile-first approach

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - ORM for database operations
- **Flask-Login** - User session management
- **Werkzeug** - Password hashing and security

### Database
- **PostgreSQL** (Production) - Robust, scalable database
- **SQLite** (Development) - Local development database

### Deployment Ready
- **Environment Configuration** - Separate dev/prod settings
- **Database Migrations** - Easy schema updates
- **Security Best Practices** - Password hashing, session management

## 📦 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (for production)
- pip

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fitness_webapp
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   flask init-db
   flask populate-exercises
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:8080`

## 🚀 Production Deployment

### Option 1: Heroku

1. **Create Heroku app**
   ```bash
   heroku create your-fitness-tracker
   ```

2. **Add PostgreSQL addon**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

3. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your_super_secret_key_here
   heroku config:set FLASK_ENV=production
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Initialize database**
   ```bash
   heroku run flask init-db
   heroku run flask populate-exercises
   ```

### Option 2: AWS/Google Cloud

1. **Set up PostgreSQL database**
   - AWS RDS or Google Cloud SQL
   - Note the connection string

2. **Configure environment**
   ```bash
   export DATABASE_URL=postgresql://username:password@host:port/database
   export SECRET_KEY=your_super_secret_key_here
   export FLASK_ENV=production
   ```

3. **Deploy with Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

### Option 3: Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
   ```

2. **Build and run**
   ```bash
   docker build -t fitness-tracker .
   docker run -p 8000:8000 fitness-tracker
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
SECRET_KEY=your_super_secret_key_change_this_in_production
FLASK_ENV=production

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/fitness_tracker

# Session Configuration
SESSION_TYPE=filesystem
PERMANENT_SESSION_LIFETIME=3600
```

### Database Configuration

The application supports both SQLite (development) and PostgreSQL (production):

- **Development**: Uses SQLite by default
- **Production**: Set `DATABASE_URL` to PostgreSQL connection string

## 📊 Database Schema

The application includes the following tables:

- **users** - User authentication and profiles
- **user_data** - Personal fitness information
- **workouts** - Exercise tracking and logging
- **exercise_library** - Pre-defined exercise database
- **body_fat_tracking** - Body composition monitoring
- **weight_tracking** - Weight progress tracking
- **hydration_tracking** - Water intake logging
- **hydration_goals** - Daily hydration targets

## 🔒 Security Features

- **Password Hashing**: Uses Werkzeug's secure password hashing
- **Session Management**: Secure session handling with Flask-Login
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CSRF Protection**: Built-in CSRF protection with Flask-WTF
- **Environment Variables**: Sensitive data stored in environment variables

## 🎨 Customization

### Styling
- Modify `static/css/style.css` for custom styling
- Update color variables in CSS `:root` section
- Add custom fonts to `static/fonts/` directory

### Features
- Add new routes in `app.py`
- Create new models in `models.py`
- Add new templates in `templates/` directory

## 📱 Mobile Responsiveness

The application is fully responsive and optimized for:
- Desktop computers
- Tablets
- Mobile phones
- Touch devices

## 🚀 Performance Optimization

- **Database Indexing**: Proper indexes on frequently queried columns
- **Connection Pooling**: Efficient database connection management
- **Static File Caching**: Optimized static file delivery
- **Compression**: Gzip compression for faster loading

## 🔧 Maintenance

### Database Backups
```bash
# PostgreSQL backup
pg_dump your_database > backup.sql

# Restore
psql your_database < backup.sql
```

### Logs
- Application logs are written to stdout/stderr
- Use your deployment platform's logging system
- Consider using a logging service like Loggly or Papertrail

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code comments

---

**Built with ❤️ for fitness enthusiasts everywhere!** 