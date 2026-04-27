# gui_client_darkmode.py
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import client

class VoteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Blockchain Voting GUI")
        self.root.configure(bg="#232429")  # dark background

        # Style configuration
        self.bg_color = "#2a2d36" #kontainer pinggiran
        self.fg_color = "#ffffff" #font id dan vote
        self.entry_bg = "#333742" #sel ID dan Vote
        self.btn_bg = "#1d5ffe" #tombol
        self.btn_fg = "#ffffff" #Font Tombol
        self.txt_bg = "#1c1d21" #Terminal Background
        self.txt_fg = "#ffffff" #Terminal Text

        # Input Frame
        frame = tk.Frame(root, bg=self.bg_color)
        frame.pack(pady=10)

        tk.Label(frame, text="Voter ID:", bg=self.bg_color, fg=self.fg_color).grid(row=0, column=0, sticky="w", padx=5)
        self.voter_entry = tk.Entry(frame, width=25, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color, relief="flat")
        self.voter_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Candidate:", bg=self.bg_color, fg=self.fg_color).grid(row=1, column=0, sticky="w", padx=5)
        self.candidate_entry = tk.Entry(frame, width=25, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color, relief="flat")
        self.candidate_entry.grid(row=1, column=1, padx=5)

        # Button Frame
        btn_frame = tk.Frame(root, bg=self.bg_color)
        btn_frame.pack(pady=10)

        btn_params = {"width": 15, "bg": self.btn_bg, "fg": self.btn_fg, "relief": "flat", "bd": 0, "activebackground": "#5a5aff", "cursor": "hand2"}

        tk.Button(btn_frame, text="Generate Keys", command=self.threaded(self.genkeys), **btn_params).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Register", command=self.threaded(self.register), **btn_params).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(btn_frame, text="Vote", command=self.threaded(self.vote), **btn_params).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(btn_frame, text="Force Commit", command=self.threaded(self.force_commit), **btn_params).grid(row=0, column=3, padx=5, pady=5)
        tk.Button(btn_frame, text="Show Chain", command=self.threaded(self.show_chain), **btn_params).grid(row=0, column=4, padx=5, pady=5)
        tk.Button(btn_frame, text="Show Results", command=self.threaded(self.show_results), **btn_params).grid(row=0, column=5, padx=5, pady=5)
        tk.Button(btn_frame, text="Reset Blockchain", command=self.threaded(self.reset_blockchain), **btn_params).grid(row=0, column=6, padx=5, pady=5)
        tk.Button(btn_frame, text="Validate Chain", command=self.threaded(self.validate_chain), **btn_params).grid(row=0, column=7, padx=5, pady=5)
        
        #modif
        tk.Button(btn_frame, text="Export Chain", command=self.threaded(self.export_chain), **btn_params).grid(row=0, column=8, padx=5, pady=5)
        #tk.Button(btn_frame, text="Import Chain", command=self.threaded(self.import_chain_prompt), **btn_params).grid(row=0, column=9, padx=5, pady=5)




        # Output box
        self.output_box = scrolledtext.ScrolledText(root, width=50, height=20, bg=self.txt_bg, fg=self.txt_fg, insertbackground=self.fg_color)
        self.output_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.output_box.configure(font=("Consolas", 11))

    def threaded(self, func):
        def wrapper():
            threading.Thread(target=func).start()
        return wrapper

    def print_to_box(self, text):
        self.output_box.insert(tk.END, text + "\n")
        self.output_box.see(tk.END)

    # --- Button functions ---
    def genkeys(self):
        voter_id = self.voter_entry.get().strip()
        if not voter_id:
            messagebox.showerror("Error", "Voter ID required")
            return
        self.print_to_box(f"Generating keys for {voter_id}...")
        client.cmd_genkeys(voter_id)
        self.print_to_box("Keys generated.\n")

    def register(self):
        voter_id = self.voter_entry.get().strip()
        if not voter_id:
            messagebox.showerror("Error", "Voter ID required")
            return
        self.print_to_box(f"Registering {voter_id}...")
        client.register(voter_id)
        self.print_to_box("Register done.\n")

    def vote(self):
        voter_id = self.voter_entry.get().strip()
        candidate = self.candidate_entry.get().strip()
        if not voter_id or not candidate:
            messagebox.showerror("Error", "Voter ID and Candidate required")
            return
        self.print_to_box(f"Voting for {candidate} by {voter_id}...")
        try:
            client.vote(voter_id, candidate)
        except Exception as e:
            self.print_to_box(f"Vote failed: {e}")
        self.print_to_box("Vote finished.\n")

    def force_commit(self):
        self.print_to_box("Force committing pending votes...")
        try:
            client.force_commit()
        except Exception as e:
            self.print_to_box(f"Force commit failed: {e}")
        self.print_to_box("Force commit finished.\n")

    def reset_blockchain(self):
        self.print_to_box("Resetting blockchain and pending votes...")
        try:
            client.reset_blockchain()
        except Exception as e:
            self.print_to_box(f"Reset failed: {e}")
        self.print_to_box("Blockchain reset done.\n")

    def validate_chain(self):
        self.print_to_box("Validating blockchain...")
        try:
            result = client.validate_chain()
            if isinstance(result, dict):
                if "valid" in result:
                    valid_text = "VALID" if result["valid"] else "INVALID"
                    self.print_to_box(f"Blockchain is {valid_text}\n")
                elif "error" in result:
                    self.print_to_box(f"Validation error: {result['error']}\n")
        except Exception as e:
            self.print_to_box(f"Validation exception: {e}\n")

    def show_chain(self):
        self.print_to_box("Fetching blockchain...")
        chain_window = tk.Toplevel(self.root)
        chain_window.title("Blockchain")
        txt = scrolledtext.ScrolledText(chain_window, width=140, height=40, bg=self.txt_bg, fg=self.txt_fg, insertbackground=self.fg_color)
        txt.pack()
        try:
            data = client.show_chain()
            if not data or "chain" not in data:
                txt.insert(tk.END, "No chain data available.\n")
                return
            for blk in data["chain"]:
                txt.insert(tk.END, f"Block #{blk['index']}\n")
                txt.insert(tk.END, "Data:\n")
                if isinstance(blk['data'], list):
                    for v in blk['data']:
                        txt.insert(tk.END, f"  Voter: {v.get('voter')}, Candidate: {v.get('candidate')}\n")
                else:
                    txt.insert(tk.END, f"  {blk['data']}\n")
                txt.insert(tk.END, f"Hash       : {blk['hash']}\n")
                txt.insert(tk.END, f"Prev Hash  : {blk['previous_hash']}\n")
                txt.insert(tk.END, f"Nonce      : {blk.get('nonce', 'N/A')}\n")
                txt.insert(tk.END, "="*70 + "\n")
        except Exception as e:
            txt.insert(tk.END, f"Error fetching chain: {e}\n")

        self.print_to_box("Blockchain displayed.\n")

    def show_results(self):
        self.print_to_box("Fetching voting results...")
        result_window = tk.Toplevel(self.root)
        result_window.title("Voting Results")
        txt = scrolledtext.ScrolledText(result_window, width=60, height=25, bg=self.txt_bg, fg=self.txt_fg, insertbackground=self.fg_color)
        txt.pack()
        try:
            data = client.show_results()
            if not data or "results" not in data:
                txt.insert(tk.END, "No results available.\n")
                return
            txt.insert(tk.END, "Voting Results:\n")
            for cand, count in data["results"].items():
                txt.insert(tk.END, f"  {cand}: {count} votes\n")
            txt.insert(tk.END, "="*40 + "\n")
            if data.get("pending_votes"):
                txt.insert(tk.END, "Pending Votes:\n")
                for v in data["pending_votes"]:
                    txt.insert(tk.END, f"  Voter: {v.get('voter')}, Candidate: {v.get('candidate')}\n")
        except Exception as e:
            txt.insert(tk.END, f"Error fetching results: {e}\n")

        self.print_to_box("Results displayed.\n")
        
    def export_chain(self):
        self.print_to_box("Exporting blockchain to JSON file...")
        try:
            result = client.export_chain()
            if "file" in result:
                self.print_to_box(f"Export successful. Saved as: {result['file']}\n")
                messagebox.showinfo("Success", f"Chain exported to:\n{result['file']}")
            else:
                self.print_to_box("Export failed.\n")
        except Exception as e:
            self.print_to_box(f"Export error: {e}\n")

    def import_chain_prompt(self):
        # Open dialog to ask filename
        import tkinter.simpledialog as sd
        filename = sd.askstring("Import Chain", "Enter filename (e.g., chain_export.json):")
        if not filename:
            return
        self.import_chain(filename)

    def import_chain(self, filename):
        self.print_to_box(f"Importing chain from {filename}...")
        try:
            result = client.import_chain(filename)

            if isinstance(result, dict) and result.get("status") == "success":
                self.print_to_box("Import successful.\n")
                messagebox.showinfo("Success", "Chain imported successfully.")

                # ⬇️ optional: auto refresh chain window
                self.show_chain()

            else:
                self.print_to_box(f"Import failed: {result}\n")

        except Exception as e:
            self.print_to_box(f"Import error: {e}\n")




if __name__ == "__main__":
    root = tk.Tk()
    gui = VoteGUI(root)
    root.mainloop()
