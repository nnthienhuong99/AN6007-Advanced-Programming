# mobile_app.py - Flet mobile application
import flet as ft
import requests
import json
from datetime import datetime
import os

# API Configuration
API_BASE_URL = "http://localhost:5000/api"

class CDCApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "CDC Vouchers"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # Application status
        self.current_user = None
        self.user_role = None  # "household", "merchant", "admin"
        self.household_data = None
        self.merchant_data = None
        
        # Initialize application
        self.setup_page()
    
    def setup_page(self):
        """Set page"""
        self.page.clean()
        self.show_home_page()
    
    def show_home_page(self):
        """Show Homepage - Character Selection"""
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
                    
                    ft.ElevatedButton(
                        "Admin",
                        icon=ft.icons.ADMIN_PANEL_SETTINGS,
                        on_click=lambda e: self.show_admin_login(),
                        style=ft.ButtonStyle(
                            padding=20,
                            bgcolor=ft.colors.ORANGE,
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
            f"{role.capitalize()} Login" if role != "admin" else "Admin Login",
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
        else:
            id_field = ft.TextField(
                label="Admin ID",
                hint_text="Enter Admin ID",
                prefix_icon=ft.icons.SECURITY,
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
    
    def show_admin_login(self):
        """Display administrator login page"""
        self.page.clean()
        
        title = ft.Text("Admin Login", size=24, weight=ft.FontWeight.BOLD)
        
        password_field = ft.TextField(
            label="Password",
            hint_text="Enter admin password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.icons.LOCK,
            width=300
        )
        
        login_btn = ft.ElevatedButton(
            "Login",
            icon=ft.icons.LOGIN,
            on_click=lambda e: self.handle_admin_login(password_field.value),
            width=300
        )
        
        back_btn = ft.TextButton(
            "Back to Home",
            on_click=lambda e: self.show_home_page()
        )
        
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=30),
                    password_field,
                    ft.Divider(height=20),
                    login_btn,
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
    
    def handle_admin_login(self, password):
        """Handle administrator login"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/admin/login",
                json={"password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_user = "admin"
                self.user_role = "admin"
                self.show_admin_dashboard()
            else:
                self.show_snackbar("Invalid password", ft.colors.RED)
        except Exception as e:
            self.show_snackbar(f"Error: {str(e)}", ft.colors.RED)
    
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
    
    def show_merchant_signup(self):
        """Display merchant registration page"""
        title = ft.Text("Merchant Registration", size=24, weight=ft.FontWeight.BOLD)
        
        # Get bank list
        banks = []
        try:
            response = requests.get(f"{API_BASE_URL}/banks")
            if response.status_code == 200:
                data = response.json()
                banks = data.get("banks", [])
        except:
            pass
        
        # Input fields
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
        
        # Bank selection
        bank_options = [ft.dropdown.Option(f"{bank['bank_code']} - {bank['bank_name']}") for bank in banks]
        bank_dropdown = ft.Dropdown(
            label="Select Bank",
            options=bank_options,
            width=300
        )
        
        branch_field = ft.TextField(
            label="Branch Code",
            hint_text="Enter branch code",
            prefix_icon=ft.icons.ACCOUNT_BALANCE,
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
        
        # Register button
        register_btn = ft.ElevatedButton(
            "Register",
            icon=ft.icons.BUSINESS_CENTER,
            on_click=lambda e: self.handle_merchant_signup(
                name_field.value,
                uen_field.value,
                bank_dropdown.value,
                branch_field.value,
                account_field.value,
                holder_field.value
            ),
            width=300
        )
        
        back_btn = ft.TextButton(
            "Back to Login",
            on_click=lambda e: self.show_login_page("merchant")
        )
        
        # layout
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    name_field,
                    uen_field,
                    bank_dropdown,
                    branch_field,
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
        
        try:
            # Extract bank code
            bank_code = bank.split(" - ")[0] if bank and " - " in bank else ""
            
            response = requests.post(
                f"{API_BASE_URL}/merchants/register",
                json={
                    "merchant_name": name,
                    "uen": uen,
                    "bank_code": bank_code,
                    "branch_code": branch,
                    "account_number": account,
                    "account_holder_name": holder
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                merchant_id = data.get("merchant_id")
                
                # Display success message
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
            on_click=lambda e: self.generate_redemption_code(),
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
    
    def generate_redemption_code(self):
        """Generate redemption code"""
        # Create temporary redemption code file
        import uuid
        code = str(uuid.uuid4())[:8].upper()
        
        # Save to file
        filename = f"redemption_code_{self.current_user}_{code}.txt"
        with open(filename, "w") as f:
            f.write(f"Household ID: {self.current_user}\n")
            f.write(f"Redemption Code: {code}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\nMerchant Instructions:\n")
            f.write("1. Open Merchant app\n")
            f.write(f"2. Enter Household ID: {self.current_user}\n")
            f.write(f"3. Enter Redemption Code: {code}\n")
            f.write("4. Select vouchers to redeem\n")
        
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
            hint_text="Enter household ID",
            prefix_icon=ft.icons.PERSON,
            width=300
        )
        
        code_field = ft.TextField(
            label="Redemption Code",
            hint_text="Enter redemption code",
            prefix_icon=ft.icons.CODE,
            width=300
        )
        
        voucher2_field = ft.TextField(
            label="$2 Vouchers",
            value="0",
            width=100
        )
        
        voucher5_field = ft.TextField(
            label="$5 Vouchers",
            value="0",
            width=100
        )
        
        voucher10_field = ft.TextField(
            label="$10 Vouchers",
            value="0",
            width=100
        )
        
        def increment_voucher(field, amount):
            current = int(field.value)
            field.value = str(current + amount)
            self.page.update()
        
        voucher_controls = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("$2", size=16),
                        ft.Row(
                            [
                                ft.IconButton(ft.icons.REMOVE, 
                                            on_click=lambda e: increment_voucher(voucher2_field, -1)),
                                voucher2_field,
                                ft.IconButton(ft.icons.ADD, 
                                            on_click=lambda e: increment_voucher(voucher2_field, 1))
                            ]
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Column(
                    [
                        ft.Text("$5", size=16),
                        ft.Row(
                            [
                                ft.IconButton(ft.icons.REMOVE, 
                                            on_click=lambda e: increment_voucher(voucher5_field, -1)),
                                voucher5_field,
                                ft.IconButton(ft.icons.ADD, 
                                            on_click=lambda e: increment_voucher(voucher5_field, 1))
                            ]
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Column(
                    [
                        ft.Text("$10", size=16),
                        ft.Row(
                            [
                                ft.IconButton(ft.icons.REMOVE, 
                                            on_click=lambda e: increment_voucher(voucher10_field, -1)),
                                voucher10_field,
                                ft.IconButton(ft.icons.ADD, 
                                            on_click=lambda e: increment_voucher(voucher10_field, 1))
                            ]
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        def process_redemption(e):
            household_id = household_field.value
            code = code_field.value
            
            if not household_id:
                self.show_snackbar("Please enter household ID", ft.colors.RED)
                return
            
            # Verify redemption code
            if code:
                code_file = f"redemption_code_{household_id}_{code}.txt"
                if not os.path.exists(code_file):
                    self.show_snackbar("Invalid redemption code", ft.colors.RED)
                    return
            
            # Get voucher quantity
            v2 = int(voucher2_field.value)
            v5 = int(voucher5_field.value)
            v10 = int(voucher10_field.value)
            
            if v2 + v5 + v10 == 0:
                self.show_snackbar("Please select at least one voucher", ft.colors.RED)
                return
            
            total = v2 * 2 + v5 * 5 + v10 * 10
            
            # Confirmation dialog box
            def confirm_redemption(e):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/transactions/redeem",
                        json={
                            "household_id": household_id,
                            "merchant_id": self.current_user,
                            "vouchers_2": v2,
                            "vouchers_5": v5,
                            "vouchers_10": v10
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Delete redemption code file
                        if code and os.path.exists(code_file):
                            os.remove(code_file)
                        
                        # Display success message
                        self.page.dialog.open = False
                        self.page.update()
                        
                        self.show_redemption_success(
                            data.get("transaction", {}).get("transaction_id", ""),
                            total,
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
                        ft.Divider(height=10),
                        ft.Text(f"$2 Vouchers: {v2}"),
                        ft.Text(f"$5 Vouchers: {v5}"),
                        ft.Text(f"$10 Vouchers: {v10}"),
                        ft.Divider(height=10),
                        ft.Text(f"Total Amount: ${total}", size=18, weight=ft.FontWeight.BOLD)
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
                    household_field,
                    code_field,
                    ft.Divider(height=20),
                    ft.Text("Select Vouchers to Redeem:", size=16),
                    voucher_controls,
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
    
    def show_admin_dashboard(self):
        """Display administrator dashboard"""
        self.page.clean()
        
        # Create application bar
        self.page.appbar = ft.AppBar(
            title=ft.Text("Admin Dashboard"),
            bgcolor=ft.colors.ORANGE,
            actions=[
                ft.IconButton(ft.icons.LOGOUT, on_click=lambda e: self.show_home_page())
            ]
        )
        
        title = ft.Text("System Administration", size=24, weight=ft.FontWeight.BOLD)
        
        # Get system statistics
        stats = {}
        try:
            response = requests.get(f"{API_BASE_URL}/stats")
            if response.status_code == 200:
                data = response.json()
                stats = data.get("stats", {})
        except:
            pass
        
        # Statistical cards
        stats_grid = ft.Row(
            [
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Households", size=14),
                                ft.Text(str(stats.get("total_households", 0)), 
                                       size=24, weight=ft.FontWeight.BOLD)
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=20,
                        width=150
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Merchants", size=14),
                                ft.Text(str(stats.get("total_merchants", 0)), 
                                       size=24, weight=ft.FontWeight.BOLD)
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=20,
                        width=150
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        stats_grid2 = ft.Row(
            [
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Transactions", size=14),
                                ft.Text(str(stats.get("total_transactions", 0)), 
                                       size=24, weight=ft.FontWeight.BOLD)
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=20,
                        width=150
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Amount", size=14),
                                ft.Text(f"${stats.get('total_amount_redeemed', 0)}", 
                                       size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN)
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=20,
                        width=150
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Function button
        view_all_households = ft.ElevatedButton(
            "View All Households",
            icon=ft.icons.GROUP,
            on_click=lambda e: self.show_all_households(),
            width=300
        )
        
        view_all_merchants = ft.ElevatedButton(
            "View All Merchants",
            icon=ft.icons.STORE,
            on_click=lambda e: self.show_all_merchants(),
            width=300
        )
        
        view_all_transactions = ft.ElevatedButton(
            "View All Transactions",
            icon=ft.icons.LIST_ALT,
            on_click=lambda e: self.show_all_transactions(),
            width=300
        )
        
        system_report = ft.ElevatedButton(
            "Generate Report",
            icon=ft.icons.ASSESSMENT,
            on_click=lambda e: self.generate_report(),
            width=300
        )
        
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    stats_grid,
                    ft.Divider(height=10),
                    stats_grid2,
                    ft.Divider(height=30),
                    view_all_households,
                    view_all_merchants,
                    view_all_transactions,
                    system_report
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ),
            padding=20,
            alignment=ft.alignment.center
        )
        
        self.page.add(content)
        self.page.update()
    
    def show_all_households(self):
        """Display all household"""
        self.page.clean()
        
        title = ft.Text("All Households", size=24, weight=ft.FontWeight.BOLD)
        
        # Get household List
        households = []
        try:
            response = requests.get(f"{API_BASE_URL}/households")
            if response.status_code == 200:
                data = response.json()
                households = data.get("households", [])
        except:
            pass
        
        # household List
        if households:
            household_list = ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                height=400
            )
            
            for household in households:
                balance = household.get("balance", {"2": 0, "5": 0, "10": 0})
                total_value = balance["2"] * 2 + balance["5"] * 5 + balance["10"] * 10
                
                household_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(household.get("household_id", ""), 
                                                   size=16, weight=ft.FontWeight.BOLD),
                                            ft.Text(f"${total_value}", 
                                                   size=16, color=ft.colors.GREEN)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Divider(height=5),
                                    ft.Text(household.get("name", ""), size=14),
                                    ft.Text(household.get("email", ""), size=12, color="gray"),
                                    ft.Row(
                                        [
                                            ft.Text(f"$2: {balance.get('2', 0)}", size=11),
                                            ft.Text(f"$5: {balance.get('5', 0)}", size=11),
                                            ft.Text(f"$10: {balance.get('10', 0)}", size=11)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_AROUND
                                    )
                                ]
                            ),
                            padding=15
                        ),
                        width=350
                    )
                )
        else:
            household_list = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.GROUP, size=60, color="gray"),
                        ft.Text("No households found", size=16, color="gray")
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=40
            )
        
        back_btn = ft.ElevatedButton(
            "Back to Admin",
            icon=ft.icons.ARROW_BACK,
            on_click=lambda e: self.show_admin_dashboard(),
            width=200
        )
        
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    ft.Text(f"Total: {len(households)} households", size=16),
                    household_list,
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
    
    def show_all_merchants(self):
        """Display all merchants"""
        self.page.clean()
        
        title = ft.Text("All Merchants", size=24, weight=ft.FontWeight.BOLD)
        
        # Get merchant list
        merchants = []
        try:
            response = requests.get(f"{API_BASE_URL}/merchants")
            if response.status_code == 200:
                data = response.json()
                merchants = data.get("merchants", [])
        except:
            pass
        
        # merchant list
        if merchants:
            merchant_list = ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                height=400
            )
            
            for merchant in merchants:
                merchant_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(merchant.get("merchant_id", ""), 
                                                   size=16, weight=ft.FontWeight.BOLD),
                                            ft.Badge(
                                                merchant.get("status", "Active"),
                                                bgcolor=ft.colors.GREEN if merchant.get("status") == "Active" else ft.colors.GREY
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Divider(height=5),
                                    ft.Text(merchant.get("merchant_name", ""), size=14),
                                    ft.Text(f"UEN: {merchant.get('uen', '')}", size=12),
                                    ft.Text(merchant.get("bank_name", ""), size=12, color="gray")
                                ]
                            ),
                            padding=15
                        ),
                        width=350
                    )
                )
        else:
            merchant_list = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.STORE, size=60, color="gray"),
                        ft.Text("No merchants found", size=16, color="gray")
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=40
            )
        
        back_btn = ft.ElevatedButton(
            "Back to Admin",
            icon=ft.icons.ARROW_BACK,
            on_click=lambda e: self.show_admin_dashboard(),
            width=200
        )
        
        content = ft.Container(
            content=ft.Column(
                [
                    title,
                    ft.Divider(height=20),
                    ft.Text(f"Total: {len(merchants)} merchants", size=16),
                    merchant_list,
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
    
    def show_all_transactions(self):
        """Get all transactions"""
        self.page.clean()
        
        title = ft.Text("All Transactions", size=24, weight=ft.FontWeight.BOLD)
        
        # Get transactions records
        transactions = []
        total_amount = 0
        try:
            response = requests.get(f"{API_BASE_URL}/transactions")
            if response.status_code == 200:
                data = response.json()
                transactions = data.get("transactions", [])
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
            
            for txn in transactions[-20:]:  # Display the most recent 20 items
                transaction_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(f"TX: {txn.get('transaction_id', '')}", 
                                                   size=12),
                                            ft.Text(f"${txn.get('amount', 0)}", 
                                                   size=16, weight=ft.FontWeight.BOLD, 
                                                   color=ft.colors.GREEN)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Divider(height=5),
                                    ft.Row(
                                        [
                                            ft.Text(f"Household: {txn.get('household_id', '')}", size=11),
                                            ft.Text(f"Merchant: {txn.get('merchant_id', '')}", size=11)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
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
            "Back to Admin",
            icon=ft.icons.ARROW_BACK,
            on_click=lambda e: self.show_admin_dashboard(),
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
    
    def generate_report(self):
        """Generate report"""
        import webbrowser
        
        # Open API statistics page
        webbrowser.open("http://localhost:5000/api/stats")
        
        self.show_snackbar("Report generated and opened in browser", ft.colors.BLUE)
    
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
    print("\nThen connect to: http://localhost:5000")
    print("=" * 60)
    
    ft.app(target=main)