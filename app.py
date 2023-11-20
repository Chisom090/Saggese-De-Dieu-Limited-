import csv
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, 
)
from flask_mysqldb import MySQL
import MySQLdb
from flask_bcrypt import Bcrypt
import random
import logging

app = Flask(__name__)
mysql = MySQL(app) 

@app.before_request
def before_request():
    try:
        if mysql.connection is None:
            mysql.connect()
    except MySQLdb.OperationalError as e:
        # Log the specific exception
        logging.error("MySQL connection error: %s", str(e))
bcrypt = Bcrypt(app)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'Chisom07'
app.config['MYSQL_PASSWORD'] = 'Nigeria@3'
app.config['MYSQL_DB'] = 'SaggeseStorage'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Allows accessing results as dictionaries


# Create Employee Table
with app.app_context():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            position VARCHAR(50) NOT NULL,
            phone_number VARCHAR(15) NOT NULL,
            picture_url VARCHAR(255),
            UNIQUE KEY unique_full_name (full_name)
        )
    ''')
    mysql.connection.commit()
    cursor.close()

# Create Purchase Forms Table
with app.app_context():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_forms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            description VARCHAR(255) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            employee_id INT,
            FOREIGN KEY (employee_id) REFERENCES employee(id)
        )
    ''')
    mysql.connection.commit()
    cursor.close()

