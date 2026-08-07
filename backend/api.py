from flask import Flask, request, jsonify, flash
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import jwt
import datetime
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'




#### replace credential here
tmdbCredential = {}
####


# Fgenerate a token JWT
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # expiration time
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

# Database initialization
conn = sqlite3.connect('./bdd/data.db', check_same_thread=False)
cursor = conn.cursor()

# Create Users, Films, userfilms tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        CONSTRAINT nom UNIQUE (username)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS films (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL UNIQUE,
        genre TEXT NOT NULL,
        annee INTERGER NOT NULL,
        realisateur TEXT NOT NULL,
        acteur1 TEXT DEFAUT '',
        acteur2 TEXT DEFAUT '',
        acteur3 TEXT DEFAUT '',
        affiche TEXT DEFAUT '',
        CONSTRAINT film UNIQUE (titre)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS userfilms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXTE,
        film_id TEXTE,
        CONSTRAINT username FOREIGN KEY (user_id) REFERENCES users (username)
        CONSTRAINT titre FOREIGN KEY (film_id) REFERENCES films (titre)
    )
''')

conn.commit()


#***************************     USERS       **************************

# Get all users
@app.route('/users', methods=['GET'])
def get_users():
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    return jsonify({'users': users})

# get specific user
@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    cursor.execute('SELECT * FROM users WHERE username = ?', (user_id,))
    user = cursor.fetchone()
    if user:
        return jsonify({'user': user})
    else:
        return jsonify({'message': 'User not found'}), 404

# create user
@app.route('/adduser', methods=['POST'])
def create_user():
    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        email = data['email']
        password = data['password']
        cursor.execute('SELECT users.username FROM users WHERE username = ?',(username,))
        userdb = cursor.fetchone()

        if userdb == None:
            userdb= ''
        else:
            userdb = userdb[0]
           
        cursor.execute('SELECT email FROM users')
        emaildb = cursor.fetchall()
        for i in emaildb:
            if email in i[0]:
                email = 'emailUsed'
                          
        if userdb != username and email != 'emailUsed':
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, generate_password_hash(password)),)
            conn.commit()
     
            return jsonify({'message': 'Utilisateur créé'}),201
        else:
            return jsonify({'message': 'Utilisateur déja créé'}),500
    else:
        return jsonify({'message': ''})

# login route
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        password = data['password']
        error = None
        user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'

        elif not check_password_hash(user[3], password):
            error = 'Incorrect password.'
            return jsonify({'message': 'User connecté'}),401

        if error is None:   
            token = generate_token(user[1])
            return jsonify({'token': token, 'token_id': user[1]})
        flash(error)
    return jsonify({'message': 'user connecter'})

# update a specific user
@app.route('/user/<user_id>', methods=['GET','PUT'])
def update_user(user_id):
    data = request.get_json()
    email = data['email']
    password = data['password']
    cursor.execute('UPDATE users SET email = ?, password = ? WHERE username = ?', (email,generate_password_hash(password), user_id))
    conn.commit()
    return jsonify({'message': 'User updated successfully'})

# delete a specifique user
@app.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    cursor.execute('DELETE FROM users WHERE username = ?', (user_id,))
    conn.commit()
    return jsonify({'message': 'User deleted successfully'})



#*************************FILMS************************************

# GET films
@app.route('/films', methods=['GET'])
def get_films():
    cursor.execute('SELECT * FROM films ORDER BY "titre"')
    films = cursor.fetchall()
    return jsonify({'films': films})

# GET specific film
@app.route('/film/<int:film_id>', methods=['GET'])
def get_film(film_id):
    cursor.execute('SELECT * FROM films WHERE id = ?', (film_id,))
    film = cursor.fetchone()

    if film:
        return jsonify({'film': film})
    else:
        return 'Film introuvable', 404


# Add film
@app.route('/addfilm', methods=['GET', 'POST'])
def create_film():

    if request.method == 'POST':
        data = request.get_json()
        id = data['id']

        headers = tmdbCredential

        url = "https://api.themoviedb.org/3/movie/" + id +"?language=fr-FR"
        response = requests.get(url, headers=headers)
        data = response.json()

        url2 = "https://api.themoviedb.org/3/movie/" + id + "/credits?language=fr-FR"
        response = requests.get(url2, headers=headers)
        data2 = response.json()

        titre=data['title']
        genre = data['genres'][0]['name']
        annee = data['release_date']
        affiche = "https://image.tmdb.org/t/p/w500" + data['poster_path']
        realisateur = data2['crew'][0]['name']
        acteur1 = data2['cast'][0]['name']
        acteur2 = data2['cast'][1]['name']
        acteur3 = data2['cast'][2]['name']

                
        cursor.execute('SELECT films.titre FROM films WHERE titre = ?',(titre,))
        titredb = cursor.fetchone()
        if titredb == None:
            titredb = ''
        else:
            titredb = titredb[0]
               
        if titre != titredb:
            cursor.execute('INSERT INTO films (titre, genre, annee, realisateur, affiche, acteur1, acteur2, acteur3) VALUES (?, ?, ?, ?,?,?,?,?)', (titre, genre, annee, realisateur, affiche, acteur1, acteur2, acteur3 ))
            conn.commit()
        
            return jsonify({'message': 'Film created successfully'}),201
        else:
            return jsonify({'message': 'Film deja existant'}),404

# Update a specific film
@app.route('/film/<int:film_id>', methods=['GET','PUT'])
def update_film(film_id):
    data = request.get_json()
    genre = data['genre']
    annee = data['annee']
    realisateur = data['realisateur']
    affiche = data['affiche']
    cursor.execute('UPDATE films SET genre = ?, annee = ?, realisateur = ?, affiche = ? WHERE id = ? ', (genre, annee, realisateur, affiche, film_id))
    conn.commit()

    return jsonify({'message': 'Film updated successfully'})

# Delete a specific film
@app.route('/film/<int:film_id>', methods=['DELETE'])
def delete_film(film_id):
    cursor.execute('DELETE FROM films WHERE id = ?', (film_id,))
    conn.commit()
    return jsonify({'message': 'Film deleted successfully'})



# Search a film
@app.route('/search', methods=['GET', 'POST'])
def search_film():
    if request.method == 'POST':
        data = request.get_json()
        titre = data['titre']

        url = f'https://api.themoviedb.org/3/search/movie?query={titre}&include_adult=false&language=fr-FR&page=1'

        headers = tmdbCredential

        response = requests.get(url, headers=headers)

        data = response.json()
         
        return jsonify(data = data["results"])
    
    return jsonify({'message': 'Film inexistant'}),404


#*************************  USER FILMS  ******************************************

# GET userfilms
@app.route('/<user_id>/films', methods=['GET'])
def get_userfilms(user_id):
    cursor.execute('SELECT * from films INNER JOIN userfilms ON userfilms.film_id = films.titre WHERE userfilms.user_id = ? ORDER BY "titre"', (user_id,))
    films = cursor.fetchall()
    return jsonify({'films': films})


# GET userfilm
@app.route('/<user_id>/film/<int:film_id>', methods=['GET'])
def get_userfilm(user_id,film_id):
    cursor.execute('SELECT * from films INNER JOIN userfilms ON userfilms.film_id = films.titre WHERE userfilms.id = ?', (film_id,))
    films = cursor.fetchall()
    return jsonify({'films': films})


# Add user film
@app.route('/<user_id>/addfilm', methods=['GET', 'POST'])
def create_userfilm(user_id):

    if request.method == 'POST':
        data = request.get_json()
        id = data['id']

        headers = tmdbCredential

        url = "https://api.themoviedb.org/3/movie/" + id +"?language=fr-FR"
        response = requests.get(url, headers=headers)
        data = response.json()

        url2 = "https://api.themoviedb.org/3/movie/" + id + "/credits?language=fr-FR"
        response = requests.get(url2, headers=headers)
        data2 = response.json()

        titre=data['title']
        genre = data['genres'][0]['name']
        annee = data['release_date']
        affiche = "https://image.tmdb.org/t/p/w500" + data['poster_path']
        realisateur = data2['crew'][0]['name']
        acteur1 = data2['cast'][0]['name']
        acteur2 = data2['cast'][1]['name']
        acteur3 = data2['cast'][2]['name']

        cursor.execute('SELECT userfilms.film_id FROM userfilms WHERE user_id = ?',(user_id,))
        film_id= cursor.fetchall()

        for i in film_id:
            if titre == i[0]:
                film_id = i[0]
                break
            
        cursor.execute('SELECT films.titre FROM films WHERE titre = ?',(titre,))
        titredb = cursor.fetchone()
        if titredb == None:
            titredb = ''
        else:
            titredb = titredb[0]
       
        if titre != film_id:
            cursor.execute('INSERT INTO userfilms (user_id, film_id) VALUES (?, ?)', (user_id,titre))
            conn.commit()
        
        if titre != titredb:
            cursor.execute('INSERT INTO films (titre, genre, annee, realisateur, affiche, acteur1, acteur2, acteur3) VALUES (?, ?, ?, ?,?,?,?,?)', (titre, genre, annee, realisateur, affiche, acteur1, acteur2, acteur3 ))
            conn.commit()
        
        return jsonify({'message': 'Film created successfully'}),201
    else:
        return jsonify({'message': 'Film deja existant'}),404


# DELETE userfilm
@app.route('/<user_id>/film/<int:film_id>', methods=['DELETE'])
def delete_userfilm(user_id,film_id):

    cursor.execute('DELETE FROM userfilms WHERE  user_id = ? AND id = ?', (user_id,film_id))
    conn.commit()

    return jsonify({'message': 'Film deleted successfully'})



if __name__ == '__main__':
    app.run(debug=True, port=5000)
