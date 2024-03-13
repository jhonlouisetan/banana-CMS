import sqlite3
import tkinter
import tkinter.font 
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import uuid
import babel.numbers
import ttkthemes

# Function that validates whether an entry is an integer or not.
def validate_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

# Sort order as soon as the module opens.
current_sort_order = {"Debudding Date": "desc", "Harvesting Date": "desc", "Area": "desc", "Status": "desc", "Number of Crops": "desc"}

# Main function that adds 18 weeks to the entry.
def calculate_harvesting_date(debudding_date):
    debudding_date_obj = datetime.strptime(debudding_date, '%Y-%m-%d')
    harvesting_date = debudding_date_obj + timedelta(weeks=18)
    return harvesting_date.strftime('%Y-%m-%d')

# Main function that enters the entry into the table after checking if generated uuid is not already in the harvandlost_table.
def insert_crop_data(debudding_date, area, entry_count, status='Growing'):
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()

    if not validate_integer(entry_count):
        messagebox.showerror("Error", "Number of entries should only be a whole, non-negative number.")
        return

    entry_uuid = str(uuid.uuid4())

    while cur.execute("SELECT COUNT(*) FROM harvandlost_table WHERE id=?", (entry_uuid,)).fetchone()[0] > 0:
        entry_uuid = str(uuid.uuid4())

    harvesting_date = calculate_harvesting_date(debudding_date)

    status_id = cur.execute("SELECT crop_status_id FROM crop_statuses_table WHERE crop_status_desc=?", (status,)).fetchone()[0]

    cur.execute("SELECT area_name FROM areas_table WHERE area_id=?", (area,))
    area_name = cur.fetchone()[0]

    cur.execute("INSERT INTO main_table (id, debudding_date, harvesting_date, area, status, number) VALUES (?, ?, ?, ?, ?, ?)",
                (entry_uuid, debudding_date, harvesting_date, area_name, status, entry_count))
    
    con.commit()
    con.close()

    update()
    update_status_based_on_age()

# Function that checks if there are similar entries in the table.
def check_for_duplicate(debudding_date, area):
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM main_table WHERE debudding_date = ? AND area = ?", (debudding_date, area))
    count = cur.fetchone()[0]

    con.close()

    return count > 0

# Function that adds entries.
def add_entries():
    debudding_date = debudding_date_entry.get()
    area = area_var.get()

    # Check for duplicates
    if check_for_duplicate(debudding_date, area):
        messagebox.showerror("Duplicate Entry", "An entry with the same debudding date and area already exists.")
        return
    
    debudding_date = debudding_date_entry.get_date().strftime('%Y-%m-%d')
    area_name = area_var.get()
    entry_count = entry_count_var.get()

    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM areas_table")
    print(cur.fetchall())

    cur.execute("SELECT area_id FROM areas_table WHERE UPPER(area_name)=?", (area_name,))
    result = cur.fetchone()

    if result:
        area_id = result[0]
        print(f"Found area_id: {area_id} for area_name: {area_name}")
        insert_crop_data(debudding_date, area_id, entry_count)
        update()
        update_status_based_on_age()
    else:
        print(f"Invalid area name: {area_name}")
        messagebox.showerror("Error", "Invalid area name.")
    
    con.close()

# Function that formats dates.    
def format_dates(entry):
    formatted_entry = []
    for value in entry:
        if isinstance(value, str):
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
    for row in tree.get_children():
        tree.delete(row)

    data = fetch_data()

    for entry in data:
        formatted_entry = format_dates(entry)
        tree.insert('', 'end', values=formatted_entry)
        
# Function that deletes entries that have been selected.        
def delete():
    selected_items = tree.selection()
    if selected_items:
        confirmed = tkinter.messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected entries?")
        if confirmed:
            con = sqlite3.connect("crop_database.db")
            cur = con.cursor()

            for item in selected_items:

                values = tree.item(item, "values")

                cur.execute("DELETE FROM main_table WHERE id=?", (values[0],))

            con.commit()
            con.close()

            for item in selected_items:
                tree.delete(item)

            update_status_based_on_age()

# Function that checks crop data from the main table and displays it on the terminal. For debugging.
def check_entries():
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM main_table")
    data = cur.fetchall()

    for row in data:
        print(row)

    con.close()

# Function that fetches data from the main table.
def fetch_data():
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM main_table")
    data = cur.fetchall()
    con.close()
    return data

# Function that sorts entries in the frontend table.
def sort(column):
    data = [(tree.set(child, "Debudding Date"), tree.set(child, "Harvesting Date"),
             tree.set(child, "Area"), tree.set(child, "Status"), tree.set(child, "Number of Crops"), child)
            for child in tree.get_children("")]

    column_index = ["Debudding Date", "Harvesting Date", "Area", "Status", "Number of Crops"].index(column)

    current_sort_order[column] = "desc" if current_sort_order[column] == "asc" else "asc"

    # Update the lambda function to handle "Number of Crops" as an integer
    data.sort(key=lambda x: (x[column_index], int(x[4])), reverse=(current_sort_order[column] == "desc"))

    for i, (debudding_date, harvesting_date, area, status, num_crops, child) in enumerate(data):
        tree.move(child, "", i)


