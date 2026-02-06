# mobile_app.py - Flet mobile application for CDC Vouchers
import flet as ft
import requests
import json
from datetime import datetime
import os

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

class CDCApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "CDC Vouchers"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # Application status
        self.current_user = None
        self.user_role = None  # "household", "merchant"
        self.household_data = None
        self.merchant_data = None
        
        # Initialize application
        self.setup_page()
    
    def setup_page(self):
        """Set page"""
        self.page.clean()
        self.show_home_page()
    
    def show_home_page(self):
        """Display homepage - role selection"""
        self.page.clean()
        self.page.appbar = None
        
        # Create homepage content
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Image(
                        src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
                        width=100,
                        height=100,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    ft.Text("CDC Vouchers", size=32, weight=ft.FontWeight.BOLD),
                    ft.Text("Singapore Government Voucher System", size=14, color="gray"),
                    ft.Divider(height=40),
                    
                    ft.ElevatedButton(
                        "Household User",
                        icon=ft.icons.HOME,
                        on_click=lambda e: self.show_login_page("household"),
                        style=ft.ButtonStyle(
                            padding=20,
                            bgcolor=ft.colors.BLUE,
                            color=ft.colors.WHITE
                        ),
                        width=300
                    ),
                    
                    ft.ElevatedButton(
                        "Merchant",
                        icon=ft.icons.STORE,
                        on_click=lambda e: self.show_login_page("merchant"),
                        style=ft.ButtonStyle(
                            padding=20,
                            bgcolor=ft.colors.GREEN,
                            color=ft.colors.WHITE
                        ),
                        width=300
                    ),
                    
                    ft.Divider(height=30),
                    ft.Text("© 2025 CDC Singapore", size=12, color="gray")
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            padding=40,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def show_login_page(self, role):
        """Display login page"""
        self.user_role = role
        self.page.clean()
        
        # title
        title = ft.Text(
            f"{role.capitalize()} Login",
            size=24,
            weight=ft.FontWeight.BOLD
        )
        
        # Input fields
        if role == "household":
            id_field = ft.TextField(
                label="Household ID",
                hint_text="Enter your Household ID",
                prefix_icon=ft.icons.PERSON,
                width=300
            )
        elif role == "merchant":
            id_field = ft.TextField(
                label="Merchant ID",
                hint_text="Enter your Merchant ID",
                prefix_icon=ft.icons.BUSINESS,
                width=300
            )
        
        # Button
        login_btn = ft.ElevatedButton(
            "Login",
            icon=ft.icons.LOGIN,
            on_click=lambda e: self.handle_login(id_field.value, role),
            width=300
        )
        
        signup_btn = ft.TextButton(
            "Don't have an account? Sign up",
            on_click=lambda e: self.show_signup_page(role)
        )
        
        back_btn = ft.TextButton(
            "Back to Home",
            on_click=lambda e: self.show_home_page()
        )
        
        # layout
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=30),
                    id_field,
                    ft.Divider(height=20),
                    login_btn,
                    ft.Divider(height=10),
                    signup_btn,
                    back_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            padding=40,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def handle_login(self, user_id, role):
        """Login handling"""
        if not user_id:
            self.show_snackbar("Please enter your ID", ft.colors.RED)
            return
        
        self.current_user = user_id
        self.user_role = role
        
        if role == "household":
            # Get household information
            try:
                response = requests.get(f"{API_BASE_URL}/households/{user_id}")
                if response.status_code == 200:
                    data = response.json()
                    self.household_data = data.get("household", {})
                    self.show_household_dashboard()
                else:
                    self.show_snackbar("Household not found", ft.colors.RED)
            except Exception as e:
                self.show_snackbar(f"Error: {str(e)}", ft.colors.RED)
        
        elif role == "merchant":
            # Merchant should be verified
            self.merchant_data = {"merchant_id": user_id, "merchant_name": "Merchant"}
            self.show_merchant_dashboard()
    
    def show_signup_page(self, role):
        """Display registration page"""
        self.page.clean()
        
        if role == "household":
            self.show_household_signup()
        elif role == "merchant":
            self.show_merchant_signup()
    
    def show_household_signup(self):
        """Display family registration page"""
        title = ft.Text("Household Registration", size=24, weight=ft.FontWeight.BOLD)
        
        # Input fields
        name_field = ft.TextField(
            label="Full Name",
            hint_text="Enter your full name",
            prefix_icon=ft.icons.PERSON,
            width=300
        )
        
        nric_field = ft.TextField(
            label="NRIC/FIN",
            hint_text="Enter NRIC or FIN",
            prefix_icon=ft.icons.BADGE,
            width=300
        )
        
        email_field = ft.TextField(
            label="Email",
            hint_text="Enter your email",
            prefix_icon=ft.icons.EMAIL,
            width=300
        )
        
        postal_field = ft.TextField(
            label="Postal Code",
            hint_text="Enter postal code",
            prefix_icon=ft.icons.LOCATION_ON,
            width=300
        )
        
        unit_field = ft.TextField(
            label="Unit Number",
            hint_text="Enter unit number",
            prefix_icon=ft.icons.HOME,
            width=300
        )
        
        # Register button
        register_btn = ft.ElevatedButton(
            "Register",
            icon=ft.icons.PERSON_ADD,
            on_click=lambda e: self.handle_household_signup(
                name_field.value,
                nric_field.value,
                email_field.value,
                postal_field.value,
                unit_field.value
            ),
            width=300
        )
        
        back_btn = ft.TextButton(
            "Back to Login",
            on_click=lambda e: self.show_login_page("household")
        )
        
        # layout
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    name_field,
                    nric_field,
                    email_field,
                    postal_field,
                    unit_field,
                    ft.Divider(height=20),
                    register_btn,
                    back_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=40,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def handle_household_signup(self, name, nric, email, postal, unit):
        """Process household registration"""
        if not all([name, nric, email, postal, unit]):
            self.show_snackbar("Please fill all fields", ft.colors.RED)
            return
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/households/register",
                json={
                    "name": name,
                    "nric": nric,
                    "email": email,
                    "postal_code": postal,
                    "unit_number": unit,
                    "num_people": 1
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                household_id = data.get("household_id")
                
                # Display success message
                self.page.clean()
                success_content = ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.icons.CHECK_CIRCLE, size=80, color=ft.colors.GREEN),
                            ft.Text("Registration Successful!", size=24, weight=ft.FontWeight.BOLD),
                            ft.Divider(height=20),
                            ft.Text(f"Your Household ID: {household_id}", size=18),
                            ft.Text("Please save this ID for login", size=14, color="gray"),
                            ft.Divider(height=30),
                            ft.ElevatedButton(
                                "Go to Login",
                                on_click=lambda e: self.show_login_page("household"),
                                width=200
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=40,
                    alignment=ft.alignment.center
                )
                self.page.add(success_content)
            else:
                error_data = response.json()
                self.show_snackbar(error_data.get("message", "Registration failed"), ft.colors.RED)
        
        except Exception as e:
            self.show_snackbar(f"Error: {str(e)}", ft.colors.RED)
