import flask import Flask, request, render_template, redirect, url_for 


app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('test_page.html')