# Function that calucates crop age.
def calculate_age(debudding_date):
    debudding_date_obj = datetime.strptime(debudding_date, '%Y-%m-%d')
    
    current_date_obj = datetime.now()

    age_in_weeks = (current_date_obj - debudding_date_obj).days // 7

    return age_in_weeks

# Function that edits the status based on the value of the previous function.
def update_status_based_on_age():
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()

    cur.execute("SELECT rowid, debudding_date, area, status FROM main_table")
    data = cur.fetchall()

    for entry in data:
        row_id, debudding_date, area_id, status_id = entry

        age_in_weeks = calculate_age(debudding_date)

        if age_in_weeks < 16:
            new_status = cur.execute("SELECT crop_status_desc FROM crop_statuses_table WHERE crop_status_id=?", (1,)).fetchone()[0]  
        elif 17 <= age_in_weeks <= 19:
            new_status = cur.execute("SELECT crop_status_desc FROM crop_statuses_table WHERE crop_status_id=?", (2,)).fetchone()[0]  
        else:
            new_status = cur.execute("SELECT crop_status_desc FROM crop_statuses_table WHERE crop_status_id=?", (3,)).fetchone()[0]

        cur.execute("UPDATE main_table SET status=? WHERE rowid=?", (new_status, row_id))

    con.commit()
    con.close()

# Function that checks for duplicates in the harvested and lost table.
def check_for_duplicate_in_harvandlost(debudding_date, harvesting_date, area):
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM harvandlost_table WHERE debudding_date = ? AND harvesting_date = ? AND area = ?", (debudding_date, harvesting_date, area))
    count = cur.fetchone()[0]

    con.close()

    return count > 0

# Function that moves selected entries to the harvandlost table.        
def move_entries_to_harvandlost(status):
    selected_items = tree.selection()
    if selected_items:
        confirmed = tkinter.messagebox.askyesno("Confirm Action", f"Are you sure you want to mark the selected entries as {status}?")
        if confirmed:
            con = sqlite3.connect("crop_database.db")
            cur = con.cursor()

            status_row = cur.execute("SELECT crop_status_id FROM crop_statuses_table WHERE crop_status_desc=?", (status,)).fetchone()

            if status_row is not None:
                status_id = status_row[0]

                for item in selected_items:
                    original_values = cur.execute("SELECT debudding_date, harvesting_date, area, number FROM main_table WHERE id=?", (tree.item(item, "values")[0],)).fetchone()

                    entry_uuid = str(uuid.uuid4())

                    debudding_date = original_values[0]
                    harvesting_date = original_values[1]
                    area_value = original_values[2]
                    entry_count = original_values[3]

                    if check_for_duplicate_in_harvandlost(debudding_date, harvesting_date, area_value):
                        messagebox.showerror("Duplicate Entry", "An entry with the same debudding date, harvesting date, and area already exists in the harvested and lost table.")
                        continue

                    cur.execute("SELECT area_id FROM areas_table WHERE area_name=?", (area_value,))
                    area_id_result = cur.fetchone()

                    if area_id_result:
                        area_id = area_id_result[0]

                        status_desc_result = cur.execute("SELECT crop_status_desc FROM crop_statuses_table WHERE crop_status_id=?", (status_id,)).fetchone()

                        if status_desc_result:
                            status_desc = status_desc_result[0]

                            cur.execute("INSERT INTO harvandlost_table (id, debudding_date, harvesting_date, area, status, number) VALUES (?, ?, ?, ?, ?, ?)",
                                        (entry_uuid, debudding_date, harvesting_date, area_value, status_desc, entry_count))

                            cur.execute("DELETE FROM main_table WHERE id=?", (tree.item(item, "values")[0],))
                        else:
                            messagebox.showerror("Error", f"Status '{status}' not found in crop_statuses_table.")
                    else:
                        messagebox.showerror("Error", f"Invalid area letter: '{area_value}'.")

                con.commit()

                for item in selected_items:
                    tree.delete(item)

                update_status_based_on_age()

            else:
                messagebox.showerror("Error", f"Status '{status}' not found in crop_statuses_table.")

            con.close()
            update()


# Function that displays entries based on their status.            
def view_status_counts():
    selected_items = tree.selection()

    if not selected_items:
        selected_items = None

    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()

    status_counts = {"Growing": 0, "Ready to Harvest": 0, "Overripe": 0}

    if selected_items is None:
        data = cur.execute("SELECT status, SUM(number) FROM main_table GROUP BY status").fetchall()
        for entry in data:
            status = entry[0]
            count = entry[1]
            if status in status_counts:
                status_counts[status] += count
    else:
        for item in selected_items:
            entry_id = tree.item(item, "values")[0]
            print(f"Fetching data for entry ID: {entry_id}")
            entry_data = cur.execute("SELECT status, number FROM main_table WHERE id = ?", (entry_id,)).fetchone()
            print(f"Retrieved data: {entry_data}")
            if entry_data:
                status = entry_data[0]
                count = entry_data[1]
                if status in status_counts:
                    status_counts[status] += count

    con.close()

    print(f"Status counts: {status_counts}")

    results_window = tkinter.Toplevel()
    results_window.title("Crops Status Counter")

    status_tree = ttk.Treeview(results_window, columns=("Status", "Crop Count"), show="headings")
    status_tree.heading("Status", text="Status")
    status_tree.heading("Crop Count", text="Crop Count")
    status_tree.pack()

    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        status_tree.insert('', 'end', values=(status, count))


