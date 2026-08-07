from flask import Flask, jsonify, redirect, request, render_template, url_for,session, g
from werkzeug.security  import generate_password_hash
import requests
import jwt
import functools


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'your_secret_key'

urlApi = 'http://172.22.0.3:5000'


# verify and decode token JWT
def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Le token a expiré
    except jwt.InvalidTokenError:
        return None  # Le token est invalide


# add g.user variable
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
            g.user =None
    else:
        g.user = user_id

# add fonction login required
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view



#*****************    INDEX    *******************************
# index
@app.route('/', methods=['GET'])
def index():
    return render_template('base.html')


#*****************USER****************************
# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        url = f'{urlApi}/login'
        username = request.form['username']
        password = request.form['password']
        data = {'username': username, 'password': password}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data,headers=headers)

        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            token_id = data.get('token_id')

            if token:
                decoded_token = verify_token(token)
                if decoded_token:
                    session.clear()
                    session['user_id'] = decoded_token['user_id']
                    return redirect(url_for('get_userfilms'))

        elif response.status_code == 401:
            return render_template('login.html', message='Mot de passe incorrect')
        else:
            return redirect(url_for('login'))
        
    return render_template('login.html')

# logout
@app.route('/logout')
def logout():
    session.clear()
    g.user = None
    return redirect(url_for('index'))

# create user
@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']

        if password != confirmPassword:
            return render_template('register.html', message='les password ne correpondent pas')

        else:
            data = {'username': username, 'email': email, 'password': password}
            url = f'{urlApi}/adduser'
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=data,headers=headers)
            if response.status_code == 201:
                return redirect(url_for('login'))
            elif response.status_code == 500:
                return render_template('register.html',message= 'user déja creé'),500
            else:
                return jsonify({'error': 'page not found'}), 404
        
    else:
        return render_template('register.html')


# Delete a specific user
@app.route('/user/<user_id>', methods=['POST','DELETE'])
@login_required
def delete_user(user_id):
    url = f'{urlApi}/user/{g.user}'
    headers = {"Content-Type": "application/json"}
    response = requests.delete(url, json=user_id,headers=headers)

    if response.status_code == 200:

        return redirect(url_for('logout'))
    else:
        return jsonify({'error': 'page not found'}), 404


# read a specific user
@app.route('/user/<user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    url = f'{urlApi}/user/{user_id}'
    response = requests.get(url)
    if response.status_code == 200:
        user = response.json()
        return render_template('user.html', user_id=user)
    else:
        return jsonify({'error': 'page not found'}), 404


# Update a specific user
@app.route('/update_user/<user_id>', methods=[ 'GET','POST'])
@login_required
def update_user(user_id):
    if request.method == 'GET':
        url_get = f'{urlApi}/user/{user_id}'
        response_get = requests.get(url_get)
        
        if response_get.status_code == 200:
            user = response_get.json()
            return render_template('updateuser.html', user_id=user)
        else:
            return jsonify({'error': 'user not found'}), 404

    elif request.method == 'POST':
        email = request.form['email']
        newPassword = request.form['newPassword']
        confirmPassword = request.form['confirmPassword']
        password = request.form['password']


        if newPassword != confirmPassword:
            user= {'user':['',g.user,email]}
            return render_template('updateuser.html',user_id = user, message='Les password ne correspondent pas')


        elif newPassword != password:
            password = newPassword
        
            data = {'email': email, 'password': password}
            url_post = f'{urlApi}/user/{user_id}'
            headers = {"Content-Type": "application/json"}
            response_post = requests.put(url_post, json=data, headers=headers)

            if response_post.status_code == 200:
                return redirect(url_for('get_userfilms'))
            else:
                return jsonify({'error': 'user update failed'}), 500
    return redirect(url_for('get_userfilms'))



#***********************************FILMS*****************************************************

# Read all videos
@app.route('/filmAll', methods=['GET'])
def get_films():
    url = f'{urlApi}/films'
    response = requests.get(url)

    if response.status_code == 200:
        films = response.json()
        return render_template('films.html', films=films['films'])
    else:
        return jsonify({'error': 'page not found'}), 404


# Read a specific video
@app.route('/filmAll/<int:titre_id>', methods=['GET'])
def get_film(titre_id):
    url = f'{urlApi}/film/{str(titre_id)}'
    response = requests.get(url)
  
    if response.status_code == 200:
        film = response.json()
        return render_template('film.html', film=film['film'])
    else:
        return jsonify({'error': 'page not found'}), 404

# create film
@app.route('/addfilmAll', methods=['GET', 'POST'])
def create_film():
    if request.method == 'POST':
        titre = request.form['titre']
        genre = request.form['genre']
        annee = request.form['annee']
        realisateur = request.form['realisateur']
        data = {'titre': titre, 'genre': genre, 'annee': annee, 'realisateur': realisateur}
        url = f'{urlApi}/addfilm'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data,headers=headers)

        if response.status_code == 201:
            return render_template('addfilm.html', message='Film créé et ajouté'),201
        elif response.status_code == 500:
            return render_template('addfilm.html', message='Film déja ajouté'),500
        else:
            return jsonify({'error': 'page not found'}), 404
    else:
        return render_template('addfilm.html')


