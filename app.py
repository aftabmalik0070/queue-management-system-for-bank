from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

token_counter = 100
DATABASE = "bank.db"

SERVICE_CONFIG = {
    'Cash Deposit':     {'prefix': 'C', 'priority': 2},
    'Bills':            {'prefix': 'B', 'priority': 2},
    'New Account':      {'prefix': 'N', 'priority': 1},
    'Loan Application': {'prefix': 'L', 'priority': 1}
}

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def customer_page():
    return render_template('customer_test_page.html')

@app.route('/submit_form', methods=['POST'])
def submit_form():
    global token_counter 
    selected_service = request.form.get('selected-service')
    
    if not selected_service or selected_service not in SERVICE_CONFIG:
        return redirect(url_for('customer_page'))
    
    token_counter += 1
    config = SERVICE_CONFIG[selected_service]
    token_number = f"{config['prefix']}-{token_counter}"
    arrival_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()
    

    cursor.execute("""
        INSERT INTO Customer (Token_Number, Service_Type, Priority, Arrival_Time, Status) 
        VALUES (?, ?, ?, ?, ?)
    """, (token_number, selected_service, config['priority'], arrival_time, 'Waiting'))
    conn.commit()
    conn.close()
    
    return render_template('token.html', token=token_number, service=selected_service)



@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/message', methods=['POST'])
def message():
    user_name = request.form.get('username')
    stored_password = request.form.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Teller WHERE Name = ?", (user_name,))
    user = cursor.fetchone()
    conn.close()

    if user and user['password'] == stored_password:
        return render_template('teller_test_page.html', 
                               user=user['Name'], 
                               skills=user['Skills'],
                               teller_id=user['ID'],
                               serving_token=None)
    else:
        return render_template('login.html', msg="Invalid Credentials")

@app.route('/next_customer', methods=['POST'])
def next_customer():
    teller_id = request.form.get('teller_id')
    teller_skills_str = request.form.get('skills')
    teller_name = request.form.get('user')


    skills_list = teller_skills_str.split(',')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Customer WHERE Assigned_Teller_ID = ? AND Status = 'Serving'", (teller_id,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return render_template('teller_test_page.html', 
                           user=teller_name, skills=teller_skills_str, teller_id=teller_id,
                           serving_token=existing['Token_Number'],
                           customer_status=f"Finish serving {existing['Token_Number']} first!")


    placeholders = ','.join('?' for _ in skills_list)
    
    query = f"""
        SELECT * FROM Customer 
        WHERE Status = 'Waiting' 
        AND Service_Type IN ({placeholders}) 
        ORDER BY Priority ASC, Arrival_Time ASC 
        LIMIT 1
    """
    

    cursor.execute(query, skills_list)
    next_cust = cursor.fetchone()

    serving_token = None
    msg = "No customers matching your skills."

    if next_cust:

        cursor.execute("UPDATE Customer SET Status='Serving', Assigned_Teller_ID=? WHERE ID=?", (teller_id, next_cust['ID']))
        conn.commit()
        
        serving_token = next_cust['Token_Number']
        msg = f"Serving: {serving_token} ({next_cust['Service_Type']})"
    
    conn.close()

    return render_template('teller_test_page.html', 
                           user=teller_name, 
                           skills=teller_skills_str, 
                           teller_id=teller_id,
                           customer_status=msg,
                           serving_token=serving_token)

@app.route('/complete_transaction', methods=['POST'])
def complete_transaction():
    teller_id = request.form.get('teller_id')
    teller_name = request.form.get('user')
    teller_skills = request.form.get('skills')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE Customer SET Status='Completed' WHERE Assigned_Teller_ID=? AND Status='Serving'", (teller_id,))
    conn.commit()
    conn.close()

    return render_template('teller_test_page.html', 
                           user=teller_name, 
                           skills=teller_skills, 
                           teller_id=teller_id,
                           customer_status="Transaction Completed. Ready for next.",
                           serving_token=None)

if __name__ == "__main__":
    app.run(debug=True)