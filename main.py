from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
from datetime import datetime
import math
import json
import os



with open('confin.json','r') as c:
    params = json.load(c)["params"]


local_sever = True
app = Flask(__name__, template_folder='template')
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload-location']



app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME =  params['gmail_user'],
    MAIL_PASSWORD= params['gmail_password']
)
mail = Mail(app)
if(local_sever):
   app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']


db = SQLAlchemy(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(20),  nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120),  nullable=False)

class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(80), unique=False, nullable=False)
    slug = db.Column(db.String(21),  nullable=False)
    post = db.Column(db.String(12), nullable=False)
    tagline = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(12),  nullable=False)
    img_file = db.Column(db.String(12),  nullable=False)



@app.route("/")
def home():
    post = Post.query.filter_by().all()
    last = math.ceil(len(post)/int(params['no_of_page']))


    #pagination logic

    page = request.args.get('page')

    if( not str(page).isnumeric()):
        page = 1
    page = int(page)

    post = post[(page-1)*int(params['no_of_page']):(page-1)*int(params['no_of_page'])+int(params['no_of_page'])]
    if (page==1):
        prev = "#"
        next ="/?page="+str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)




    return render_template('index.html',params=params, post=post , prev=prev, next=next)

@app.route("/index")
def index():
    post = Post.query.filter_by().all()[0:params['no_of_page']]
    return render_template('index.html',params=params,post=post)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params, post= post)


@app.route("/about")
def about():
    return render_template('about.html',params=params)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        """Add entry to the database"""
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        massage=request.form.get('message')
        entry = Contact(name=name, email=email, phone=phone, msg=massage)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New massage from' + name,
                          sender= email,
                          recipients=[params['gmail_user']],
                          body=massage + "\n" + phone
                          )
    return render_template('contact.html',params=params)

@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if "user" in session and session['user'] == params["admin_user"]:
       if (request.method=='POST'):
           f= request.files['file']
           f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename )))
           return 'Upload successfully'

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/log')

@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if "user" in session and session['user'] == params["admin_user"]:
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/log')

@app.route("/log" , methods=['GET', 'POST'])
def log():
    if "user" in session and session['user'] == params["admin_user"]:
        post = Post.query.all()
        return render_template('dashboard.html', params= params, post=post)
    elif request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('upass')
        if username == params["admin_user"] and userpass == params["admin_pass"]:
            #set the session variable
            session["user"] = username
            post = Post.query.all()
        return render_template('dashboard.html', params= params, post=post)


    else:
        return render_template('log.html',params=params ,)

@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
        if "user" in session and session['user'] == params["admin_user"]:
            if request.method == 'POST':
                box_titel = request.form.get('titel')
                tline = request.form.get('tline')
                slug = request.form.get('slug')
                post = request.form.get('post')
                img_file = request.form.get('img_file')
                date = datetime.now()

                if sno =='0':
                    post = Post(titel = box_titel,tagline=tline, slug=slug, post=post,img_file=img_file, date=date)
                    db.session.add(post)
                    db.session.commit()
                else:
                    post = Post.query.filter_by(sno=sno).first()
                    post.titel=box_titel
                    post.slug=slug
                    post.post=post
                    post.tagline=tline
                    post.date= date
                    post.img_file=img_file
                    #db.session.add(post)
                    db.session.commit()
                    return redirect('/edit/'+ sno)

            post = Post.query.filter_by(sno=sno).first()
            return render_template('edit.html', params=params, sno=sno, post=post)




app.run(debug=True)
