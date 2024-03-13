import sqlite3
import tkinter
from tkinter import ttk, messagebox
import index
import os.path as path
import ttkthemes

# Function that opens the main menu.
def menu(entered_username, entered_password):
    root.withdraw()
    index.launch(root, entered_username, entered_password)

# Function that creates the user database.
def create_user_database():
    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS user_table ("
                    "user_id TEXT PRIMARY KEY, "
                    "user_password TEXT NOT NULL, "
                    "user_role_id INT NOT NULL, "
                    "FOREIGN KEY (user_role_id) REFERENCES user_roles(user_role_id))")
        
        cur.execute("CREATE TABLE IF NOT EXISTS user_roles ("
                    "user_role_id INT PRIMARY KEY, "
                    "user_role_desc varchar(6) NOT NULL)")
        
        con.commit()

# Function that creates the user roles table.
def create_user_roles():
    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()

        user_role_id1 = 1
        user_role_text1 = "Admin"
        user_role_id2 = 2
        user_role_text2 = "User"

        try:
            cur.execute("INSERT INTO user_roles (user_role_id, user_role_desc) "
                        "VALUES (?, ?)", (user_role_id1, user_role_text1))
            cur.execute("INSERT INTO user_roles (user_role_id, user_role_desc) "
                        "VALUES (?, ?)", (user_role_id2, user_role_text2))
            con.commit()
        except sqlite3.IntegrityError:
            pass

# Function that lets a user sign up and add their details to the user table.
def sign_up():
    username = user_id_input.get()
    password = password_input.get()

    if not username or not password:
        messagebox.showerror("Error", "Username and password are required")
        return

    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()

        try:
            cur.execute("INSERT INTO user_table (user_id, user_password, user_role_id) VALUES (?, ?, ?)", (username, password, 2))
            con.commit()

            cur.execute("SELECT user_role_desc FROM user_roles WHERE user_role_id = 2")
            user_role_desc = cur.fetchone()[0]
            messagebox.showinfo("Success", f"User registered successfully with role: {user_role_desc}")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "User with the same username already exists")

# Function that checks if values inputted in the username and password boxes are in the user_table
def log_in():
    username = user_id_input.get()
    password = password_input.get()

    if not username or not password:
        messagebox.showerror("Error", "Username and password are required")
        return

    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()

        cur.execute("SELECT * FROM user_table WHERE user_id = ? AND user_password = ?", (username, password))
        user = cur.fetchone()

        if user:
            messagebox.showinfo("Success", "Login successful")
            menu(username, password)  # Pass entered_username and entered_password
        else:
            messagebox.showerror("Error", "Invalid username or password")


# Function that authenticates whether a user is an admin or not.
def authenticate_admin():
    entered_username = user_id_input.get()
    entered_password = password_input.get()

    if not entered_username or not entered_password:
        messagebox.showerror("Error", "Both username and password are required")
        return False

    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()

        cur.execute("SELECT user_role_id FROM user_table WHERE user_id = ? AND user_password = ?", (entered_username, entered_password))
        user_role_id = cur.fetchone()

    if user_role_id and user_role_id[0] == 1:
        return True
    else:
        messagebox.showerror("Access Denied", "Invalid username or password, or insufficient privileges")
        return False

# Function that displays the table of users.    
def show_users_table():
    user_table_window = tkinter.Toplevel()
    user_table_window.title("Users Table")

    tree = ttk.Treeview(user_table_window)
    tree["columns"] = ("User ID", "User Password", "User Role")

    for col in tree["columns"]:
        tree.heading(col, text=col)

    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()

        cur.execute("SELECT user_table.user_id, user_password, user_role_desc FROM user_table "
                    "JOIN user_roles ON user_table.user_role_id = user_roles.user_role_id")
        users = cur.fetchall()

    for user in users:
        tree.insert("", "end", values=user)

    tree.pack()

    promotedemote_button = ttk.Button(user_table_window, text="Promote/Demote User", command=lambda: promote_demote_user(tree, user_table_window))
    promotedemote_button.pack(pady=10)

    remove_user_button = ttk.Button(user_table_window, text="Remove User", command=lambda: remove_user(tree))
    remove_user_button.pack(pady=10)


