'''-----------------------------------Important libraries------------------------------'''
from flask import Flask, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import login_user, UserMixin, current_user, logout_user, login_required, LoginManager
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, EmailField,TextAreaField, SelectField  
from  wtforms.validators import InputRequired, ValidationError, Length, EqualTo
from datetime import datetime, date, timedelta
from flask_restful import Resource, Api, fields, marshal_with, reqparse, abort
from flask_cors import CORS
from flask_moment import Moment
import flask_excel as excel

'''--------------------------Important function for running the code--------------------'''

app = Flask(__name__)
db= SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban_project.sqlite3'
app.config['SECRET_KEY'] = 'agdrwedgffsfqtewadsfgfhar1254@'
api = Api(app)
cors = CORS(app)
moment = Moment(app)




login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
excel.init_excel(app)

'''=====================================Database Section================================'''
class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer(), primary_key = True)
    name = db.Column(db.String(), nullable = False)
    email = db.Column(db.String(),  nullable= False)
    password = db.Column(db.String(), nullable =  False)
    lists = db.relationship('List', backref = 'user', cascade = "all, delete")


    def get_username(self, email):
        return self.email
    def get_id(self):
        return self.user_id
    
class List(db.Model):
    list_id = db.Column(db.Integer(), primary_key = True)
    list_name = db.Column(db.Integer(), nullable = False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'),nullable = False)
    cards = db.relationship('Card', backref ='list', cascade ="all, delete")

class Card(db.Model):
    card_id = db.Column(db.Integer(), primary_key = True)
    title = db.Column(db.Text(), nullable = False)
    content = db.Column(db.Text(), nullable = False)
    creation_date = db.Column(db.DateTime(), nullable=False)
    last_update = db.Column(db.DateTime(), nullable=False)
    completion_date = db.Column(db.Date(), nullable = False)
    flag = db.Column(db.Boolean(), nullable= True)
    task_completed = db.Column(db.DateTime())
    list_belongs_to = db.Column(db.Integer(), db.ForeignKey('list.list_id'), nullable= False)


'''==================================End Of Database Section============================'''

'''=====================================WT Forms========================================'''
'''=================================Registraion Form===================================='''

class RegistrationFrom(FlaskForm):
    name = StringField('Name', validators=[InputRequired()], render_kw={"placeholder":"Name","autocomplete":"off", "autocorrect":"off"})

    email = EmailField('Email', validators=[InputRequired()], render_kw = {"placeholder":"Email","autocomplete":"off", "autocorrect":"off"})

    password = PasswordField("Password", validators=[InputRequired(), Length(min=4, max=25),EqualTo('confirm_password')], render_kw={"placeholder":"Password","autocomplete":"off","autocorrect":"off"})
    
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired(), Length(min=4, max=25)], render_kw={"placeholder":"Confirm Password","autocomplete":"off","autocorrect":"off"})

    submit = SubmitField("Create an Account")

    def validate_email(self, email):
        existing_email= User.query.filter_by(email = email.data.strip().lower()).first()
        if existing_email:
            flash("Account already exist!")
            raise ValidationError()

'''=====================================Login Form======================================'''

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired()], render_kw={"placeholder":"Email", "autocomplete":"off", "autofill":"off", "autocorrect":"off"})

    password = PasswordField("Password", validators=[InputRequired()], render_kw={"placeholder":"Password", "autocomplete":"off", "autofill":"off", "autocorrect":"off"})

    submit = SubmitField("Log In")

'''====================================List Form Section================================'''
'''=================================List Additon Form==================================='''
class ListForm(FlaskForm):
    list_name = StringField('Name of the list',validators=[InputRequired()], render_kw={"placeholder":"Name","autocomplete":"off", "autocorrect":"off"})
    submit = SubmitField("Confirm")
'''=======================Form for Updating a List======================================'''

class UpdateListForm(FlaskForm):
    new_name = StringField('New list name',validators=[InputRequired()], render_kw={"placeholder":"Update the name","autocomplete":"off", "autocorrect":"off"} )
    submit = SubmitField("Confirm")

