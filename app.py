from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "parivahan_secret_key"

# ---------------- DATABASE ----------------
def get_db_connection():
    conn = sqlite3.connect("database.db", timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)
    # Admin table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT UNIQUE,
        password TEXT
    )
    """)

    # Buses table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS buses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_name TEXT,
        route TEXT,
        time TEXT,
        seats INTEGER
    )
    """)

    # Bookings table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        bus_name TEXT,
        route TEXT,
        time TEXT,
        seat_no INTEGER,
        journey_date TEXT
    )
    """)

        # Reviews table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        bus_name TEXT,
        rating INTEGER,
        comment TEXT
    )
    """)

    conn.commit()
    conn.close()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user is None:
            # Create account first time
            conn.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, password)
            )
            conn.commit()
            conn.close()
            session["user"] = email
            return redirect(url_for("home"))

        if user["password"] == password:
            conn.close()
            session["user"] = email
            return redirect(url_for("home"))
        else:
            conn.close()
            message = "Incorrect password!"

    return render_template("login.html", message=message)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

# ---------------- BUS LIST ----------------
@app.route("/buses")
def buses():
    conn = get_db_connection()

    buses = conn.execute("SELECT * FROM buses").fetchall()
    reviews = conn.execute("SELECT * FROM reviews").fetchall()

    conn.close()

    return render_template("buses.html", buses=buses, reviews=reviews)

# ---------------- SERVICES ----------------
@app.route("/services")
def services():
    return render_template("services.html")

# ---------------- BOOK ----------------
@app.route("/book", methods=["GET", "POST"])
def book():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("user_name")
        bus_name = request.form.get("bus_name")
        route = request.form.get("route")
        time = request.form.get("time")
        seat_no = request.form.get("seat_no")
        journey_date = request.form.get("journey_date")

        print("FORM:", name, bus_name, route, time, seat_no, journey_date)

        if not seat_no:
            return "<h3>Please enter seat number</h3>"

        if not bus_name:
            return "<h3>Bus name missing</h3>"

        if not journey_date:
            return "<h3>Select journey date</h3>"

        seat_no = int(seat_no)

        conn = get_db_connection()
        cur = conn.cursor()

        # Get total seats
        bus = cur.execute(
            "SELECT seats FROM buses WHERE bus_name=?",
            (bus_name,)
        ).fetchone()

        if not bus:
            conn.close()
            return "<h3>Bus not found</h3>"

        # Seat validation
        if seat_no < 1 or seat_no > bus["seats"]:
            conn.close()
            return "<h3>Invalid seat number</h3>"

        # Check already booked
        existing_booking = cur.execute(
            "SELECT * FROM bookings WHERE bus_name=? AND seat_no=? AND journey_date=?",
            (bus_name, seat_no, journey_date)
        ).fetchone()

        if existing_booking:
            conn.close()
            return "<h3>Seat already booked!</h3>"

        # Insert booking
        cur.execute(
            "INSERT INTO bookings (name, bus_name, route, time, seat_no, journey_date) VALUES (?, ?, ?, ?, ?, ?)",
            (name, bus_name, route, time, seat_no, journey_date)
        )

        conn.commit()
        conn.close()

        return "<h3>Ticket Booked Successfully!</h3>"

    return render_template("book.html")

# ---------------- ADMIN REGISTER ----------------
@app.route("/admin_register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO admin (user_name, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("admin_login"))

    return render_template("admin_register.html")

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        admin = conn.execute(
            "SELECT * FROM admin WHERE user_name=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if admin:
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))
        else:
            return "Invalid Admin Login"

    return render_template("admin_login.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")

# ---------------- ADMIN ADD BUS ----------------
@app.route("/add_bus", methods=["GET", "POST"])
def admin_add_bus():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        bus_name = request.form["bus_name"]
        route = request.form["route"]
        time = request.form["time"]
        seats = int(request.form["seats"])

        print("Adding bus:", bus_name, route, time, seats)  # debug

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO buses (bus_name, route, time, seats) VALUES (?, ?, ?, ?)",
            (bus_name, route, time, seats)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("view_buses"))

    return render_template("add_bus.html")

# ---------------- ADMIN VIEW BUSES ----------------
@app.route("/view_buses")
def view_buses():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    buses = conn.execute("SELECT * FROM buses").fetchall()
    conn.close()

    return render_template("view_buses.html", buses=buses)

# ---------------- ADMIN VIEW BOOKINGS ----------------
@app.route("/view_bookings")
def view_bookings():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    bookings = conn.execute("SELECT * FROM bookings").fetchall()
    conn.close()

    return render_template("view_bookings.html", bookings=bookings)

# ---------------- ADMIN VIEW REVIEWS ----------------
@app.route("/view_reviews")
def view_reviews():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    reviews = conn.execute("SELECT * FROM reviews").fetchall()
    conn.close()

    return render_template("view_reviews.html", reviews=reviews)

# ---------------- DELETE BOOKING ----------------
@app.route("/delete_booking/<int:id>")
def delete_booking(id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM bookings WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("view_bookings"))

# ---------------- ADD REVIEW ----------------
@app.route("/add_reviews", methods=["POST"])
def add_review():
    if "user" not in session:
        return redirect(url_for("login"))

    bus_name = request.form["bus_name"]
    rating = int(request.form["rating"])
    comment = request.form["comment"]
    user_email = session["user"]

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO reviews (user_email, bus_name, rating, comment) VALUES (?, ?, ?, ?)",
        (user_email, bus_name, rating, comment)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("buses"))

# ---------------- ADMIN LOGOUT ----------------
@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("THIS IS NEW APP FILE RUNNING")
    print(app.url_map)

    create_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)