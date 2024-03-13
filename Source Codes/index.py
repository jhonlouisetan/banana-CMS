import sqlite3 
import tkinter
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import os.path as path
from tkinter import PhotoImage
import crops
import harvandlost
import plantfertilizer as fert
import ttkthemes

# Function that creates the database file with three tables using SQLite
def create_databases_and_values():
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS crop_statuses_table ("
                "crop_status_id INT PRIMARY KEY, "
                "crop_status_desc TEXT CHECK (crop_status_desc IN ('Growing', 'Ready to Harvest', 'Overripe', 'Harvested', 'Lost')) NOT NULL)")
    
    cur.execute("CREATE TABLE IF NOT EXISTS fertilizer_type_table ( "
                "fert_type_id INT PRIMARY KEY, "
                "fert_type_name TEXT CHECK (fert_type_name IN ('Urea and Potash', 'Chicken Dung', 'Duofus', 'Complete Fertilizer')) NOT NULL)")
    
    cur.execute("CREATE TABLE IF NOT EXISTS areas_table ( "
                "area_id INT PRIMARY KEY, "
                "area_name TEXT CHECK (area_name IN ('A', 'B', 'C', 'D', 'E')) NOT NULL)")
    
    cur.execute("CREATE TABLE IF NOT EXISTS main_table ("
                "id TEXT PRIMARY KEY, "
                "debudding_date DATE NOT NULL, "
                "harvesting_date DATE, "
                "area TEXT NOT NULL, "
                "status TEXT NOT NULL,"
                "number INT NOT NULL, "
                "FOREIGN KEY(area) REFERENCES areas_table(area_id), "
                "FOREIGN KEY(status) REFERENCES crop_statuses_table(crop_status_id) )")

    cur.execute("CREATE TABLE IF NOT EXISTS harvandlost_table ("
                "id TEXT PRIMARY KEY, "
                "debudding_date DATE NOT NULL, "
                "harvesting_date DATE, "
                "area TEXT NOT NULL, "
                "status TEXT NOT NULL,"
                "number INT NOT NULL, "
                "FOREIGN KEY(area) REFERENCES areas_table(area_id), "
                "FOREIGN KEY(status) REFERENCES crop_statuses_table(crop_status_id) )")

    cur.execute("CREATE TABLE IF NOT EXISTS fertilizer_table ("
                "id TEXT PRIMARY KEY, "
                "fertilizing_date DATE NOT NULL, "
                "fertilizer_type TEXT NOT NULL, "
                "area TEXT NOT NULL, "
                "fertilizer_amount FLOAT NOT NULL, "
                "FOREIGN KEY (fertilizer_type) REFERENCES fertilizer_type_table(fert_type_id)"
                "FOREIGN KEY(area) REFERENCES areas_table(area_id) )")
    
    try:
        statuses = ["Growing", "Ready to Harvest", "Overripe", "Harvested", "Lost"]

        for i, status in enumerate(statuses, start=1):
            cur.execute("INSERT INTO crop_statuses_table (crop_status_id, crop_status_desc) "
                        "VALUES (?, ?)", (i, status))

        fertilizer_types = ["Urea and Potash", "Chicken Dung", "Duofus", "Complete Fertilizer"]
        for i, fertilizer_type in enumerate(fertilizer_types, start=1):
            cur.execute("INSERT INTO fertilizer_type_table (fert_type_id, fert_type_name) "
                        "VALUES (?, ?)", (i, fertilizer_type))
        
        areas = ["A", "B", "C", "D", "E"]
        for i, area in enumerate(areas, start=1):
            cur.execute("INSERT INTO areas_table (area_id, area_name) "
                        "VALUES (?, ?)", (i, area))

        con.commit()
    except sqlite3.IntegrityError:
        pass

    con.commit()
    con.close()

# Function that retrieves dates.
def get_dates(week, year):
    week = int(week)
    d = datetime(year, 1, 1) + timedelta(days=(week - 1) * 7 - datetime(year, 1, 1).weekday())
    start_date = d.strftime('%Y-%m-%d')
    end_date = (d + timedelta(days=6)).strftime('%Y-%m-%d')
    return start_date, end_date

