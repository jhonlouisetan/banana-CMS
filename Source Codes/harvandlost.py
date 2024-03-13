import sqlite3 
import tkinter
import tkinter.font 
from tkinter import ttk
from tkinter import messagebox
import ttkthemes
from datetime import datetime

current_sort_order = {"Debudding Date": "desc", "Harvesting Date": "desc", "Area": "desc", "Status": "desc", "Number of Crops": "desc"}

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

                cur.execute("DELETE FROM harvandlost_table WHERE id=?", (values[0],))

            con.commit()
            con.close()

            for item in selected_items:
                tree.delete(item)

# Function that sorts entries in the frontend table.
def sort(column):
    data = [(tree.set(child, "Debudding Date"), tree.set(child, "Harvesting Date"),
             tree.set(child, "Area"), tree.set(child, "Status"), tree.set(child, "Number of Crops"), child)
            for child in tree.get_children("")]

    column_index = ["Debudding Date", "Harvesting Date", "Area", "Status", "Number of Crops"].index(column)

    current_sort_order[column] = "desc" if current_sort_order[column] == "asc" else "asc"

    data.sort(key=lambda x: (x[column_index], int(x[4])), reverse=(current_sort_order[column] == "desc"))

    for i, (debudding_date, harvesting_date, area, status, num_crops, child) in enumerate(data):
        tree.move(child, "", i)

# Function that formats dates.
def format_date(entry):
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
        formatted_entry = format_date(entry)
        tree.insert('', 'end', values=formatted_entry)

# Function that fetches data from the harvested and lost table.
def fetch_data():
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM harvandlost_table")
    data = cur.fetchall()
    con.close()
    return data

# Function that checks crop data from the main table and displays it on the terminal. For debugging.
def check_entries():
    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM harvandlost_table")
    data = cur.fetchall()

    for row in data:
        print(row)

    con.close()

# Function that displays entries based on their status.
def view_status_counts():
    selected_items = tree.selection()

    if not selected_items:
        selected_items = None

    con = sqlite3.connect("crop_database.db")
    cur = con.cursor()

    status_counts = {"Harvested": 0, "Lost": 0}

    if selected_items is None:
        data = cur.execute("SELECT status, SUM(number) FROM harvandlost_table GROUP BY status").fetchall()
        for entry in data:
            status = entry[0]
            count = entry[1]
            if status in status_counts:
                status_counts[status] += count
    else:
        for item in selected_items:
            entry_id = tree.item(item, "values")[0]
            print(f"Fetching data for entry ID: {entry_id}")
            entry_data = cur.execute("SELECT status, number FROM harvandlost_table WHERE id = ?", (entry_id,)).fetchone()
            print(f"Retrieved data: {entry_data}")
            if entry_data:
                status = entry_data[0]
                count = entry_data[1]
                if status in status_counts:
                    status_counts[status] += count

    con.close()

    print(f"Status counts: {status_counts}")

    results_window = tkinter.Toplevel()
    results_window.title("Harvested and Lost Status Counter")

    status_tree = ttk.Treeview(results_window, columns=("Status", "Crop Count"), show="headings")
    status_tree.heading("Status", text="Status")
    status_tree.heading("Crop Count", text="Crop Count")
    status_tree.pack()

    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        status_tree.insert('', 'end', values=(status, count))

# Function for running the frontend in a toplevel window.s
def launch(root):
    global tree

    root = tkinter.Toplevel(root)
    root.title("Harvested and Lost Crops")

    tree = ttk.Treeview(root, columns=("ID", "Debudding Date", "Harvesting Date", "Area", "Status", "Number of Crops"), show="headings")

    tree['displaycolumns'] = ("Debudding Date", "Harvesting Date", "Area", "Status", "Number of Crops")

    tree.heading("ID", text="ID")
    tree.heading("Debudding Date", text="Debudding Date", command=lambda: sort("Debudding Date"))
    tree.heading("Harvesting Date", text="Harvesting Date", command=lambda: sort("Harvesting Date"))
    tree.heading("Area", text="Area", command=lambda: sort("Area"))
    tree.heading("Status", text="Status", command=lambda: sort("Status"))
    tree.heading("Number of Crops", text="Number of Crops", command=lambda: sort("Number of Crops"))

    for col in ("Debudding Date", "Harvesting Date", "Area", "Status", "Number of Crops"):
        tree.column(col, width=100)

    tree.grid(row=0, column=0, columnspan=100)

    delete_button = ttk.Button(root, text="Delete Selected Entries", style="ToggleButton", command=delete, width=20)
    delete_button.grid(row=1, column=1, padx=20, pady=20)

    view_status_button = ttk.Button(root, text="View Status Counts", command=lambda: view_status_counts(), width=20)
    view_status_button.grid(row=1, column=2, padx=20, pady=20)

    deselect_button = ttk.Button(root, text="Deselect Entries", command=lambda: tree.selection_remove(*tree.selection()), width=20)
    deselect_button.grid(row=1, column=3, padx=20, pady=20)

    update()

    check_entries()