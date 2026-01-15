'''
Receive request. Launching the entire website serves as the entry point for all access.
'''
from flask import Flask
from claim_voucher.routes import bp as voucher_bp

app = Flask(__name__)
app.register_blueprint(voucher_bp)

@app.route('/')
def home():
    return '''
    <h1>CDC Voucher System</h1>
    <p>Welcome to the voucher redemption system</p>
    <p>Test link: <a href="/voucher/dashboard/H001">View the vouchers for the H001 family</a></p>
    '''

if __name__ == '__main__':

    app.run(debug=True, port=5000)

