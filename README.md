# TECH_INSTITUTE — Academic & Student Management Portal

A full-stack Django web application built for **TECH_INSTITUTE**, featuring online course applications, role-based Student, Instructor, and Admin portals, automated PDF document generation with official digital stamps, and real-time **Safaricom M-Pesa Daraja (STK Push)** tuition payments.

**Live Site:** [https://pythonanywhere.com](https://pythonanywhere.com)

---

## Key Features

### 1. Role-Based Portals
* **Student Portal (`/portal/dashboard/`):** View approved and pending course enrollments, track tuition balances, view 3-hour weekly class schedules, download study materials, submit assignments, check CAT/exam grades, and download stamped PDF documents.
* **Instructor Portal (`/portal/instructor/`):** Upload lecture notes/study materials, publish course assignments, grade student submissions with feedback, record CAT & final exam scores, and post notices.
* **Admin Control Center (`/portal/admin-panel/`):** Manage course catalog offerings, create instructor accounts directly, assign lecturers to courses, approve/reject student applications, schedule weekly classes, manage leadership team profiles, and monitor M-Pesa revenue.

### 2. Live Safaricom M-Pesa Daraja Integration
* Supports **Lipa Na M-Pesa Online (STK Push)** for both **Buy Goods Till (`CustomerBuyGoodsOnline`)** and **PayBill (`CustomerPayBillOnline`)** workflows.
* Routes outbound STK Push requests through a lightweight serverless **Cloudflare Worker Bridge** (`*.workers.dev`) to bypass free-tier hosting proxy restrictions and connect directly to `api.safaricom.co.ke`.
* Automatically receives Safaricom payment callbacks (`/payments/callback/`), updates transaction status (`Completed` / `Failed`), deducts paid tuition balances, and unlocks official receipts.

### 3. Official Stamped PDF Generation (ReportLab)
* **Admission Letters:** Generated automatically upon course application/approval with institutional header and official circular stamp.
* **Tuition Fee Receipts:** Instant downloadable PDF receipts showing M-Pesa transaction codes, amount paid, and remaining fee balance.
* **Academic Transcripts:** Official downloadable student transcripts summarizing course grades, remarks, and institutional verification stamp.

---

## Course Catalog

| Code | Course Title | Duration | Tuition (KES) |
| :--- | :--- | :--- | :--- |
| **CS101** | Full-Stack Web Development (Python & Django) | 6 Months | 45,000.00 |
| **CS102** | Mobile App Development (Android & Flutter) | 6 Months | 48,000.00 |
| **DS201** | Data Science & Machine Learning | 6 Months | 55,000.00 |
| **CY202** | Cybersecurity & Ethical Hacking | 6 Months | 60,000.00 |
| **NT103** | Computer Networking & Cloud Infrastructure | 4 Months | 38,000.00 |
| **DB104** | Database Administration & SQL Engineering | 3 Months | 30,000.00 |
| **UI105** | UI/UX Product Design | 3 Months | 28,000.00 |
| **IT100** | ICDL & Computer Applications | 2 Months | 15,000.00 |
| **HW106** | Computer Hardware Repair & Maintenance | 3 Months | 25,000.00 |
| **DM107** | Digital Marketing & E-Commerce Systems | 3 Months | 24,000.00 |

---

## Tech Stack
* **Backend:** Python 3.11, Django 5
* **Frontend:** Pure HTML5, CSS3 (modular stylesheets), Vanilla JavaScript
* **Database:** SQLite (Production on PythonAnywhere) / MySQL compatible
* **Payments:** Safaricom Daraja REST API + Cloudflare Workers Serverless Bridge
* **PDF Engine:** ReportLab
* **Hosting:** PythonAnywhere (Web App) & Cloudflare Workers (API Bridge)

---

## Local Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd Tech_Institute
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory based on `.env.example`:
   ```env
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   DB_ENGINE=sqlite

   MPESA_BRIDGE_URL=https://workers.dev
   BRIDGE_SECRET=your-bridge-secret
   MPESA_ENV=sandbox
   MPESA_CONSUMER_KEY=your_daraja_consumer_key
   MPESA_CONSUMER_SECRET=your_daraja_consumer_secret
   MPESA_SHORTCODE=174379
   MPESA_PARTY_B=174379
   MPESA_PASSKEY=your_daraja_passkey
   MPESA_TRANSACTION_TYPE=CustomerPayBillOnline
   MPESA_CALLBACK_URL=https://yourdomain.com
   ```

5. **Run database migrations and start the server:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

---

## Project Structure

```text
Tech_Institute/
├── TECH_INSTITUTE/     # Project settings, URLs, and WSGI configuration
├── accounts/           # Custom User model (Student, Instructor, Admin) & authentication
├── admissions/         # Course enrollment workflows & admission letter generation
├── courses/            # Course catalog, contact inquiries, and leadership team models
├── payments/           # M-Pesa STK Push integration, callback handler, & PDF receipts
├── portal/             # Role-based dashboards, schedules, assignments, & PDF transcripts
├── static/             # Separate CSS stylesheets and institutional branding assets
└── templates/          # Modular HTML templates for public pages and user portals
```
