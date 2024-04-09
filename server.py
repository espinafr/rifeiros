#env\Scripts\python.exe
# -*- coding: utf-8 -*-

import os
from flask import Flask, request, render_template, abort, url_for, redirect, session, json, send_file
from werkzeug.exceptions import HTTPException
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__, static_folder='public', template_folder='views')

app.secret_key = os.environ.get('SECRET')
app.config['USERS'] = {os.environ.get('USER'): os.environ.get('SENHA'), os.environ.get('SUSER'): os.environ.get('SSENHA')}
app.config['SUPERUSER'] = os.environ.get('SUSER')

UPLOAD_FOLDER = 'public'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def access_db(command: str, params, method: str):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(command, params)
    results = cursor.fetchall() if method=='f' else conn.commit()
    conn.close()
    return results

@app.errorhandler(Exception)
def handle_exception(e):
    return render_template("erro.html", erro=e), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rifa')
def rifaredirect():
    return render_template('index.html')

@app.route('/rifa/<idrifa>')
def rifa(idrifa):
    rifa = access_db('SELECT * FROM rifas WHERE id = ? LIMIT 1', (idrifa,), 'f')
    return render_template('rifa.html', rifa=rifa)

@app.route('/procurarrifa', methods=['POST'])
def procurarrifa():
    idrifa = request.form['idrifa']
    rawData = access_db('SELECT * FROM rifas WHERE id = ? LIMIT 1', (idrifa,), 'f')
    if not rawData == []:
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

@app.route('/login')
def login():
    if 'username' in session:
        return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/loginprocess', methods=['POST'])
def loginprocess():
    username = request.form['username']
    password = request.form['password']
    if username in app.config['USERS'] and app.config['USERS'][username] == password:
        session['username'] = username
        if username == app.config['SUPERUSER']:
            session['superuser'] = True
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

@app.route('/registrarVenda', methods=['POST'])
def registrarVenda():
    if not 'username' in session:
        abort(401)
    nomeComprador = request.form['nomeComprador']
    numeroRifa = request.form['numeroRifa']
    telefone = request.form['telefone']
    pagamento = request.form['tipoPagamento']
    nomeVendedor = request.form['nomeVendedor']
    try:
        access_db('INSERT INTO rifas VALUES (?, ?, ?, ?, ?, ?)', (numeroRifa, nomeComprador, telefone, nomeVendedor, pagamento, datetime.now().strftime("%d/%m/%Y %H:%M:%S")), 'c') #- timedelta(hours=0)
    except Exception as e:
        print(e)
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@app.route('/admin/gerararquivo', methods=['POST'])    
def gerararquivo():
    if not 'username' in session:
        abort(401)
    rifas = access_db('SELECT id FROM rifas', (), 'f')
    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'numeros.txt'), 'w') as arquivo:
        for rifa in rifas:
            arquivo.write("%s\n" % rifa)
        print('Gerou novo arquivo')
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], 'numeros.txt'), as_attachment=True)

@app.route('/admin')
def admin():
    if 'username' in session:
        rifas = access_db('SELECT * FROM rifas', (), 'f')
        rifas.sort()
        return render_template('admin.html', username=session['username'], rifas=rifas)
    abort(401)

@app.route('/admin/delete/<idrifa>', methods=['POST'])
def admindelete(idrifa):
    if not 'username' in session or not session['superuser']:
        abort(401)
    access_db('DELETE FROM rifas WHERE id = ?', (idrifa,), 'c')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    access_db('''
        CREATE TABLE IF NOT EXISTS rifas (
            id INTEGER UNIQUE,
            nome TEXT,
            telefone TEXT,
            vendedor TEXT,
            pagamento TEXT,
            data INTEGER
        )
    ''', (), 'c') # criando a table
    app.run(debug=True)