# 🎉 TN Events — Tamil Nadu Event Services Platform

> A full-stack multi-server web application for booking event services across Tamil Nadu — including wedding halls, catering, luxury cars, photography, and decorations.

---

## 📌 Table of Contents

1. [Project Overview](#-project-overview)
2. [Tech Stack](#-tech-stack)
3. [Architecture](#-architecture)
4. [Database Schema](#-database-schema)
5. [Features by Role](#-features-by-role)
6. [API Reference](#-api-reference)
7. [Project Structure](#-project-structure)
8. [How to Run](#-how-to-run)
9. [Environment Variables](#-environment-variables)
10. [Default Credentials](#-default-credentials)
11. [Limitations](#-known-limitations)
12. [Future Enhancements](#-future-enhancements)

---

## 🌐 Project Overview

**TN Events** is a city-wise event service booking platform built specifically for Tamil Nadu. It allows:

- **Users** to browse and book halls, catering, luxury cars, photography, and decoration services across TN cities.
- **Vendors** to list and manage their services, view incoming orders, and update booking statuses.
- **Admins** to oversee the entire platform — approving vendors, managing services, and monitoring all bookings.

The backend is split into **three independent Flask servers**, each serving both API routes and frontend static HTML pages — no separate frontend framework needed.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend Framework** | Python 3.x + Flask 3.0.3 |
| **Database** | MySQL (via `mysql-connector-python 8.4.0`) |
| **Authentication** | Flask Sessions + bcrypt password hashing |
| **PDF Generation** | ReportLab |
| **File Uploads** | Werkzeug `secure_filename` |
| **Environment Config** | `python-dotenv` |
| **Frontend** | Vanilla HTML5 + CSS3 + JavaScript (served as Flask static files) |
| **Session Management** | Flask-Session 0.8.0 (cookie-based, 31-day persistence) |

---

## 🏗 Architecture

The project uses a **multi-server microservice-style architecture** with three Flask apps running on separate ports:

```
┌────────────────────────────────────────────────────────┐
│                      MySQL Database                    │
│                     (tn_events DB)                     │
└───────────┬──────────────┬───────────────┬─────────────┘
            │              │               │
     ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
     │ server_user │ │server_vendor│ │server_admin│
     │  Port 3000  │ │  Port 3001  │ │  Port 3002  │
     │             │ │             │ │             │
     │ - Browse    │ │ - Add/Edit  │ │ - Approve   │
     │ - Book      │ │   Services  │ │   Vendors   │
     │ - My Orders │ │ - View      │ │ - Manage    │
     │ - Invoice   │ │   Orders    │ │   All Data  │
     └─────────────┘ └─────────────┘ └─────────────┘
```

Each server:
- Has its own Flask app with isolated session cookies
- Serves its own frontend HTML files from a `static/` folder
- Shares the same MySQL database via the common `db.py` helper

---

## 🗄 Database Schema

Database name: `tn_events` (UTF-8 `utf8mb4_unicode_ci`)

### `users`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK AI | Primary key |
| name | VARCHAR(100) | Full name |
| email | VARCHAR(100) UNIQUE | Login email |
| phone | VARCHAR(15) | Contact number |
| password_hash | VARCHAR(255) | bcrypt hashed password |
| role | ENUM('user','vendor','admin') | User role |
| vendor_service_type | ENUM('hall','catering','luxury_car','decoration','photography') | Vendor's designated service |
| status | ENUM('active','inactive','pending') | Account status |
| created_at | DATETIME | Registration timestamp |

### `halls`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK AI | Primary key |
| name | VARCHAR(100) | Hall name |
| city | VARCHAR(100) | City in Tamil Nadu |
| capacity | INT | Max guest capacity |
| amenities | TEXT | Comma-separated amenities |
| price_per_night | DECIMAL(10,2) | Booking price |
| address | LONGTEXT | Full address |
| latitude / longitude | DECIMAL(10,8) | Map coordinates |
| image_url | VARCHAR(255) | Hall image path |
| location_url | VARCHAR(255) | Google Maps link |
| status | ENUM('pending','approved','rejected') | Admin approval status |
| vendor_id | INT FK → users | Owning vendor |

### `catering_companies`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK AI | Primary key |
| user_id | INT FK → users | Owning vendor |
| company_name | VARCHAR(100) | Company name |
| city | VARCHAR(100) | Operating city |
| veg_non_veg | ENUM('veg','non_veg','both') | Menu type |
| price_per_plate | DECIMAL(10,2) | Per-plate cost |
| status | ENUM | Admin approval status |

### `catering_menu`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK AI | Primary key |
| catering_id | INT FK → catering_companies | Parent company |
| dish_name | VARCHAR(100) | Dish name |
| category | ENUM('main','side','snack','beverage','ice_cream') | Dish type |
| price_per_item | DECIMAL(10,2) | Individual item price |

### `luxury_cars`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK AI | Primary key |
| user_id | INT FK → users | Owning vendor |
| car_name | VARCHAR(100) | Brand (e.g. BMW) |
| car_model | VARCHAR(100) | Model (e.g. 7-Series) |
| city | VARCHAR(100) | Available city |
| image_url | VARCHAR(255) | Car image path |
| rate_per_km | DECIMAL(10,2) | Per-km rate |
| per_day_rent | DECIMAL(10,2) | Daily rental rate |
| per_hour_rent | DECIMAL(10,2) | Hourly rental rate |
| km_limit | INT | KM limit per booking |
| capacity | INT | Passenger capacity |
| with_decorations | BOOLEAN | Wedding decoration available |
| status | ENUM | Admin approval status |

### `photography_services`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK AI | Primary key |
| user_id | INT FK → users | Owning vendor |
| city | VARCHAR(100) | Operating city |
| service_name | VARCHAR(100) | Studio/service name |
| base_price | DECIMAL(10,2) | Starting price |
| price_per_hour | DECIMAL(10,2) | Hourly rate |
| status | ENUM | Admin approval status |

### `decorations`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK AI | Primary key |
| user_id | INT FK → users | Owning vendor |
| theme_name | VARCHAR(100) | Theme name |
| religion_style | VARCHAR(50) | Hindu / Christian / Muslim |
| culture_style | VARCHAR(50) | Tamil / Western / Traditional |
| base_price | DECIMAL(10,2) | Base price |
| city | VARCHAR(100) | Operating city |
| status | ENUM | Admin approval status |

### `bookings`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK AI | Primary key |
| user_id | INT FK → users | Customer who booked |
| service_type | ENUM('hall','catering','luxury_car','photography','decorations') | Type of service |
| service_id | INT | ID in the respective service table |
| date | DATE | Event date |
| time | TIME | Event time |
| total_people | INT | Guest count |
| total_amount | DECIMAL(10,2) | Total cost |
| advance_amount | DECIMAL(10,2) | Advance paid |
| status | ENUM('pending','confirmed','completed','cancelled') | Booking status |
| notes | TEXT | Special requests |
| created_at | DATETIME | Booking timestamp |

### `vendor_approvals`
| Column | Type | Description |
|--------|------|-------------|
| id | INT PK AI | Primary key |
| vendor_id | INT | Vendor being reviewed |
| approved_by_admin_id | INT | Admin who acted |
| approved_at | DATETIME | Action timestamp |
| status | ENUM('approved','rejected','pending') | Decision |

---

## 👥 Features by Role

### 🧑 User (Port 3000)

| Feature | Details |
|---------|---------|
| **Register / Login** | Email + bcrypt password, 31-day persistent session |
| **Browse Halls** | Filter by city, capacity, max price |
| **Browse Catering** | Filter by city and veg/non-veg type |
| **Browse Luxury Cars** | Filter by city and decoration availability |
| **Browse Photography** | Filter by city |
| **Browse Decorations** | Filter by city, religion/culture style |
| **Hall Detail View** | Full details with map link, vendor contact |
| **Service Availability Calendar** | See booked dates before booking |
| **Create Booking** | Book any service with date, time, guests, notes |
| **View My Bookings** | All bookings with status and service name |
| **Cancel Booking** | Cancel pending bookings; confirmed bookings flagged as no-refund |
| **Download Invoice (PDF)** | PDF invoice generated with ReportLab |
| **Change Password** | Update account password |

### 🏪 Vendor (Port 3001)

| Feature | Details |
|---------|---------|
| **Register / Login** | Separate vendor session |
| **Add Services** | Add halls / catering / cars / photography / decoration (one type per vendor) |
| **Edit Services** | Update name, pricing, city, image, location |
| **Delete Services** | Remove own listings |
| **Image Upload** | Upload service images (stored in `server_user/static/uploads/`) |
| **View Orders** | All bookings for own services, with customer info |
| **Filter Orders** | Filter by booking status |
| **Update Order Status** | Mark as confirmed / completed / cancelled |
| **Analytics Dashboard** | Bookings by status, over 30 days, by service type |
| **Update Pricing** | Quick-update price field on any service |

### 🔐 Admin (Port 3002)

| Feature | Details |
|---------|---------|
| **Admin Login** | Separate admin session cookie |
| **Vendor Management** | List all vendors, approve or reject them |
| **User Management** | View all registered users |
| **All Bookings** | View all platform bookings (latest 200) |
| **Full CRUD – Halls** | Create, read, update, delete any hall |
| **Full CRUD – Catering** | Full management of catering companies |
| **Full CRUD – Cars** | Full management of luxury cars |
| **Full CRUD – Photography** | Full management of photography services |
| **Full CRUD – Decorations** | Full management of decoration themes |
| **Approve / Reject Services** | Toggle service status (pending → approved/rejected) |

---

## 📡 API Reference

### User Server (`:3000/api`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register new user |
| POST | `/api/login` | User login |
| GET | `/api/logout` | Logout and redirect |
| GET | `/api/me` | Get current user info |
| POST | `/api/change-password` | Change password |
| GET | `/api/halls` | List halls (filters: city, capacity, max_price) |
| GET | `/api/halls/:id` | Hall detail |
| GET | `/api/catering` | List catering (filters: city, type) |
| GET | `/api/catering/:id` | Catering detail + menu |
| GET | `/api/cars` | List luxury cars (filters: city, decorated) |
| GET | `/api/photography` | List photography (filter: city) |
| GET | `/api/decorations` | List decorations (filters: city, style) |
| GET | `/api/cities` | Distinct cities from halls |
| GET | `/api/services/detail` | Generic service detail (?type=&id=) |
| GET | `/api/services/availability` | Booked dates for a service |
| POST | `/api/bookings` | Create a booking |
| GET | `/api/bookings` | Get my bookings |
| GET | `/api/bookings/:id` | Get single booking |
| POST | `/api/bookings/:id/cancel` | Cancel a booking |
| POST | `/api/bookings/:id/pay` | Mark payment done |
| GET | `/api/bookings/:id/invoice` | Download PDF invoice |
| POST | `/api/payment` | Simulated payment endpoint |

### Vendor Server (`:3001/api`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Vendor login |
| GET | `/api/vendor/services` | My services |
| GET | `/api/vendor/orders` | My orders (filter: status) |
| PUT | `/api/vendor/orders/:id/status` | Update order status |
| GET | `/api/vendor/analytics` | Booking analytics |
| POST | `/api/vendor/hall` | Add hall (multipart form) |
| PUT | `/api/vendor/hall/:id` | Update hall |
| DELETE | `/api/vendor/hall/:id` | Delete hall |
| POST | `/api/vendor/catering` | Add catering |
| PUT | `/api/vendor/catering/:id` | Update catering |
| DELETE | `/api/vendor/catering/:id` | Delete catering |
| POST | `/api/vendor/luxury_car` | Add car |
| PUT | `/api/vendor/luxury_car/:id` | Update car |
| DELETE | `/api/vendor/luxury_car/:id` | Delete car |
| POST | `/api/vendor/photography` | Add photography |
| PUT | `/api/vendor/photography/:id` | Update photography |
| DELETE | `/api/vendor/photography/:id` | Delete photography |
| POST | `/api/vendor/decoration` | Add decoration |
| PUT | `/api/vendor/decoration/:id` | Update decoration |
| DELETE | `/api/vendor/decoration/:id` | Delete decoration |
| PUT | `/api/vendor/services/:type/:id/price` | Quick-update price |

### Admin Server (`:3002/api`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Admin login |
| GET | `/api/admin/vendors` | List all vendors |
| POST | `/api/admin/vendors/:id/approve` | Approve vendor |
| POST | `/api/admin/vendors/:id/reject` | Reject vendor |
| DELETE | `/api/admin/vendors/:id` | Delete vendor |
| GET | `/api/admin/users` | List all users |
| GET | `/api/admin/bookings` | All platform bookings |
| GET/POST | `/api/admin/halls` | List / Add halls |
| PUT/DELETE | `/api/admin/halls/:id` | Update / Delete hall |
| GET/POST | `/api/admin/catering` | List / Add catering |
| PUT/DELETE | `/api/admin/catering/:id` | Update / Delete catering |
| GET/POST | `/api/admin/cars` | List / Add cars |
| PUT/DELETE | `/api/admin/cars/:id` | Update / Delete car |
| GET/POST | `/api/admin/photography` | List / Add photography |
| PUT/DELETE | `/api/admin/photography/:id` | Update / Delete photography |
| GET/POST | `/api/admin/decorations` | List / Add decorations |
| PUT/DELETE | `/api/admin/decorations/:id` | Update / Delete decoration |
| PUT | `/api/admin/:stype/:id/status` | Approve/reject any service |

---

## 📁 Project Structure

```
tn_events_backend/
│
├── .env                        # Environment variables (not committed)
├── .gitignore                  # Git ignore rules
├── db.py                       # Shared MySQL connection helper
├── init_db.py                  # Database initializer + data seeder
├── requirements.txt            # Python dependencies
├── start_all.bat               # Windows: start all 3 servers
├── start_all.sh                # Linux/Mac: start all 3 servers
│
├── migrate_service_type.py     # DB migration: add service_type column
├── migrate_status.py           # DB migration: add status column
├── migrate_v2.py               # DB migration: v2 schema changes
├── update_bookings_schema.py   # DB migration: bookings schema update
├── update_status.py            # DB migration: status field update
│
├── server_user/                # User portal (Port 3000)
│   ├── app.py                  # Flask app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # Register, login, logout, /me, change-password
│   │   ├── booking.py          # Create, view, cancel, pay, invoice bookings
│   │   └── services.py         # Browse halls, catering, cars, photography, decorations
│   └── static/
│       ├── index.html          # Home page
│       ├── login.html          # Login page
│       ├── register.html       # Registration page
│       ├── halls.html          # Hall listing
│       ├── hall-detail.html    # Hall detail page
│       ├── catering.html       # Catering listing
│       ├── cars.html           # Luxury cars listing
│       ├── photography.html    # Photography listing
│       ├── decorations.html    # Decorations listing
│       ├── booking.html        # Booking form
│       ├── booking-success.html# Booking confirmation page
│       ├── my-orders.html      # User's booking history
│       ├── common.js           # Shared JS utilities
│       ├── style.css           # Global styles
│       ├── login-bg.png        # Login background image
│       └── uploads/            # User-uploaded service images
│
├── server_vendor/              # Vendor portal (Port 3001)
│   ├── app.py                  # Flask app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # Vendor login/logout/me
│   │   └── dashboard.py        # Services CRUD, orders, analytics, price updates
│   └── static/
│       ├── index.html          # Vendor dashboard
│       ├── login.html          # Vendor login
│       ├── register.html       # Vendor registration
│       ├── services.html       # Service management
│       ├── orders.html         # Order management
│       ├── common.js           # Shared JS
│       └── style.css           # Vendor portal styles
│
└── server_admin/               # Admin portal (Port 3002)
    ├── app.py                  # Flask app entry point
    ├── routes/
    │   ├── __init__.py
    │   ├── auth.py             # Admin login/logout
    │   ├── manage_vendors.py   # Vendor approval, user management, bookings
    │   └── manage_services.py  # Full CRUD for all 5 service types + status updates
    └── static/
        ├── index.html          # Admin dashboard
        ├── login.html          # Admin login
        ├── vendors.html        # Vendor management
        ├── users.html          # User management
        ├── bookings.html       # All bookings view
        ├── halls.html          # Hall management
        ├── catering.html       # Catering management
        ├── cars.html           # Car management
        ├── photography.html    # Photography management
        ├── decorations.html    # Decoration management
        ├── common.js           # Shared JS
        └── style.css           # Admin portal styles
```

---

## 🚀 How to Run

### Prerequisites

- Python 3.9+
- MySQL 8.0+
- Git
- Windows (for `.bat` script) or Linux/Mac (for `.sh` script)

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/jainularsath/final-year.git
cd final-year
```

---

### Step 2 — Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The invoice feature requires `reportlab`. If not in requirements.txt, install it separately:
> ```bash
> pip install reportlab
> ```

---

### Step 4 — Configure Environment Variables

Create a `.env` file in the root directory:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=tn_events
SECRET_KEY=your_super_secret_key
ADMIN_DEFAULT_PASSWORD=Admin@TN2024!
```

---

### Step 5 — Initialize the Database

```bash
python init_db.py
```

This will:
- Create the `tn_events` database and all tables
- Seed a default **admin** account
- Seed a sample **vendor** with halls, catering, cars, photography, and decoration data

---

### Step 6 — Start All Servers

**Windows (recommended):**
```bat
start_all.bat
```

**Manual (any OS):**
```bash
# Terminal 1 - User Server
cd server_user
python app.py

# Terminal 2 - Vendor Server
cd server_vendor
python app.py

# Terminal 3 - Admin Server
cd server_admin
python app.py
```

---

### Step 7 — Open in Browser

| Portal | URL |
|--------|-----|
| 🧑 User Portal | http://localhost:3000 |
| 🏪 Vendor Portal | http://localhost:3001 |
| 🔐 Admin Portal | http://localhost:3002 |

---

## 🔑 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | MySQL host |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | `21Ucs017` | MySQL password |
| `DB_NAME` | `tn_events` | Database name |
| `SECRET_KEY` | `user_secret_2024` | Flask session secret |
| `ADMIN_DEFAULT_PASSWORD` | `Admin@TN2024!` | Default admin password |

> ⚠️ **Never commit your `.env` file.** It is already excluded by `.gitignore`.

---

## 🔐 Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tnevents.com | Admin@TN2024! |
| Sample Vendor | vendor@tnevents.com | Vendor@123 |

> These are created by `init_db.py`. Change them after first login.

---

## ⚠️ Known Limitations

1. **Simulated Payment** — The payment system is not integrated with a real payment gateway. Payments are simulated and bookings are marked as `pending` after "payment".

2. **Single Service Type per Vendor** — Each vendor account is locked to one service type (hall, catering, etc.) at registration. Switching service type requires admin intervention.

3. **No Email Notifications** — There is no email or SMS notification system. Users and vendors must log in to check booking status changes.

4. **No Real-Time Updates** — The platform does not use WebSockets or push notifications. Status updates are visible only on page refresh.

5. **Session-Based Auth Only** — Authentication uses server-side Flask sessions with cookies. No JWT or token-based auth, which limits API usage from mobile clients.

6. **No Pagination** — The admin bookings list fetches at most 200 records. Large datasets may cause slowdowns.

7. **No Multi-Image Support** — Each service listing supports only one image upload.

8. **Local File Storage** — Uploaded images are stored on the local filesystem (`server_user/static/uploads/`). Not suitable for distributed/cloud deployments without modification.

9. **No HTTPS** — Runs on HTTP by default. For production, configure a reverse proxy (Nginx/Apache) with SSL.

10. **Hardcoded Localhost Redirects** — Some routes redirect to `http://localhost:3000`. These need to be updated for production deployment.

---

## 🔮 Future Enhancements

### 🔧 Core Improvements
- [ ] **Real Payment Gateway** — Integrate Razorpay or Stripe for actual payment processing
- [ ] **Email/SMS Notifications** — Send OTPs, booking confirmations, and status updates via SMTP/Twilio
- [ ] **JWT Authentication** — Replace Flask sessions with JWT tokens for mobile app support
- [ ] **Cloud Image Storage** — Migrate file uploads to AWS S3 or Cloudinary

### 🚀 Feature Additions
- [ ] **Vendor Rating & Reviews** — Allow users to rate and review services after booking
- [ ] **Multi-Image Galleries** — Support multiple images per service listing
- [ ] **Advanced Search & Filters** — Price range sliders, availability calendar filtering
- [ ] **Bundle Bookings** — Book multiple services (hall + catering + photography) in one transaction
- [ ] **Vendor Chat** — In-app messaging between users and vendors
- [ ] **Admin Analytics Dashboard** — Platform-wide revenue charts, user growth, popular cities
- [ ] **Push Notifications** — Real-time booking alerts via WebSockets or Firebase

### 🏗 Architecture
- [ ] **Pagination & Infinite Scroll** — Handle large datasets efficiently
- [ ] **Redis Caching** — Cache frequently accessed service listings
- [ ] **Docker Containerization** — Package all 3 servers + MySQL into Docker Compose
- [ ] **CI/CD Pipeline** — Automated testing and deployment via GitHub Actions
- [ ] **REST API Documentation** — Swagger/OpenAPI spec for all endpoints
- [ ] **Mobile App** — React Native or Flutter app using the existing API

### 🔐 Security
- [ ] **HTTPS Enforcement** — SSL certificate setup
- [ ] **Rate Limiting** — Prevent brute-force on login endpoints
- [ ] **Input Sanitization** — Enhanced validation across all form inputs
- [ ] **CSRF Protection** — Add CSRF tokens to forms

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is built for academic/educational purposes as part of a final year project.

---

## 👨‍💻 Author

**Jainul Arsath**  
GitHub: [@jainularsath](https://github.com/jainularsath)

---

*Built with ❤️ for Tamil Nadu — connecting families with the best event services across the state.*