# Create User Accounts Table
with app.app_context():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('HR', 'Consultant', 'Employee') NOT NULL
        )
    ''')
    mysql.connection.commit()
    cursor.close()
# Use logging for better error handling
# logging.basicConfig(level=logging.DEBUG)



# Routes for Flask Application
@app.route('/')
def home():
    return render_template('index.html', page_type="home")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO user_accounts (username, password_hash, role) VALUES (%s, %s, %s)",
                       (username, hashed_password, role))
        mysql.connection.commit()
        cursor.close()

        flash('Account created successfully', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    role_images = {'HR': 'hr-image-container', 'Consultant': 'consultant-image-container', 'Employee': 'employee-image-container'}

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_accounts WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            session['role'] = user['role']  # Set the role based on your actual login logic
            flash('Login successful.', 'success')

            # Redirect based on user's role
            if user['role'] == 'HR':
                return redirect(url_for('hr_dashboard'))
            elif user['role'] == 'Consultant':
                return redirect(url_for('consultant_dashboard'))
            elif user['role'] == 'Employee':
                return redirect(url_for('employee_dashboard'))

        # Set the role image container to display in the template
        role_image_container = role_images.get(user['role'], 'hr-image-container')
        flash('Login unsuccessful. Check username and password', 'danger')
        return render_template('login.html', role_image_container=role_image_container)

    return render_template('login.html', role_image_container='hr-image-container')


         
           


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

# Password Reset Route
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        if 'username' in session:
            username = session['username']
            # Retrieve the hashed initial password from the database
            cursor = mysql.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user_accounts WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()

            if user:
                initial_password_hash = user['password_hash']

                # Check if the current password matches the user's password
                if bcrypt.check_password_hash(initial_password_hash, current_password):
                    # Update the password to the new one
                    new_password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')

                    # Update the password in the database
                    cursor = mysql.connection.cursor()
                    cursor.execute("UPDATE user_accounts SET password_hash = %s WHERE username = %s",
                                   (new_password_hash, username))
                    mysql.connection.commit()
                    cursor.close()

                    flash('Password reset successful', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('Current password incorrect', 'danger')
            else:
                flash('User not found', 'danger')
        else:
            flash('User not logged in', 'danger')

    return render_template('index.html', page_type='reset_password.html')

# ... (remaining code)

# Employee Management

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        full_name = request.form['full_name']
        position = request.form['position']
        phone_number = request.form['phone_number']
        picture_url = request.form['picture_url']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO employee (full_name, position, phone_number, picture_url) VALUES (%s, %s, %s, %s)",
                       (full_name, position, phone_number, picture_url))
        mysql.connection.commit()
        cursor.close()

        flash('Employee added successfully', 'success')
        return redirect(url_for('home'))

    return render_template('index.html', page_type='add_employee.html')

@app.route('/remove_employee/<int:employee_id>')
def remove_employee(employee_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM employee WHERE id = %s", (employee_id,))
    mysql.connection.commit()
    cursor.close()

    flash('Employee removed successfully', 'success')
    return redirect(url_for('home'))

@app.route('/modify_employee/<int:employee_id>', methods=['GET', 'POST'])
def modify_employee(employee_id):
    if request.method == 'POST':
        full_name = request.form['full_name']
        position = request.form['position']
        phone_number = request.form['phone_number']
        picture_url = request.form['picture_url']

        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE employee SET full_name = %s, position = %s, phone_number = %s, picture_url = %s WHERE id = %s",
                       (full_name, position, phone_number, picture_url, employee_id))
        mysql.connection.commit()
        cursor.close()

        flash('Employee modified successfully', 'success')
        return redirect(url_for('home'))

    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employee WHERE id = %s", (employee_id,))
    employee = cursor.fetchone()
    cursor.close()

    return render_template('index.html', page_type='modify_employee.html', employee=employee)
# ... (Previous code)

# Routes for Flask Application

# Communication Features

@app.route('/approve_purchase_form/<int:purchase_form_id>', methods=['GET', 'POST'])
def approve_purchase_form(purchase_form_id):
    # Check if the user is HR
    if session.get('role') == 'HR':
        cursor = mysql.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM purchase_forms WHERE id = %s", (purchase_form_id,))
        purchase_form = cursor.fetchone()

        if purchase_form:
            # Here, you might implement the logic to update the purchase form status to 'approved'
            # Also, notify the consultant
            notify_consultant(purchase_form)
            flash(f'Purchase form approved and consultant notified: {purchase_form}', 'success')
        else:
            flash('Purchase form not found', 'danger')

        cursor.close()
    else:
        flash('Unauthorized access', 'danger')

    return redirect(url_for('home'))

def notify_consultant(purchase_form):
    # Here, you might implement the logic to notify the consultant
    # This could be through an email, message, or any notification mechanism
    print(f'Notifying consultant about approved purchase form: {purchase_form}')


# Function to validate purchase forms
def validate_purchase_forms(purchase_forms):
    # Implement your validation logic here
    # Check if the CSV data has the required fields and is not empty
    # You can add more specific validation based on your requirements
    return all(len(form) == 2 for form in purchase_forms)  # Assuming two fields: description and amount


# Function to save valid purchase forms to the database
def save_purchase_forms_to_db(purchase_forms):
    cursor = mysql.connection.cursor()
    for form in purchase_forms:
        description, amount = form
        cursor.execute("INSERT INTO purchase_forms (full_name, description, amount) VALUES (%s, %s, %s)",
                       (session['username'], description, amount))
    mysql.connection.commit()
    cursor.close()


# Route for employees to input purchase forms in CSV format
@app.route('/input_purchase_forms', methods=['GET', 'POST'])
def input_purchase_forms():
    if 'role' in session and session['role'] == 'Employee':
        if request.method == 'POST':
            csv_data = request.form.get('csv_data')

            # Parse CSV data
            csv_reader = csv.reader(csv_data.splitlines())
            purchase_forms = list(csv_reader)

            if validate_purchase_forms(purchase_forms):
                save_purchase_forms_to_db(purchase_forms)
                flash('Purchase forms saved successfully', 'success')
                return redirect(url_for('home'))
            else:
                flash('Incomplete or invalid CSV data. Please check and try again.', 'danger')

        return render_template('input_purchase_forms.html')
    else:
        flash('Unauthorized access. Please log in as an Employee.', 'danger')
        return redirect(url_for('login'))
# Function to label a form using the random module
def label_form():
    return f'Form_{random.randint(1000, 9999)}'

# Function to calculate the total amount from a list of forms
def calculate_total_amount(forms):
    total_amount = sum(form['amount'] for form in forms)
    return total_amount


# Function to check if the full name exists in the employee database
def is_valid_employee(full_name):
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employee WHERE full_name = %s", (full_name,))
    employee = cursor.fetchone()
    cursor.close()
    return employee is not None


# Code for saving a new form
@app.route('/save_form', methods=['POST'])
def save_form():
    full_name = request.form['full_name']
    description = request.form['description']
    amount = request.form['amount']
    employee_id = request.form['employee_id']

    # Label the form
    form_label = label_form()

    # Save the form with the generated label
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO purchase_forms (full_name, description, amount, employee_id) VALUES (%s, %s, %s, %s)",
                   (full_name, description, amount, employee_id))
    mysql.connection.commit()
    cursor.close()

    flash(f'Form saved successfully with label: {form_label}', 'success')
    return redirect(url_for('home'))

# Code for displaying forms and calculating total amount
@app.route('/display_forms')
def display_forms():
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM purchase_forms")
    forms = cursor.fetchall()
    cursor.close()

    total_amount = calculate_total_amount(forms)

    return render_template('forms.html', forms=forms, total_amount=total_amount)

@app.route('/hr_dashboard')
def hr_dashboard():
    if 'role' in session and session['role'] == 'HR':
        # Only HR has access to this route
        return render_template('hr_dashboard.html')  # Assuming you have a separate template for HR dashboard
    else:
        flash('Unauthorized access. Please log in as HR.', 'danger')
        return redirect(url_for('login'))

# Example route that requires Consultant access
@app.route('/consultant_dashboard')
def consultant_dashboard():
    if 'role' in session and session['role'] == 'Consultant':
        # Only Consultant has access to this route
        return render_template('consultant_dashboard.html')
    else:
        flash('Unauthorized access. Please log in as Consultant.', 'danger')
        return redirect(url_for('login'))

# Example route that requires Employee access
@app.route('/employee_dashboard')
def employee_dashboard():
    if 'role' in session and session['role'] == 'Employee':
        # Only Employee has access to this route
        return render_template('employee_dashboard.html')
    else:
        flash('Unauthorized access. Please log in as Employee.', 'danger')
        return redirect(url_for('login'))

# ...
# Route to display a list of employees
@app.route('/employee_list')
def employee_list():
    if 'role' in session and session['role'] == 'HR':
        cursor = mysql.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employee")
        employees = cursor.fetchall()
        cursor.close()
        return render_template('employee_list.html', employees=employees)
    else:
        flash('Unauthorized access. Please log in as HR.', 'danger')
        return redirect(url_for('login'))

# Route to search for employees by name
@app.route('/search_employee', methods=['POST'])
def search_employee():
    if 'role' in session and session['role'] == 'HR':
        search_term = request.form.get('search_term')

        cursor = mysql.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employee WHERE full_name LIKE %s", ('%' + search_term + '%',))
        search_results = cursor.fetchall()
        cursor.close()

        return render_template('search_results.html', results=search_results)
    else:
        flash('Unauthorized access. Please log in as HR.', 'danger')
        return redirect(url_for('login'))
# Import the logging moduleging

# ... (your existing imports)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# ... (your existing code)


if __name__ == '__main__':
    try:
        app.run(debug=False)
    except Exception as e:
        logging.exception("An error occurred: %s", str(e))