# Update a specific film
@app.route('/update_film/<int:film_id>', methods=[ 'GET','POST'])
@login_required
def update_film(film_id):
    if request.method == 'GET':
        url_get = f'{urlApi}/film/{str(film_id)}'
        response_get = requests.get(url_get)
        
        if response_get.status_code == 200:
            film = response_get.json()
            return render_template('updatefilm.html', film=film['film'])
        else:
            return jsonify({'error': 'Film not found'}), 404

    elif request.method == 'POST':
        titre = request.form['titre']
        genre = request.form['genre']
        annee = request.form['annee']
        realisateur = request.form['realisateur']
        affiche = request.form['affiche']
        data = {'titre': titre, 'genre': genre, 'annee': annee, 'realisateur': realisateur, 'affiche': affiche}
        url_post = f'{urlApi}/film/{str(film_id)}'
        headers = {"Content-Type": "application/json"}
        response_post = requests.put(url_post, json=data, headers=headers)

        if response_post.status_code == 200:
            return redirect(url_for('get_userfilms'))
        else:
            return jsonify({'error': 'Film update failed'}), 500
    return redirect(url_for('get_userfilms'))


# Delete a specific video6
@app.route('/filmAll/<int:film_id>', methods=['POST', 'DELETE'])
def delete_film(film_id):
    url = f'{urlApi}/film/{str(film_id)}'
    headers = {"Content-Type": "application/json"}
    response = requests.delete(url, json=film_id,headers=headers)

    if response.status_code == 200:
        return redirect(url_for('get_films'))
    else:
        return jsonify({'error': 'page not found'}), 404



#****************  USER FILMS  ***********************************************


# Read all user's film
@app.route('/films', methods=['GET'])
@login_required
def get_userfilms():
    url = f'{urlApi}/{g.user}/films'
    response = requests.get(url)
    
    if response.status_code == 200:
        films = response.json()
        return render_template('films.html', films=films['films'])
    else:
        return jsonify({'error': 'page not found'}), 404


# Read a specific user film
@app.route('/film/<int:titre_id>', methods=['GET'])
@login_required
def get_userfilm(titre_id):
    url = f'{urlApi}/{g.user}/film/{str(titre_id)}'
    response = requests.get(url)

    if response.status_code == 200:
        film = response.json()
        return render_template('film.html', film=film['films'][0], user_id=g.user)
    else:
        return jsonify({'error': 'page not found'}), 404

# add a film to specific user
@app.route('/addfilm', methods=['GET', 'POST'])
@login_required
def create_userfilm():
    if request.method == 'POST':
        id = request.form['film']
        data = {'id': id}
        url = f'{urlApi}/{g.user}/addfilm'
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data,headers=headers)

        if response.status_code == 201:
            return render_template('addfilm.html', message='Film ajouté'),201
        elif response.status_code == 200:
            return render_template('addfilm.html', message='Film ajouté'),200
        elif response.status_code == 500:
            return render_template('addfilm.html', message='Film déja ajouté'),500
        else:
            return jsonify({'error': 'page not found'}), 404
    else:
        return render_template('addfilm.html')


# Delete USER film
@app.route('/film/<int:film_id>', methods=['POST', 'DELETE'])
@login_required
def delete_userfilm(film_id):
    url = f'{urlApi}/{g.user}/film/{str(film_id)}'
    headers = {"Content-Type": "application/json"}
    response = requests.delete(url, json=film_id,headers=headers)

    if response.status_code == 200:
        return redirect(url_for('get_userfilms'))
    else:
        return jsonify({'error': 'page not found'}), 404



######################################################################   SEARCH   #############
# search a film
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_film():
    if request.method == 'POST':
        titre = request.form['titre']
        data = {'titre': titre}
        url = f'{urlApi}/search'
      
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json= data, headers=headers)

        if response.status_code == 200:
            results = response.json()
            return render_template('search.html', data = results['data'])
            
        else:
            return jsonify({'error': 'page not found'}), 404
         
    return redirect(url_for('get_userfilms'))




if __name__ == '__main__':
    app.run(debug=True, port=5000)