'''====================================End of List Form Section========================='''
'''====================================Card Form Section================================'''
'''===================================Card Addition Form================================'''
class CardForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()], render_kw={"placeholder":"Title"})
    content = TextAreaField("Content", validators=[InputRequired()], render_kw={"placeholder":"Content"})
    completion_date = DateField('Deadline', validators=[InputRequired()])
    flag = BooleanField("If task is completed then click on check box.")
    submit = SubmitField("Confirm")

'''======================================Card Update Form==============================='''

class UpdateCardForm(FlaskForm):
    title = StringField('New Title',  render_kw={"placeholder":"Update title here"})
    content = TextAreaField("Content",  render_kw={"placeholder":"Update content here"})
    flag = BooleanField("If task is completed then click on check box.")
    submit = SubmitField("Confirm")

'''================================Move a Card Form====================================='''
class MoveCardForm(FlaskForm):
    list_name = SelectField('Select a list', coerce=int)
    submit = SubmitField('Confirm')
'''===============================Forget Password Form================================='''

class ForgotForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()], render_kw={"placeholder":"Name"})
    email = EmailField('Email', validators=[InputRequired()], render_kw={"placeholder":"Name","autocomplete":"off", "autocorrect":"off",})
    new_password = PasswordField('New Password',validators=[InputRequired(), EqualTo('confirm_password')], render_kw={"placeholder":"New Password"})
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired()], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField("Submit")

'''====================================End of Card Form Section========================='''

'''===================================Delete Confirmation Page=========================='''
class DeleteConfirmation(FlaskForm):
    flag = BooleanField("Are you sure? If yes then please tick the check box.")
    submit = SubmitField('Confirm')

'''=========================================WT Form Section Ended======================='''

'''-------------------------------Python Code for Running the app-----------------------'''
'''--------------------------------User Loader------------------------------------------'''

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

'''=====================================End of User Loader Section======================'''
'''====================================Home Page Section================================'''

@app.route('/')
def home():
    return render_template("index.html")


'''-----------------------------------Registration Section----------------------------'''

@app.route('/register', methods=['GET', 'POST'])
def register():
    register = RegistrationFrom()
    if register.validate_on_submit():
        password_hash = bcrypt.generate_password_hash(register.password.data)
        new_user = User(name = register.name.data.strip().title(), email = register.email.data.strip().lower(), password= password_hash)
        db.session.add(new_user)
        db.session.commit()
        flash("You have successfully created a new account!")
        return redirect(url_for('login'))
    return render_template('registration.html', register = register)