# Display merchant registration page
    def show_merchant_signup(self):
        """"""
        title = ft.Text("Merchant Registration", size=24, weight=ft.FontWeight.BOLD)

        # Load banks (bank_code + bank_name)
        banks = []
        try:
            response = requests.get(f"{API_BASE_URL}/banks")
            if response.status_code == 200:
                data = response.json()
                banks = data.get("banks", [])
        except:
            pass

        # Inputs
        name_field = ft.TextField(
            label="Business Name",
            hint_text="Enter business name",
            prefix_icon=ft.icons.BUSINESS,
            width=300
        )

        uen_field = ft.TextField(
            label="UEN Number",
            hint_text="Enter UEN number",
            prefix_icon=ft.icons.NUMBERS,
            width=300
        )

        account_field = ft.TextField(
            label="Account Number",
            hint_text="Enter account number",
            prefix_icon=ft.icons.CREDIT_CARD,
            width=300
        )

        holder_field = ft.TextField(
            label="Account Holder Name",
            hint_text="Enter account holder name",
            prefix_icon=ft.icons.PERSON,
            width=300
        )

        # Dropdowns
        bank_options = [
            ft.dropdown.Option(f"{b.get('bank_code','')} - {b.get('bank_name','')}".strip(" -"))
            for b in banks
        ]

        bank_dropdown = ft.Dropdown(
            label="Select Bank",
            options=bank_options,
            width=300
        )

        branch_dropdown = ft.Dropdown(
            label="Select Branch",
            options=[],
            width=300,
            disabled=True
        )

        def _parse_bank(v: str):
            parts = (v or "").split(" - ", 1)
            bank_code = parts[0].strip()
            bank_name = parts[1].strip() if len(parts) > 1 else ""
            return bank_code, bank_name

        def _parse_branch_code(v: str) -> str:
            return (v or "").split(" - ", 1)[0].strip()

        def on_bank_change(e):
            # reset branch first
            branch_dropdown.options = []
            branch_dropdown.value = None
            branch_dropdown.disabled = True

            selected_bank = bank_dropdown.value
            if not selected_bank or " - " not in selected_bank:
                self.page.update()
                return

            bank_code, bank_name = _parse_bank(selected_bank)

            branches = []
            try:
                response = requests.get(
                    f"{API_BASE_URL}/banks/{bank_code}/branches",
                    params={"bank_name": bank_name}  # differentiate DBS vs POSB with same bank_code
                )
                if response.status_code == 200:
                    data = response.json()
                    branches = data.get("branches", [])
            except:
                branches = []

            branch_dropdown.options = [
                ft.dropdown.Option(
                    f"{br.get('branch_code','')} - {br.get('branch_name','')}".strip(" -")
                )
                for br in branches
            ]
            branch_dropdown.disabled = False
            self.page.update()

        bank_dropdown.on_change = on_bank_change

        # Buttons
        register_btn = ft.ElevatedButton(
            "Register",
            icon=ft.icons.BUSINESS_CENTER,
            on_click=lambda e: self.handle_merchant_signup(
                name_field.value,
                uen_field.value,
                bank_dropdown.value,
                branch_dropdown.value, 
                account_field.value,
                holder_field.value
            ),
            width=300
        )

        back_btn = ft.TextButton(
            "Back to Login",
            on_click=lambda e: self.show_login_page("merchant")
        )

        # Layout
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    name_field,
                    uen_field,
                    bank_dropdown,
                    branch_dropdown,
                    account_field,
                    holder_field,
                    ft.Divider(height=20),
                    register_btn,
                    back_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=40,
            alignment=ft.alignment.center
        )

        self.page.add(content)
        self.page.update()


    def handle_merchant_signup(self, name, uen, bank, branch, account, holder):
        """Process merchant registration"""
        if not all([name, uen, bank, branch, account, holder]):
            self.show_snackbar("Please fill all fields", ft.colors.RED)
            return

        # ✅ strict: bank must be "7171 - DBS Bank Ltd", not "7171"
        if " - " not in (bank or ""):
            self.show_snackbar("Please select a bank from the dropdown", ft.colors.RED)
            return

        try:
            bank_code, bank_name = bank.split(" - ", 1)
            bank_code = bank_code.strip()
            bank_name = bank_name.strip()

            branch_code = (branch or "").split(" - ", 1)[0].strip()

            response = requests.post(
                f"{API_BASE_URL}/merchants/register",
                json={
                    "merchant_name": name,
                    "uen": uen,
                    "bank_code": bank_code,
                    "bank_name": bank_name,           # ✅ send for auditing / clarity (backend can ignore if not needed)
                    "branch_code": branch_code,       # ✅ FIX: send code only, not full string
                    "account_number": account,
                    "account_holder_name": holder
                }
            )

            if response.status_code == 200:
                data = response.json()
                merchant_id = data.get("merchant_id")

                self.page.clean()
                success_content = ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.icons.CHECK_CIRCLE, size=80, color=ft.colors.GREEN),
                            ft.Text("Registration Successful!", size=24, weight=ft.FontWeight.BOLD),
                            ft.Divider(height=20),
                            ft.Text(f"Your Merchant ID: {merchant_id}", size=18),
                            ft.Text("Please save this ID for login", size=14, color="gray"),
                            ft.Divider(height=30),
                            ft.ElevatedButton(
                                "Go to Login",
                                on_click=lambda e: self.show_login_page("merchant"),
                                width=200
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=40,
                    alignment=ft.alignment.center
                )
                self.page.add(success_content)
            else:
                error_data = response.json()
                self.show_snackbar(error_data.get("message", "Registration failed"), ft.colors.RED)

        except Exception as e:
            self.show_snackbar(f"Error: {str(e)}", ft.colors.RED)
    
    def show_household_dashboard(self):
        """Display home user Dashboard"""
        self.page.clean()
        
        # Create application bar
        self.page.appbar = ft.AppBar(
            title=ft.Text(f"Welcome, {self.household_data.get('name', 'User')}"),
            bgcolor=ft.colors.BLUE,
            actions=[
                ft.IconButton(ft.icons.LOGOUT, on_click=lambda e: self.show_home_page())
            ]
        )
        
        # Get balance information
        balance = self.household_data.get("balance", {"2": 0, "5": 0, "10": 0})
        total_value = sum([
            balance.get("2", 0) * 2,
            balance.get("5", 0) * 5,
            balance.get("10", 0) * 10
        ])
        
        # Create card
        balance_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Your Balance", size=18, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=10),
                        ft.Text(f"Total: ${total_value}", size=24, color=ft.colors.GREEN, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=10),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text("$2", size=14),
                                        ft.Text(str(balance.get("2", 0)), size=20, weight=ft.FontWeight.BOLD)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                ft.VerticalDivider(width=20),
                                ft.Column(
                                    [
                                        ft.Text("$5", size=14),
                                        ft.Text(str(balance.get("5", 0)), size=20, weight=ft.FontWeight.BOLD)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                ft.VerticalDivider(width=20),
                                ft.Column(
                                    [
                                        ft.Text("$10", size=14),
                                        ft.Text(str(balance.get("10", 0)), size=20, weight=ft.FontWeight.BOLD)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20
            )
        )
        
        # Function button
        claim_btn = ft.ElevatedButton(
            "Claim Vouchers",
            icon=ft.icons.CARD_GIFTCARD,
            on_click=lambda e: self.show_voucher_claim(),
            width=300
        )
        
        view_transactions_btn = ft.ElevatedButton(
            "View Transactions",
            icon=ft.icons.HISTORY,
            on_click=lambda e: self.show_transactions(),
            width=300
        )
        
        generate_code_btn = ft.ElevatedButton(
            "Generate Redemption Code",
            icon=ft.icons.QR_CODE,
            on_click=lambda e: self.show_voucher_selection(),
            width=300
        )
        
        # layout
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"Household ID: {self.current_user}", size=16, color="gray"),
                    ft.Divider(height=20),
                    balance_card,
                    ft.Divider(height=20),
                    claim_btn,
                    view_transactions_btn,
                    generate_code_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ),
            padding=20,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def show_voucher_claim(self):
        """Displays voucher redemption page"""
        self.page.clean()
        
        title = ft.Text("Claim Vouchers", size=24, weight=ft.FontWeight.BOLD)
        
        # Check batches that have been claimed
        claimed_tranches = self.household_data.get("claimed_tranches", [])
        
        # Batch1: May 2025 ($500)
        tranche1_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("May 2025 Tranche", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE),
                        ft.Text("Total Value: $500", size=16),
                        ft.Divider(height=10),
                        ft.Text("• 50 x $2 vouchers", size=14),
                        ft.Text("• 20 x $5 vouchers", size=14),
                        ft.Text("• 30 x $10 vouchers", size=14),
                        ft.Divider(height=20),
                        ft.ElevatedButton(
                            "Already Claimed" if "T1" in claimed_tranches else "Claim Now",
                            icon=ft.icons.CHECK if "T1" in claimed_tranches else ft.icons.DOWNLOAD,
                            on_click=lambda e: self.claim_voucher_tranche("T1") if "T1" not in claimed_tranches else None,
                            disabled="T1" in claimed_tranches,
                            bgcolor=ft.colors.GREEN if "T1" not in claimed_tranches else ft.colors.GREY,
                            color=ft.colors.WHITE,
                            width=200
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20,
                width=300
            )
        )
        
        # Batch2: Jan 2026 ($300)
        tranche2_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("January 2026 Tranche", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN),
                        ft.Text("Total Value: $300", size=16),
                        ft.Divider(height=10),
                        ft.Text("• 30 x $2 vouchers", size=14),
                        ft.Text("• 12 x $5 vouchers", size=14),
                        ft.Text("• 18 x $10 vouchers", size=14),
                        ft.Divider(height=20),
                        ft.ElevatedButton(
                            "Already Claimed" if "T2" in claimed_tranches else "Claim Now",
                            icon=ft.icons.CHECK if "T2" in claimed_tranches else ft.icons.DOWNLOAD,
                            on_click=lambda e: self.claim_voucher_tranche("T2") if "T2" not in claimed_tranches else None,
                            disabled="T2" in claimed_tranches,
                            bgcolor=ft.colors.GREEN if "T2" not in claimed_tranches else ft.colors.GREY,
                            color=ft.colors.WHITE,
                            width=200
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20,
                width=300
            )
        )
        
        back_btn = ft.ElevatedButton(
            "Back to Dashboard",
            icon=ft.icons.ARROW_BACK,
            on_click=lambda e: self.show_household_dashboard(),
            width=200
        )
        
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    tranche1_card,
                    tranche2_card,
                    ft.Divider(height=30),
                    back_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            padding=40,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def claim_voucher_tranche(self, tranche_id):
        """voucher claimed batches"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/vouchers/claim",
                json={
                    "household_id": self.current_user,
                    "tranche_id": tranche_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.show_snackbar(data.get("message", "Vouchers claimed successfully!"), ft.colors.GREEN)
                
                # Refresh household data
                response = requests.get(f"{API_BASE_URL}/households/{self.current_user}")
                if response.status_code == 200:
                    data = response.json()
                    self.household_data = data.get("household", {})
                
                # Return to voucher redemption page
                self.show_voucher_claim()
            else:
                error_data = response.json()
                self.show_snackbar(error_data.get("message", "Claim failed"), ft.colors.RED)
        
        except Exception as e:
            self.show_snackbar(f"Error: {str(e)}", ft.colors.RED)
    
    def show_transactions(self):
        """Display transaction records"""
        self.page.clean()
        
        title = ft.Text("Transaction History", size=24, weight=ft.FontWeight.BOLD)
        
        # Get transaction records
        transactions = []
        try:
            response = requests.get(f"{API_BASE_URL}/transactions")
            if response.status_code == 200:
                data = response.json()
                # Filter current user's transactions
                transactions = [t for t in data.get("transactions", []) 
                              if t.get("household_id") == self.current_user]
        except:
            pass
        
        # transaction list
        if transactions:
            transaction_list = ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                height=400
            )
            
            for txn in transactions[-10:]:  # Display the 10 most recent items
                transaction_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(f"TX ID: {txn.get('transaction_id', '')}", 
                                                   size=12, color="gray"),
                                            ft.Text(f"${txn.get('amount', 0)}", 
                                                   size=16, weight=ft.FontWeight.BOLD, 
                                                   color=ft.colors.GREEN)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Divider(height=5),
                                    ft.Text(f"Merchant: {txn.get('merchant_id', '')}", size=12),
                                    ft.Text(f"Date: {txn.get('datetime', '')[:16]}", size=10, color="gray")
                                ]
                            ),
                            padding=10
                        ),
                        width=350
                    )
                )
        else:
            transaction_list = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.RECEIPT_LONG, size=60, color="gray"),
                        ft.Text("No transactions found", size=16, color="gray")
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=40
            )
        
        back_btn = ft.ElevatedButton(
            "Back to Dashboard",
            icon=ft.icons.ARROW_BACK,
            on_click=lambda e: self.show_household_dashboard(),
            width=200
        )
        
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    ft.Text(f"Total Transactions: {len(transactions)}", size=16),
                    transaction_list,
                    ft.Divider(height=20),
                    back_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=20,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def show_voucher_selection(self):
        """Display voucher selection page"""
        self.page.clean()
        
        title = ft.Text("Select Vouchers for Redemption", size=24, weight=ft.FontWeight.BOLD)
        
        # Get current balance
        balance = self.household_data.get("balance", {"2": 0, "5": 0, "10": 0})
        
        # Create quantity input control
        def create_voucher_counter(denomination, current_value, max_value):
            field = ft.TextField(
                value="0",
                width=80,
                text_align=ft.TextAlign.CENTER
            )
            
            def increment(e):
                current = int(field.value)
                if current < max_value:
                    field.value = str(current + 1)
                    self.page.update()
            
            def decrement(e):
                current = int(field.value)
                if current > 0:
                    field.value = str(current - 1)
                    self.page.update()
            
            return ft.Column(
                [
                    ft.Text(f"${denomination} Vouchers", size=16),
                    ft.Text(f"Available: {max_value}", size=12, color="gray"),
                    ft.Row(
                        [
                            ft.IconButton(ft.icons.REMOVE, on_click=decrement),
                            field,
                            ft.IconButton(ft.icons.ADD, on_click=increment)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ), field
        
        # Create selectors for three denominations
        voucher2_counter, self.voucher2_field = create_voucher_counter(2, 0, balance.get("2", 0))
        voucher5_counter, self.voucher5_field = create_voucher_counter(5, 0, balance.get("5", 0))
        voucher10_counter, self.voucher10_field = create_voucher_counter(10, 0, balance.get("10", 0))
        
        # Display total amount
        total_text = ft.Text("Total Amount: $0", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN)
        
        def update_total():
            v2 = int(self.voucher2_field.value)
            v5 = int(self.voucher5_field.value)
            v10 = int(self.voucher10_field.value)
            total = v2 * 2 + v5 * 5 + v10 * 10
            total_text.value = f"Total Amount: ${total}"
            self.page.update()
        
        def on_value_change(e):
            update_total()
        
        # Add change events to each input field
        self.voucher2_field.on_change = on_value_change
        self.voucher5_field.on_change = on_value_change
        self.voucher10_field.on_change = on_value_change
        
        # Generate redemption code button
        generate_btn = ft.ElevatedButton(
            "Generate Redemption Code",
            icon=ft.icons.QR_CODE,
            on_click=lambda e: self.generate_redemption_code_with_vouchers(),
            width=300,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )
        
        back_btn = ft.ElevatedButton(
            "Back to Dashboard",
            icon=ft.icons.ARROW_BACK,
            on_click=lambda e: self.show_household_dashboard(),
            width=200
        )
        
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    ft.Text("Select the number of vouchers you want to redeem:", size=16),
                    ft.Divider(height=10),
                    ft.Row(
                        [voucher2_counter, voucher5_counter, voucher10_counter],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    ft.Divider(height=20),
                    total_text,
                    ft.Divider(height=30),
                    generate_btn,
                    ft.Divider(height=10),
                    back_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            padding=30,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def generate_redemption_code_with_vouchers(self):
        """Generate a redemption code using the selected voucher"""
        import uuid
        
        # Get the selected number of vouchers
        v2 = int(self.voucher2_field.value)
        v5 = int(self.voucher5_field.value)
        v10 = int(self.voucher10_field.value)
        
        # Check if at least one voucher has been selected
        if v2 + v5 + v10 == 0:
            self.show_snackbar("Please select at least one voucher", ft.colors.RED)
            return
        
        # Check if balance is sufficient
        balance = self.household_data.get("balance", {"2": 0, "5": 0, "10": 0})
        if (v2 > balance.get("2", 0) or 
            v5 > balance.get("5", 0) or 
            v10 > balance.get("10", 0)):
            self.show_snackbar("Insufficient voucher balance", ft.colors.RED)
            return
        
        # Generate redemption code
        code = str(uuid.uuid4())[:8].upper()
        total_amount = v2 * 2 + v5 * 5 + v10 * 10
        
        # Save to file
        filename = f"redemption_code_{self.current_user}_{code}.txt"
        with open(filename, "w") as f:
            f.write(f"Household ID: {self.current_user}\n")
            f.write(f"Redemption Code: {code}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"$2 Vouchers: {v2}\n")
            f.write(f"$5 Vouchers: {v5}\n")
            f.write(f"$10 Vouchers: {v10}\n")
            f.write(f"Total Amount: ${total_amount}\n")
            f.write("\nMerchant Instructions:\n")
            f.write("1. Open Merchant app\n")
            f.write(f"2. Enter Household ID: {self.current_user}\n")
            f.write(f"3. Enter Redemption Code: {code}\n")
            f.write("4. Click 'Process Redemption' to complete transaction\n")
        
        # Display success message
        self.page.clean()
        success_content = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.QR_CODE, size=80, color=ft.colors.BLUE),
                    ft.Text("Redemption Code Generated!", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=20),
                    ft.Text("Share this code with merchant:", size=16),
                    ft.Text(code, size=32, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN),
                    ft.Divider(height=10),
                    ft.Text(f"Vouchers selected:", size=14),
                    ft.Text(f"• $2: {v2} vouchers", size=14),
                    ft.Text(f"• $5: {v5} vouchers", size=14),
                    ft.Text(f"• $10: {v10} vouchers", size=14),
                    ft.Text(f"Total: ${total_amount}", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    ft.Text(f"Saved to: {filename}", size=12, color="gray"),
                    ft.Divider(height=30),
                    ft.ElevatedButton(
                        "Back to Dashboard",
                        on_click=lambda e: self.show_household_dashboard(),
                        width=200
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=40,
            alignment=ft.alignment.center
        )
        
        self.page.add(success_content)
        self.page.update()
    
    def show_merchant_dashboard(self):
        """Display merchant dashboard"""
        self.page.clean()
        
        # Create application bar
        self.page.appbar = ft.AppBar(
            title=ft.Text(f"Merchant: {self.current_user}"),
            bgcolor=ft.colors.GREEN,
            actions=[
                ft.IconButton(ft.icons.LOGOUT, on_click=lambda e: self.show_home_page())
            ]
        )
        
        title = ft.Text("Merchant Dashboard", size=24, weight=ft.FontWeight.BOLD)
        
        # Redemption function
        household_field = ft.TextField(
            label="Household ID",
            hint_text="Enter household ID from customer",
            prefix_icon=ft.icons.PERSON,
            width=300
        )
        
        code_field = ft.TextField(
            label="Redemption Code",
            hint_text="Enter redemption code from customer",
            prefix_icon=ft.icons.CODE,
            width=300
        )
        
        def process_redemption(e):
            household_id = household_field.value
            code = code_field.value
            
            if not household_id or not code:
                self.show_snackbar("Please enter household ID and redemption code", ft.colors.RED)
                return
            
            # Check if the redemption code file exists
            code_file = f"redemption_code_{household_id}_{code}.txt"
            if not os.path.exists(code_file):
                self.show_snackbar("Invalid redemption code or household ID", ft.colors.RED)
                return
            
            # Read the redemption code file to obtain the number of vouchers
            try:
                with open(code_file, "r") as f:
                    lines = f.readlines()
                
                vouchers_2 = 0
                vouchers_5 = 0
                vouchers_10 = 0
                
                for line in lines:
                    if "$2 Vouchers:" in line:
                        vouchers_2 = int(line.split(":")[1].strip())
                    elif "$5 Vouchers:" in line:
                        vouchers_5 = int(line.split(":")[1].strip())
                    elif "$10 Vouchers:" in line:
                        vouchers_10 = int(line.split(":")[1].strip())
                
                total_amount = vouchers_2 * 2 + vouchers_5 * 5 + vouchers_10 * 10
                
                # Confirmation dialog box
                def confirm_redemption(e):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/transactions/redeem",
                            json={
                                "household_id": household_id,
                                "merchant_id": self.current_user,
                                "vouchers_2": vouchers_2,
                                "vouchers_5": vouchers_5,
                                "vouchers_10": vouchers_10
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Delete redemption code file
                            if os.path.exists(code_file):
                                os.remove(code_file)
                            
                            # Display success message
                            self.page.dialog.open = False
                            self.page.update()
                            
                            self.show_redemption_success(
                                data.get("transaction", {}).get("transaction_id", ""),
                                total_amount,
                                household_id
                            )
                        else:
                            error_data = response.json()
                            self.show_snackbar(error_data.get("message", "Redemption failed"), ft.colors.RED)
                    
                    except Exception as ex:
                        self.show_snackbar(f"Error: {str(ex)}", ft.colors.RED)
                
                def cancel_redemption(e):
                    self.page.dialog.open = False
                    self.page.update()
                
                # Create confirmation dialog box
                self.page.dialog = ft.AlertDialog(
                    title=ft.Text("Confirm Redemption"),
                    content=ft.Column(
                        [
                            ft.Text(f"Household: {household_id}"),
                            ft.Text(f"Merchant: {self.current_user}"),
                            ft.Text(f"Redemption Code: {code}"),
                            ft.Divider(height=10),
                            ft.Text(f"$2 Vouchers: {vouchers_2}"),
                            ft.Text(f"$5 Vouchers: {vouchers_5}"),
                            ft.Text(f"$10 Vouchers: {vouchers_10}"),
                            ft.Divider(height=10),
                            ft.Text(f"Total Amount: ${total_amount}", size=18, weight=ft.FontWeight.BOLD)
                        ],
                        tight=True
                    ),
                    actions=[
                        ft.TextButton("Cancel", on_click=cancel_redemption),
                        ft.TextButton("Confirm", on_click=confirm_redemption)
                    ]
                )
                self.page.dialog.open = True
                self.page.update()
                
            except Exception as ex:
                self.show_snackbar(f"Error reading redemption code file: {str(ex)}", ft.colors.RED)
        
        redeem_btn = ft.ElevatedButton(
            "Process Redemption",
            icon=ft.icons.PAYMENT,
            on_click=process_redemption,
            width=300,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )
        
        view_transactions_btn = ft.ElevatedButton(
            "View My Transactions",
            icon=ft.icons.RECEIPT,
            on_click=lambda e: self.show_merchant_transactions(),
            width=300
        )
        
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    ft.Text("Instructions:", size=16),
                    ft.Text("1. Ask customer for Household ID and Redemption Code", size=12),
                    ft.Text("2. Enter both values below", size=12),
                    ft.Text("3. Click 'Process Redemption'", size=12),
                    ft.Divider(height=20),
                    household_field,
                    code_field,
                    ft.Divider(height=20),
                    redeem_btn,
                    ft.Divider(height=10),
                    view_transactions_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ),
            padding=20,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def show_redemption_success(self, transaction_id, amount, household_id):
        """Display successful redemption page"""
        self.page.clean()
        
        success_content = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.CHECK_CIRCLE, size=100, color=ft.colors.GREEN),
                    ft.Text("Redemption Successful!", size=28, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=20),
                    ft.Text(f"Transaction ID: {transaction_id}", size=16),
                    ft.Text(f"Household: {household_id}", size=16),
                    ft.Text(f"Amount: ${amount}", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN),
                    ft.Text(f"Time: {datetime.now().strftime('%H:%M:%S')}", size=14, color="gray"),
                    ft.Divider(height=30),
                    ft.ElevatedButton(
                        "New Redemption",
                        icon=ft.icons.ADD,
                        on_click=lambda e: self.show_merchant_dashboard(),
                        width=200
                    ),
                    ft.ElevatedButton(
                        "View Receipt",
                        icon=ft.icons.RECEIPT,
                        on_click=lambda e: self.show_receipt(transaction_id),
                        width=200
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=40,
            alignment=ft.alignment.center
        )
        
        self.page.add(success_content)
        self.page.update()
    
    def show_receipt(self, transaction_id):
        """Show receipt"""
        self.show_snackbar(f"Receipt for transaction {transaction_id}", ft.colors.BLUE)
    
    def show_merchant_transactions(self):
        """Display merchant transaction records"""
        self.page.clean()
        
        title = ft.Text("Merchant Transactions", size=24, weight=ft.FontWeight.BOLD)
        
        # Get transaction records
        transactions = []
        total_amount = 0
        try:
            response = requests.get(f"{API_BASE_URL}/transactions")
            if response.status_code == 200:
                data = response.json()
                # Filter transactions of current merchant
                transactions = [t for t in data.get("transactions", []) 
                              if t.get("merchant_id") == self.current_user]
                total_amount = sum(t.get("amount", 0) for t in transactions)
        except:
            pass
        
        # Statistical cards
        stats_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text("Total", size=14),
                                        ft.Text(str(len(transactions)), size=24, weight=ft.FontWeight.BOLD)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                ft.VerticalDivider(width=20),
                                ft.Column(
                                    [
                                        ft.Text("Amount", size=14),
                                        ft.Text(f"${total_amount}", size=24, weight=ft.FontWeight.BOLD, 
                                               color=ft.colors.GREEN)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ]
                ),
                padding=20
            )
        )
        
        # Transaction list
        if transactions:
            transaction_list = ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                height=300
            )
            
            for txn in transactions[-10:]:  # Display the 10 most recent items
                transaction_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(f"TX: {txn.get('transaction_id', '')[:8]}...", 
                                                   size=12),
                                            ft.Text(f"${txn.get('amount', 0)}", 
                                                   size=16, weight=ft.FontWeight.BOLD, 
                                                   color=ft.colors.GREEN)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Divider(height=5),
                                    ft.Text(f"Household: {txn.get('household_id', '')}", size=12),
                                    ft.Text(f"Date: {txn.get('datetime', '')[:16]}", size=10, color="gray")
                                ]
                            ),
                            padding=10
                        ),
                        width=350
                    )
                )
        else:
            transaction_list = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.RECEIPT_LONG, size=60, color="gray"),
                        ft.Text("No transactions found", size=16, color="gray")
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=40
            )
        
        back_btn = ft.ElevatedButton(
            "Back to Dashboard",
            icon=ft.icons.ARROW_BACK,
            on_click=lambda e: self.show_merchant_dashboard(),
            width=200
        )
        
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    stats_card,
                    ft.Divider(height=20),
                    ft.Text("Recent Transactions:", size=16),
                    transaction_list,
                    ft.Divider(height=20),
                    back_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=20,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def show_snackbar(self, message, color=ft.colors.BLUE):
        """Display prompt message"""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

def main(page: ft.Page):
    # Set page properties
    page.title = "CDC Vouchers Mobile App"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Initialize application
    app = CDCApp(page)

if __name__ == "__main__":
    print("=" * 60)
    print("CDC Vouchers Mobile Application")
    print("=" * 60)
    print("\nMake sure the Flask API server is running:")
    print("• python app.py")
    print("\nThen connect to: http://localhost:8000")
    print("\nFeatures:")
    print("• Household users: Claim vouchers, generate redemption codes")
    print("• Merchants: Process redemptions, view transactions")
    print("• Automatic CSV generation for all transactions")
    print("=" * 60)
    
    ft.app(target=main)