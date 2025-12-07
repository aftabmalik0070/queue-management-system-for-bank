import sqlite3

def init_db():
    connection = sqlite3.connect('bank.db')
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Teller(
        ID integer PRIMARY KEY,
        Name text UNIQUE,
        password text,
        Status text,
        Skills text
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customer(
        ID integer PRIMARY KEY,
        Token_Number text,
        Service_Type text,
        Priority integer,
        Arrival_Time datetime,
        Assigned_Teller_ID text,
        Status text
    )""")

    tellers = [
        ('aftab', '12k412k4', 'active', 'New Account,Cash Deposit'),
        ('hamza', '6148', 'active', 'Loan Application,New Account'),
        ('ahmed', '6163', 'active', 'Bills,Loan Application') 
    ]
    
    for teller in tellers:
        try:
            cursor.execute("INSERT INTO Teller (Name, password, Status, Skills) VALUES (?, ?, ?, ?)", teller)
            print(f"Added teller: {teller[0]}")
        except sqlite3.IntegrityError:
            print(f"Teller {teller[0]} already exists.")
        except sqlite3.ProgrammingError as e:
            print(f"Error adding {teller[0]}: {e}")

    connection.commit()
    connection.close()
    print("Database initialized successfully with new tellers.")

if __name__ == "__main__":
    init_db()