# Function that deselects items from the table.
def deselect_selected_items():
    selected_items = tree.selection()
    for item in selected_items:
        tree.selection_remove(item)

# Function that checks if area is valid or not.
def validate_area(*args):
    selected_area = area_var.get()
    valid_areas = ["A", "B", "C", "D", "E"]
    if selected_area not in valid_areas:
        messagebox.showerror("Invalid Area", "Please select a valid area (A, B, C, D, or E).")
        area_var.set(valid_areas[0])

# Function that checks if date is valid or not.
def validate_date():
    try:
        datetime.strptime(debudding_date_entry.get(), '%Y-%m-%d')
        return True
    except ValueError:
        messagebox.showerror("Invalid Date", "Please enter a valid date in the format YYYY-MM-DD.")
        debudding_date_entry.set_date(None)
        return False

# Function for running the frontend in a toplevel window.
def launch(root: tkinter.Tk):
    global tree, debudding_date_entry, area_var, area_dropdown, entry_count_var, entry_count_entry

    update_status_based_on_age()

    root = tkinter.Toplevel(root)
    root.title("Crop Monitoring")

    tree = ttk.Treeview(root, columns=("ID", "Debudding Date", "Harvesting Date", "Area", "Status", "Number of Crops"), show="headings")

    tree['displaycolumns'] = ("Debudding Date", "Harvesting Date", "Area", "Status", "Number of Crops")

    tree.heading("ID", text="ID")
    tree.heading("Debudding Date", text="Debudding Date", command=lambda: sort("Debudding Date"))
    tree.heading("Harvesting Date", text="Harvesting Date", command=lambda: sort("Harvesting Date"))
    tree.heading("Area", text="Area", command=lambda: sort("Area"))
    tree.heading("Status", text="Status", command=lambda: sort("Status"))
    tree.heading("Number of Crops", text="Number of Crops", command=lambda: sort("Number of Crops"))

    for col in ("Debudding Date", "Harvesting Date", "Area", "Status"):
        tree.column(col, width=100)

    tree.grid(row=6, column=0, columnspan=10)

    debudding_label = ttk.Label(root, text="Debudding Date:", width=20)
    debudding_label.grid(row=1, column=0, padx=15)

    debudding_date_entry = DateEntry(root, width=20, date_pattern='yyyy-mm-dd')
    debudding_date_entry.grid(row=1, column=1, padx=15)

    area_label = ttk.Label(root, text="Area (A-E):", width=20)
    area_label.grid(row=1, column=2)

    area_var = tkinter.StringVar()
    area_var.trace_add("write", validate_area)
    area_dropdown = ttk.Combobox(root, width=20, textvariable=area_var, values=["A", "B", "C", "D", "E"])
    area_dropdown.grid(row=1, column=3)
    area_dropdown.set("A")

    entry_count_label = ttk.Label(root, text="Number of Entries:", width=20)
    entry_count_label.grid(row=1, column=4, padx=25)

    entry_count_var = tkinter.StringVar(value="1")
    entry_count_entry = ttk.Entry(root, width=20, textvariable=entry_count_var)
    entry_count_entry.grid(row=1, column=5, padx=25)

    add_entries_button = ttk.Button(root, text="Add Entries", style="Accent.TButton", command=add_entries, width=20)
    add_entries_button.grid(row=2, column=2, padx=15, pady=20)

    delete_button = ttk.Button(root, text="Delete Selected Entries", style="ToggleButton", command=delete, width=20)
    delete_button.grid(row=2, column=3, padx=15, pady=20)

    mark_harvested_button = ttk.Button(root, text="Mark as Harvested", command=lambda: move_entries_to_harvandlost("Harvested"), width=20)
    mark_harvested_button.grid(row=7, column=1, pady=15, padx=15)

    mark_lost_button = ttk.Button(root, text="Mark as Lost", command=lambda: move_entries_to_harvandlost("Lost"), width=20)
    mark_lost_button.grid(row=7, column=2, pady=15, padx=15)

    view_status_button = ttk.Button(root, text="View Status Counts", command=lambda: view_status_counts(), width=20)
    view_status_button.grid(row=7, column=3, pady=15, padx=15)

    deselect_button = ttk.Button(root, text="Deselect Entries", command=lambda: tree.selection_remove(*tree.selection()), width=20)
    deselect_button.grid(row=7, column=4, pady=15, padx=15)

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    update()
    sort("Debudding Date")

    check_entries()