# Function that gets the user role for the currently logged-in user
def get_role(entered_username, entered_password):
    with sqlite3.connect("user_database.db", check_same_thread=False) as con:
        cur = con.cursor()
        cur.execute("SELECT user_role_id FROM user_table WHERE user_id = ? AND user_password = ?", (entered_username, entered_password))
        user_role_id = cur.fetchone()
        return user_role_id[0] if user_role_id else None

# Function that shows the summary report.
def view_summary_report():
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()

    data = cur.execute("SELECT * FROM main_table WHERE status IN ('Growing', 'Ready to Harvest')").fetchall()
    data.reverse()

    harvesting_week_counts = {}

    for entry in data:
        debudding_date = entry[1]
        harvesting_date = entry[2]
        area = entry[3]

        try:
            debudding_date_obj = datetime.strptime(debudding_date, '%Y-%m-%d')
            harvesting_date_obj = datetime.strptime(harvesting_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", f"Invalid date format for entry with ID {entry[0]}")
            continue

        iso_week_number = harvesting_date_obj.isocalendar()[1]
        year = harvesting_date_obj.year

        week_key = f"{iso_week_number}-{year}-{area}"

        if week_key not in harvesting_week_counts:
            harvesting_week_counts[week_key] = {'count': entry[5]}
        else:
            harvesting_week_counts[week_key]['count'] += entry[5]

    con.close()

    results = tkinter.Toplevel()
    results.title("Summary Report")

    summary_table = ttk.Treeview(results, columns=("Harvesting Week", "Entry Count"), show="headings")
    summary_table.heading("Harvesting Week", text="Harvesting Week")
    summary_table.column("Harvesting Week", width=500)
    summary_table.heading("Entry Count", text="Entry Count")
    summary_table.pack(expand=True)

    for week_key, data in sorted(harvesting_week_counts.items(), key=lambda x: (int(x[0].split('-')[1]), int(x[0].split('-')[0]), x[0].split('-')[2]), reverse=False):

        iso_week_number, year, area = week_key.split('-')
        week_start, week_end = get_dates(iso_week_number, int(year))
        week_start_date = datetime.strptime(week_start, '%Y-%m-%d')
        week_end_date = datetime.strptime(week_end, '%Y-%m-%d')
        week_label = f"{week_start_date.strftime('%B %d, %Y')} to {week_end_date.strftime('%B %d, %Y')} ({area})"
        count = data['count']
        summary_table.insert('', 'end', values=(week_label, count))

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


# # Function that checks if authenticate_admin is true, if so then it runs the show_users_table function.
# def view_users_table():
#     access_granted = authenticate_admin()
#     if access_granted:
#         show_users_table()

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

# Function for running the frontend in a toplevel window.
def launch(root: tkinter.Tk, entered_username, entered_password):

    # Functions that launch other windows.
    def main_table():
        crops.launch(root)

    def harv_and_lost():
        harvandlost.launch(root)

    def fertilize():
        fert.launch(root)

    main_root = root

    root = tkinter.Toplevel(root)
    root.title("Crop Monitoring System")

    index_label = ttk.Label(root, text="Bartulaba-Domolok Banana Farm\n       Crop Monitoring System", font=("arial", "20", 'bold'))
    index_label.grid(row=0, column=0, pady=20, padx=30)

    crops_button = ttk.Button(root, text="Crops", style="ToggleButton", command=main_table, width=30)
    crops_button.grid(row=2, column=0, pady=10, padx=20)

    harvandlost_button = ttk.Button(root, text="Harvested and Lost Crops", style="ToggleButton", command=harv_and_lost, width=30)
    harvandlost_button.grid(row=3, column=0, pady=10, padx=20)

    fert_button = ttk.Button(root, text="Fertilizer Application", style="ToggleButton", command=fertilize, width=30)
    fert_button.grid(row=4, column=0, pady=10, padx=20)

    summary_button = ttk.Button(root, text="View Summary Report", style="ToggleButton", command=view_summary_report, width=30)
    summary_button.grid(row=5, column=0, pady=10, padx=20)

    user_role = get_role(entered_username, entered_password)
    if user_role == 1:
        view_users_button = ttk.Button(root, text="Manage Users", command=show_users_table, width=30)
        view_users_button.grid(row=7, column=0, pady=10)

    root.protocol("WM_DELETE_WINDOW", lambda: main_root.destroy())

    root.mainloop()

create_databases_and_values()