'''-------------------------------------Login section-----------------------------------'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user =User.query.filter_by(email = login_form.email.data.strip().lower()).first()
        if user:
            if bcrypt.check_password_hash(user.password,login_form.password.data):
                login_user(user)         
                flash("You're logged in successfully!")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials!")
                return render_template('login.html', login_form = login_form)
        else:
            flash("Invalid credentials!")
            return render_template('login.html', login_form = login_form)
    return render_template('login.html', login_form = login_form)

'''=================================CRUD on List Section================================'''
'''===================================Create a New List ================================'''

@app.route('/list', methods=["GET", 'POST'])
@login_required
def add_list():
    list_form = ListForm()
    if list_form.validate_on_submit():
        list = List.query.filter_by(user_id =current_user.user_id).all()
        name_list = []
        for i in list:
            name_list.append(i.list_name.capitalize())
        new_list = List(list_name = list_form.list_name.data.capitalize(), user_id = current_user.user_id)
        if new_list.list_name in name_list:
            flash("List name already exists!")
            return render_template('list.html', list_form = list_form)
            
        else:
            db.session.add(new_list)
            db.session.commit()
            flash('List created successefully!')
        return redirect(url_for('dashboard')) 
    return render_template('list.html', list_form = list_form)

'''=========================================Update the Old List========================='''

@app.route('/list/<int:list_id>/update', methods=['GET','POST'])
@login_required
def update_list(list_id):
    list_form = UpdateListForm()
    if list_form.validate_on_submit():
        list = List.query.filter_by(user_id =current_user.user_id).all()
        old_list = List.query.get(list_id)
        name_list = []  
        for i in list:
            name_list.append(i.list_name.capitalize())
        for j in list:
            if list_id == j.list_id:
                if list_form.new_name.data.strip().capitalize() in name_list:
                    flash("List name already exists!")
                    return render_template('update_list.html', list_form = list_form)
             
                else:
                    old_list.list_name = list_form.new_name.data.strip().capitalize()
                    db.session.commit()
                    flash("List successfully updated!")
                    return redirect(url_for('dashboard'))        
    return render_template('update_list.html', list_form = list_form)
'''=====================================Delete the List================================='''

@app.route('/list/<int:list_id>/delete', methods=['GET', "POST"])
@login_required
def delete(list_id):
    del_list = List.query.get(list_id)
    form = DeleteConfirmation()
    if form.validate_on_submit():
        if form.flag.data == True:
            db.session.delete(del_list)
            db.session.commit()
            flash("List "+del_list.list_name +" deleted successfully!")
            return redirect(url_for('dashboard'))
        else:
            flash("List not deleted!")
            return redirect(url_for("dashboard"))  
    return render_template('delete_confirmation.html', form = form)

'''=================================CRUD on Card Section================================'''
'''=================================Create a Card ======================================'''

@app.route('/card/<int:list_id>/create_card', methods=['GET', 'POST'])
@login_required
def cards(list_id):
    cards = CardForm()
    if cards.validate_on_submit():
        creation_date = datetime.now()
        last_update = datetime.now()
        new_card = Card(title=cards.title.data.strip().capitalize(), content = cards.content.data, completion_date = cards.completion_date.data, flag = cards.flag.data, list_belongs_to = list_id, creation_date = creation_date, last_update = last_update)
        card = Card.query.filter_by(list_belongs_to = list_id).all()
        name_card = []
        for i in card:
            name_card.append(i.title.capitalize())
        if new_card.title.strip().capitalize() in name_card:
            flash("Card title already exists!")
            return render_template('cards.html',cards = cards)
        if cards.completion_date.data < date.today():
            flash("Deadline must be today's date or after today's date!")
            return render_template('cards.html',cards = cards) 
        else:
            if cards.flag.data == True:
                task_completed = Card(title=cards.title.data.strip().capitalize(), content = cards.content.data, completion_date = cards.completion_date.data, flag = cards.flag.data, list_belongs_to = list_id, creation_date = creation_date, last_update = last_update,task_completed = datetime.now())
                db.session.add(task_completed)
            else:
                db.session.add(new_card)
            db.session.commit()
            flash("Card created successfully!")
            return redirect(url_for('dashboard'))
    return render_template('cards.html',cards = cards) 

'''===============================Update the old Card==================================='''

@app.route('/card/<int:card_id>/update', methods=['GET', 'POST'])
@login_required
def update_card(card_id):
    update_card_form = UpdateCardForm()
    if update_card_form.validate_on_submit():
        cards = Card.query.get(card_id)
        if cards.flag == False:
            list_id = cards.list_belongs_to
            list = Card.query.filter_by(list_belongs_to = list_id).all()
            card_title = []
            for i in list:
                card_title.append(i.title.capitalize())
            if update_card_form.title.data != '':
                if update_card_form.title.data.strip().capitalize() in card_title:
                    flash("Card title already exists!")
                    return render_template('update_card.html', card = update_card_form)      
                else:
                    cards.title = update_card_form.title.data.strip().capitalize()
            if update_card_form.content.data != '':
                cards.content = update_card_form.content.data
            if update_card_form.flag.data != '':
                cards.flag = update_card_form.flag.data
            cards.last_update = datetime.now()
            if update_card_form.flag.data == True:
                cards.task_completed =datetime.now()    
            db.session.commit()
            flash("Card updated successfully!")
            return redirect(url_for('dashboard'))
        else:
            flash("No more updations allowed. Task is already completed!")
    return render_template('update_card.html', card = update_card_form)

'''====================================Delete a Card===================================='''

@app.route('/card/<int:card_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_card(card_id):
    card = Card.query.get(card_id)
    form = DeleteConfirmation()
    list_id = card.list_belongs_to
    if form.validate_on_submit():
        if form.flag.data == True:
            db.session.delete(card)
            db.session.commit()
            flash("Card "+ card.title +" deleted successfully!")
            return redirect(url_for('dashboard'))
        else:
            flash("Card not deleted!")    
            return redirect(url_for('dashboard'))
    return render_template('delete_card.html', form = form, list = List.query.get(list_id))

'''=================================Move a Card========================================='''
@app.route('/card/<int:card_id>/move', methods=['GET', 'POST'])
@login_required
def move_card(card_id):
    form = MoveCardForm()
    card = Card.query.get(card_id)
    avl_list = List.query.filter_by(user_id = current_user.user_id).all()
    form.list_name.choices =[]
    for i in avl_list:
        if i.list_id != card.list_belongs_to:
            form.list_name.choices.append((i.list_id, i.list_name))
    if len(form.list_name.choices) ==0:
        flash("No list available to move the card!") 
        return redirect(url_for("dashboard"))
    else:
        if form.validate_on_submit():
            list_id = form.list_name.data
            card.list_belongs_to = list_id
            db.session.add(card)
            db.session.commit()
            flash("Card successfully moved to another list!")
            return redirect(url_for('dashboard'))
    return render_template('move_card.html', form = form)

'''===================================Move All Cards===================================='''

@app.route('/card/<int:list_id>/move_all_cards', methods= ['GET', 'POST'])
@login_required
def move_all_cards(list_id):
    form = MoveCardForm()
    cards = Card.query.filter_by(list_belongs_to=list_id).all()
    avl_list = List.query.filter_by(user_id = current_user.user_id).all()
    form.list_name.choices=[]
    for i in avl_list:
        if i.list_id != list_id:
            form.list_name.choices.append((i.list_id, i.list_name))
    if cards == []:
        flash("Current list is empty!")
        return redirect(url_for("dashboard"))
    
    elif len(form.list_name.choices) ==0:
        flash("No list available to move the card!") 
        return redirect(url_for("dashboard"))
    else:
        if form.validate_on_submit():
            new_list_id = form.list_name.data
            list_name = List.query.get(new_list_id)
            for i in cards:
                i.list_belongs_to = new_list_id
                db.session.add(i)
            db.session.commit()
            flash("All the cards are moved to list " + list_name.list_name+"!")
            return redirect(url_for('dashboard'))
    return render_template('move_cards.html', form = form)


'''====================================User Dashboard==================================='''

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    lists = List.query.filter_by(user_id = current_user.user_id).all()
    cards = Card.query.all()
    dat = date.today()
    return render_template('dashboard.html', user = current_user.name, list = lists, cards = cards, dat = dat, t= current_user.name.title())

'''==================================Cards board section================================'''
@app.route('/cards/<int:list_id>', methods=['GET','POST'])
@login_required
def card_dashboard(list_id):
    cards = Card.query.filter_by(list_belongs_to = list_id).all()
    list = List.query.get(list_id)
    to_do = []
    pending = []
    complete = []
    if cards != []:
        for i in cards:
            if i.completion_date >= date.today() and i.flag == False:
                to_do.append(i)
            elif i.completion_date <= date.today() and i.flag == False:
                    pending.append(i)
            else:
                complete.append(i)
        return render_template('card_dashboard.html', card = cards, list = list,to_do = to_do, pending = pending, complete = complete)
    else:
        flash("List is empty!")
        return redirect(url_for('dashboard'))

'''====================================Extra Section===================================='''
'''=====================================Forgot Password Section========================='''
@app.route('/forgot', methods=['GET', 'POST'])
def forget():
    forgot_form = ForgotForm()
    if forgot_form.validate_on_submit():
        registered_email = forgot_form.email.data.strip().lower()
        registered_name = forgot_form.name.data.strip().title()
        user = User.query.filter_by(email = registered_email, name = registered_name).first()
        if user: 
            password_hash = bcrypt.generate_password_hash(forgot_form.new_password.data)
            user.password = password_hash
            db.session.commit()
            flash("You have successfully recovered account password!")
            return redirect(url_for("login"))           
        else:
            flash("Invalid credentials!")
            return render_template("forgotpassword.html", forgot_form = forgot_form)   
    return render_template("forgotpassword.html", forgot_form = forgot_form)
'''================================End of the Passwrod Forgot section==================='''
'''=================================Summary Section===================================='''
@app.route('/summary/<int:list_id>', methods=['GET', 'POST'])
@login_required
def summary(list_id):
    cards = Card.query.filter_by(list_belongs_to = list_id).all()
    to_do_task = []
    pending_tasks=[]
    completed_task = []
    test_list = [["Tasks type", "# of cards"]]
    date_comp_dic = {}
    date_comp_list = [["Days", "# of tasks completed"]]
    if cards != []:
        for i in cards:
            if i.flag == True:
                if i.task_completed.strftime("%b %d") in date_comp_dic.keys():
                    date_comp_dic[i.task_completed.strftime("%b %d")] += 1
                else:
                    date_comp_dic[i.task_completed.strftime("%b %d")] = 1
                
            if i.completion_date >= date.today() and i.flag == False:
                to_do_task.append([i.completion_date, i.title])
            elif i.completion_date <= date.today() and i.flag == False:
                pending_tasks.append([i.completion_date, i.title])
            else:
                completed_task.append([i.completion_date, i.title])
        test_list.append(["# To-do cards", len(to_do_task)])
        test_list.append(["# Deadline crossed cards", len(pending_tasks)])
        test_list.append(["# Completed cards", len(completed_task)])           
        new_list = list(date_comp_dic.items())
        date_comp_list += new_list            
        return render_template('summary.html', t = date_comp_list, test = test_list)
    else:
        flash("List is empty!")
        return redirect(url_for('dashboard'))
'''======================================Excel Download========================'''
@app.route("/download/<int:list_id>/excel", methods=['GET'])
@login_required
def download_file(list_id):
    cards= Card.query.filter_by(list_belongs_to = list_id)
    card_dic={"Title":[], "Content":[], "Deadline":[], "Wheter Completed?":[], "Task Completion Date":[], "Card Creation Date Time":[], "Last Update":[],}
    card_list= [["Title","Content", "Deadline", "Wheter Completed?", "Task Completion Date", "Card Creation Date Time","Last Update"]]
    for i in cards:
        if i.flag == True:
            card_list.append([i.title,i.content, i.completion_date.strftime("%d %b %Y"), "Yes", i.task_completed.strftime("%d %b %Y %H:%M:%S"),i.creation_date.strftime("%d %b %Y %H:%M:%S"),i.last_update.strftime("%d %b %Y %H:%M:%S")])
        else:
            card_list.append([i.title,i.content, i.completion_date.strftime("%d %b %Y"), "No", i.task_completed,i.creation_date.strftime("%d %b %Y %H:%M:%S"),i.last_update.strftime("%d %b %Y %H:%M:%S")])        
    return excel.make_response_from_array(card_list, "csv")


'''===================================Logout Section===================================='''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

'''======================================End Of the Logout Section======================'''

    

'''====================================Api Section code=========================================================='''

'''============================Api Curd on List================================================================'''
list_details = {
  "list_id": fields.Integer,
  "list_name": fields.String,
  "user_id": fields.Integer,
}

create_list_parser = reqparse.RequestParser()
create_list_parser.add_argument("list_name")

update_list_parser = reqparse.RequestParser()
update_list_parser.add_argument("list_name")

class ListApi(Resource):
    @marshal_with(list_details)
    def get(self, list_name, email):
        user = User.query.filter_by(email = email.strip().lower()).first()
        if user:
            list = List.query.filter_by(list_name = list_name.strip().capitalize(), user_id = user.user_id).first()
            if list:
                return list, 200
            else:
                abort(404, message = "List doesn't exists")
        else:
           abort(404, message = "User doesn't exists")
    
    @marshal_with(list_details)
    def put(self, list_name, email):
        args = update_list_parser.parse_args()
        name = args.get("list_name", None)
        user = User.query.filter_by(email = email.strip().lower()).first()
        if user:
            list = List.query.filter_by(list_name = list_name.strip().capitalize(), user_id = user.user_id).first()
            if list:
                avl_list = []
                lists = List.query.filter_by(user_id = user.user_id).all()
                for i in lists:
                    avl_list.append(i.list_name)
                if (type(name) is str) and (name != "None" and name != ""):
                    if name.strip().capitalize() not in avl_list:
                        list.list_name = name.strip().capitalize()
                        db.session.commit()
                        return list, 200
                    else:
                        abort(409, message="List name already exists")
                else:
                    abort(400, message="Invalid Input" )
            else:
                abort(404, message='List not found')
        else:
            abort(404, message="User not found")
    
    @marshal_with(list_details)
    def post(self, email):
        user = User.query.filter_by(email= email.strip().lower()).first()
        args = create_list_parser.parse_args()
        list_name = args.get('list_name')
        
        if user:
            avl_list = []
            lists = List.query.filter_by(user_id = user.user_id).all()
            for i in lists:
                avl_list.append(i.list_name)
            if (type(list_name) is str) and (list_name != "None" and list_name != ""):
                if list_name.strip().capitalize() not in avl_list:
                    new_list = List(list_name = list_name.strip().capitalize(), user_id = user.user_id)
                    db.session.add(new_list)
                    db.session.commit()
                    new_list_info = List.query.filter_by(list_name= list_name, user_id = user.user_id).first()
                    return new_list_info, 200
                else:
                    abort(409, message="List name already exists")     
            else:
                abort(400, message="Invalid Input")
        else:
            abort(404, message="User not found")
    def delete(self, list_name, email):
        user = User.query.filter_by(email = email.strip().lower()).first()
        if user:
            list = List.query.filter_by(list_name = list_name , user_id = user.user_id).first()
            if list:
                db.session.delete(list)
                db.session.commit()
                return "Successfully deleted"
            else:
                abort(404, message="List not found")
        else:
            abort(404, message= "User not found")
api.add_resource(ListApi, '/api/list/<string:email>',"/api/list/<string:list_name>/<string:email>" )
'''======================================CRUD on list completed================================================='''
'''=======================================Api CRUD on Card====================================================='''
card_details = {
    "card_id": fields.Integer,
    "title": fields.String,
    "content": fields.String,
    "creation_date": fields.DateTime,
    "last_update": fields.DateTime,
    "completion_date": fields.String,
    "flag": fields.Boolean,
    "task_completed": fields.DateTime,
    "list_belongs_to": fields.Integer,
}

create_card_parser = reqparse.RequestParser()
create_card_parser.add_argument("card_title")
create_card_parser.add_argument("card_content")
create_card_parser.add_argument("flag")
create_card_parser.add_argument("dead_line")

update_card_parser = reqparse.RequestParser()
update_card_parser.add_argument("card_title")
update_card_parser.add_argument("card_content")
update_card_parser.add_argument("flag")

class CardApi(Resource):
    @marshal_with(card_details)
    def get(self, card_title, list_name, email):
        user = User.query.filter_by(email = email.strip().lower()).first()
        if user:
            list = List.query.filter_by(list_name = list_name.strip().capitalize(), user_id = user.user_id).first()
            if list:
                card = Card.query.filter_by(title = card_title.strip().capitalize(), list_belongs_to = list.list_id).first()
                if card:
                    return card, 200
                else:
                    abort(404, message="Card not found")
            else:
                abort(404, message="List not found") 
        else:
            abort(404, message="User not found")

    @marshal_with(card_details)
    def put(self, card_title, list_name, email):
        args = update_card_parser.parse_args()
        user = User.query.filter_by(email = email.strip().lower()).first()
        if user:
            list = List.query.filter_by(list_name = list_name.strip().capitalize(), user_id = user.user_id).first()
            if list:
                card = Card.query.filter_by(title = card_title.strip().capitalize(), list_belongs_to = list.list_id).first() 
                if card:
                    cards = Card.query.filter_by(list_belongs_to = list.list_id).all()
                    avl_cards = []
                    for i in cards:
                        avl_cards.append(i.title)

                    new_title = args.get('card_title')
                    new_content = args.get('card_content')
                    new_flag = args.get('flag')

                    if (new_title not in ["None",""]) and (type(new_title) is str):
                        if new_title.strip().capitalize() != avl_cards:
                            card.title = new_title.strip().capitalize()
                        else:
                            abort(409, message='Card title already exists')
                    else:
                        abort(400, "Title:Invalid Input")
                    if new_content not in [None,"None", ""]:
                        card.content = new_content
                    else:
                        abort(400, message="Content: Invalid Input")
                    if new_flag not in ['True','true',"false", 'False']:
                        abort(400, message="Flag:Invalid input")
                    else:
                        card.flag = eval(new_flag.capitalize())
                        if new_flag in ['True', 'true']:
                            card.task_completed = datetime.now()
                    db.session.commit()
                    return card,200
                else:
                    abort(404, message="Card not found")
            else:
                abort(404, message="List not found")
        else:
            abort(404, message="User not found")
    
    def delete(self, card_title, list_name, email):
        user = User.query.filter_by(email = email.strip().lower()).first()
        if user:
            list = List.query.filter_by(list_name = list_name.strip().capitalize(), user_id = user.user_id).first()
            if list:
                card = Card.query.filter_by(title = card_title.strip().capitalize(), list_belongs_to = list.list_id).first()
                if card:
                    db.session.delete(card)
                    db.session.commit()
                    return "Card successefully deleted", 200
                else:
                    abort(404, message="Card not found")
            else:
                abort(404, message="List not found")
        else:
            abort(404, message="User not found")
    
    @marshal_with(card_details)
    def post(self, list_name, email):
        args = create_card_parser.parse_args()
        user = User.query.filter_by(email = email.strip().lower()).first()
        if user:
            list = List.query.filter_by(list_name = list_name.strip().capitalize(), user_id = user.user_id).first()
            if list:
                cards = Card.query.filter_by(list_belongs_to = list.list_id).all()
                cards_title = []
                for i in cards:
                        cards_title.append(i.title)

                title = args.get('card_title')
                content = args.get("card_content")
                dead_line = int(args.get("dead_line"))
                flag = (args.get("flag")).capitalize()
                deadline = date.today() + timedelta(days= dead_line)
                if (title not in ["None",""]) and (type(title) is str):
                    if title.strip().capitalize() not in cards_title: 
                        if flag not in ['True','False'] or content in [None, "None", ""]:
                            abort(400, message="Invalid input")
                        else:
                            new_flag = eval(flag)
                            if new_flag == True:
                                card = Card(title = title.strip().capitalize(), content = content, flag = new_flag, completion_date = deadline, creation_date = datetime.now(), last_update = datetime.now(), task_completed= datetime.now(), list_belongs_to = list.list_id)
                            else:
                                card = Card(title = title.strip().capitalize(), content = content, flag = new_flag, completion_date = deadline, creation_date = datetime.now(), last_update = datetime.now(), list_belongs_to = list.list_id)
                            db.session.add(card)
                            db.session.commit()
                        new_card = Card.query.filter_by(title =  title.strip().capitalize(), list_belongs_to= list.list_id).first()
                        return new_card , 200
                    else:
                        abort(404, message="Card already exists")
                else:
                    abort(400, "Card title: Invalid Input")
            else:
                abort(400, message="List not found")
        else:
            abort(404, message="User not found")

api.add_resource(CardApi, '/api/card/<string:list_name>/<string:email>',"/api/card/<string:card_title>/<string:list_name>/<string:email>")
'''======================================Summary Api Resourse========================================='''

class SummaryApi(Resource):
    def get(self, list_name, email):
        user = User.query.filter_by(email = email.strip().lower()).first()
        if user:
            lists = List.query.filter_by(list_name = list_name.strip().capitalize(), user_id = user.user_id).first()
            if list:
                cards = Card.query.filter_by(list_belongs_to = lists.list_id).all()
                to_do_task = 0
                pending_tasks= 0
                completed_task = 0
                if cards != []:
                    for i in cards:
                        if i.flag == True:
                            completed_task += 1 
                        elif i.completion_date >= date.today() and i.flag == False:
                            to_do_task += 1
                        else:
                            pending_tasks += 1
                return {"number of tasks completed":completed_task, "number of tasks in progess":to_do_task, "number of deadline crossed tasks":pending_tasks}, 200
            else:
                abort(404, message = "List doesn't exists")
        else:
           abort(404, message = "User doesn't exists")

api.add_resource(SummaryApi, '/api/summary/<string:list_name>/<string:email>')



'''======================================App Run Section================================'''

if __name__ == "__main__":
    app.run()

'''======================================End Of App Run Section========================''' 