# Function that checks if authenticate_admin is true, if so then it runs the show_users_table function.
def view_users_table():
    access_granted = authenticate_admin()
    if access_granted:
        show_users_table()

# Funcion that promotes/demotes users.
def promote_demote_user(tree, user_table_window):
    selected_item = tree.selection()

    if not selected_item:
        messagebox.showerror("Error", "Please select a user to promote or demote")
        return

    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()

        for item in selected_item:
            user_id = tree.item(item, "values")[0]
            cur.execute("SELECT user_role_id FROM user_table WHERE user_id = ?", (user_id,))
            current_role_id = cur.fetchone()[0]

            new_role_id = 1 if current_role_id == 2 else 2
            cur.execute("UPDATE user_table SET user_role_id = ? WHERE user_id = ?", (new_role_id, user_id))

        con.commit()

    for item in tree.get_children():
        tree.delete(item)

    cur.execute("SELECT user_table.user_id, user_password, user_role_desc FROM user_table "
                "JOIN user_roles ON user_table.user_role_id = user_roles.user_role_id")
    users = cur.fetchall()

    for user in users:
        tree.insert("", "end", values=user)

# Function that removes users.
def remove_user(tree):
    selected_item = tree.selection()

    if not selected_item:
        messagebox.showerror("Error", "Please select a user to remove")
        return

    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()

        for item in selected_item:
            user_id = tree.item(item, "values")[0]
            cur.execute("SELECT user_role_id FROM user_table WHERE user_id = ?", (user_id,))
            user_role_id = cur.fetchone()[0]

            if user_role_id == 1:
                messagebox.showwarning("Warning", "Cannot remove an admin user.")
                return

        confirmation = messagebox.askyesno("Confirmation", "Are you sure you want to remove the selected user(s)?")

        if confirmation:
            for item in selected_item:
                user_id = tree.item(item, "values")[0]
                cur.execute("DELETE FROM user_table WHERE user_id = ?", (user_id,))

            con.commit()

            for item in tree.get_children():
                tree.delete(item)

            cur.execute("SELECT user_table.user_id, user_password, user_role_desc FROM user_table "
                        "JOIN user_roles ON user_table.user_role_id = user_roles.user_role_id")
            users = cur.fetchall()

            for user in users:
                tree.insert("", "end", values=user)
        else:
            return

# Function that adds the admin credentials.
def add_admin_account():
    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()

        admin_username = "admin"
        admin_password = "adminpass"
        admin_role_id = 1

        try:
            cur.execute("INSERT INTO user_table (user_id, user_password, user_role_id) "
                        "VALUES (?, ?, ?)", (admin_username, admin_password, admin_role_id))
            con.commit()
            messagebox.showinfo("Success", "Admin account added successfully")
        except sqlite3.IntegrityError:
            pass

create_user_database()
add_admin_account()

# Frontend code
root = tkinter.Tk()
root.title("Log In")

root.tk.call("source", path.abspath(path.join(path.dirname(__file__), "forest-light.tcl")))
ttk.Style().theme_use('forest-light')

login_label = ttk.Label(root, text="Bartulaba-Domolok Banana Farm\n       Crop Monitoring System", font=("arial", "20", 'bold'))
login_label.grid(row=0, column=0, pady=20, padx=30)

entry_count_label = ttk.Label(root, text="Username:", width=20)
entry_count_label.grid(row=1, column=0, padx=25)

user_id_input = tkinter.StringVar()
username_entry = ttk.Entry(root, width=20, textvariable=user_id_input)
username_entry.grid(row=2, column=0, padx=25)

entry_count_label = ttk.Label(root, text="Password:", width=20)
entry_count_label.grid(row=3, column=0, padx=25)

password_input = tkinter.StringVar()
password_entry = ttk.Entry(root, width=20, textvariable=password_input, show="*")
password_entry.grid(row=4, column=0, padx=25)

log_in_button = ttk.Button(root, text="Log In", command=log_in, width=20)
log_in_button.grid(row=5, column=0, pady=10)

sign_up_button = ttk.Button(root, text="Sign Up", command=sign_up, width=20)
sign_up_button.grid(row=6, column=0, pady=10)

create_user_roles()
root.mainloop()