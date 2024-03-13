import sqlite3 
import tkinter
import tkinter.font 
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
import uuid
from datetime import datetime

# Function that checks if the entered number is a float or another value.
def validate_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

# Function that checks if there are similar entries in the table.
def check_duplicate(fertilizing_date, fertilizer_type, area):
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM fertilizer_table WHERE fertilizing_date = ? AND fertilizer_type = ? AND area = ?", 
                (fertilizing_date, fertilizer_type, area))
    count = cur.fetchone()[0]

    con.close()

    return count > 0

# Function that adds fertilizer data to the fertilizer table.
def insert_fertilizer_entry():
    fert_date = fert_date_entry.get()
    fertilizer_type = fert_var.get()
    area = area_var.get()
    fertilizer_amount = fert_amount_entry.get()

    if not validate_float(fertilizer_amount):
        messagebox.showerror("Error", "Fertilizer amount must be a valid number.")
        return

    # Check for duplicate entry
    if check_duplicate(fert_date, fertilizer_type, area):
        messagebox.showerror("Duplicate Entry", "An entry with the same fertilizing date, fertilizer type, and area already exists.")
        return

    entry_id = str(uuid.uuid4())

    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()
    
    # Convert area and fertilizer types to numeric IDs
    area_mapping = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
    fert_type_mapping = {"Urea and Potash": 1, "Chicken Dung": 2, "Duofus": 3, "Complete Fertilizer": 4}

    area_id = area_mapping.get(area)
    fert_type_id = fert_type_mapping.get(fertilizer_type)

    if area_id is None or fert_type_id is None:
        messagebox.showerror("Error", "Invalid area or fertilizer type.")
        return
    
    # Fetch corresponding values from areas_table and fertilizer_type_table
    cur.execute("SELECT area_name FROM areas_table WHERE area_id=?", (area_id,))
    area_name = cur.fetchone()[0]

    cur.execute("SELECT fert_type_name FROM fertilizer_type_table WHERE fert_type_id=?", (fert_type_id,))
    fert_type_name = cur.fetchone()[0]

    cur.execute("INSERT INTO fertilizer_table (id, fertilizing_date, fertilizer_type, area, fertilizer_amount) VALUES (?, ?, ?, ?, ?)",
                (entry_id, fert_date, fert_type_name, area_name, float(fertilizer_amount)))
    con.commit()
    con.close()

    update()

    fert_date_entry.set_date(None)
    fert_dropdown.set("Urea and Potash")
    area_dropdown.set("A")
    fert_amount_entry.delete(0, tkinter.END)


# Function that deletes entries that have been selected.  
def delete_selected_entries():
    selected_items = tree.selection()
    if selected_items:
        confirmed = tkinter.messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected entries?")
        if confirmed:
            con = sqlite3.connect("crop_database.db")
            cur = con.cursor()

            for item in selected_items:
                values = tree.item(item, "values")

                cur.execute("DELETE FROM fertilizer_table WHERE id=?", (values[0],))

            con.commit()
            con.close()

            for item in selected_items:
                tree.delete(item)

    update()

# Function that fetches data from the plant fertilizer table.
def fetch_data():
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM fertilizer_table")
    data = cur.fetchall()
    con.close()
    return data

# Function that formats dates.
def format_date(entry):
    formatted_entry = []
    for index, value in enumerate(entry):
        if index == 1:
            try:
                date_obj = datetime.strptime(value, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%B %d, %Y')
                formatted_entry.append(formatted_date)
            except ValueError:
                formatted_entry.append(value)
        else:
            formatted_entry.append(value)
    return formatted_entry

# Function that updates the frontend table.
def update():
    for item in tree.get_children():
        tree.delete(item)

    data = fetch_data()

    for entry in data:
        formatted_entry = format_date(entry) 
        tree.insert('', 'end', values=formatted_entry)

# Function that checks if input is valid or not.
def validate_fert(*args):
    selected_fert_type = fert_var.get()
    valid_fert_types = ["Urea and Potash", "Chicken Dung", "Duofus", "Complete Fertilizer"]
    if selected_fert_type not in valid_fert_types:
        messagebox.showerror("Invalid Fertilizer Type", "Please select a valid fertilizer type.")
        fert_var.set(valid_fert_types[0])

# Function that checks if date is valid or not.
def validate_date():
    try:
        datetime.datetime.strptime(fert_date_entry.get(), '%Y-%m-%d')
        return True
    except ValueError:
        messagebox.showerror("Invalid Date", "Please enter a valid date in the format YYYY-MM-DD.")

        fert_date_entry.set_date(None)
        return False

# Function for running the frontend in a toplevel window.
def launch(root):
    global fert_date_entry, fert_dropdown, fert_amount_entry, tree, fert_var, area_dropdown, area_var

    root = tkinter.Toplevel(root)
    root.title("Fertilizer Application")
    root.geometry("1200x425")

    tree = ttk.Treeview(root, columns=("ID", "Fertilizing Date", "Fertilizer Type", "Area", "Fertilizer Amount"), show="headings", height=12)

    tree['displaycolumns'] = ("Fertilizing Date", "Fertilizer Type", "Area", "Fertilizer Amount")

    tree.heading("ID", text="ID")
    tree.heading("Fertilizing Date", text="Fertilizing Date")
    tree.heading("Fertilizer Type", text="Fertilizer Type")
    tree.heading("Area", text="Area")
    tree.heading("Fertilizer Amount", text="Fertilizer Amount (Grams)")

    for col in ("Fertilizing Date", "Fertilizer Type", "Area", "Fertilizer Amount"):
        tree.column(col, width=150)

    tree.grid(row=100, column=0, columnspan=10)

    entry_count_label = ttk.Label(root, width=15, text="Fertilizing Date:")
    entry_count_label.grid(row=0, column=0, padx=20)

    fert_date_entry = DateEntry(root, width=20, date_pattern='yyyy-mm-dd')
    fert_date_entry.grid(row=0, column=1, padx=10)

    entry_count_label = ttk.Label(root, text="Fertilizer Type:")
    entry_count_label.grid(row=0, column=2, padx=100)

    fert_var = tkinter.StringVar()
    fert_var.trace_add("write", validate_fert)
    fert_dropdown = ttk.Combobox(root, width=15, textvariable=fert_var, values=["Urea and Potash", "Chicken Dung", "Duofus", "Complete Fertilizer"])
    fert_dropdown.grid(row=0, column=3)
    fert_dropdown.set("Urea and Potash")

    area_label = ttk.Label(root, text="Area:")
    area_label.grid(row=0, column=4, padx=10)

    area_var = tkinter.StringVar()
    area_dropdown = ttk.Combobox(root, width=5, textvariable=area_var, values=["A", "B", "C", "D", "E"])
    area_dropdown.grid(row=0, column=5)
    area_dropdown.set("A")

    entry_count_label = ttk.Label(root, text="Fertilizer Amount (Grams):")
    entry_count_label.grid(row=0, column=6)

    fert_amount_entry = ttk.Entry(root, width=30)
    fert_amount_entry.grid(row=0, column=7, padx=10)

    insert_button = ttk.Button(root, text="Insert Fertilizer Entry", command=insert_fertilizer_entry)
    insert_button.grid(row=1, column=2, padx=20, pady=20)

    delete_button = ttk.Button(root, text="Delete Selected Entries", command=delete_selected_entries)
    delete_button.grid(row=1, column=3, padx=20, pady=20)

    update()