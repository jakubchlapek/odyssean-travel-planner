from flask import render_template, flash, redirect, url_for, request
import sqlalchemy as sa
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, TripForm, ComponentForm, EmptyForm
from app.models import User, Trip, Component



@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = TripForm(user_id=current_user.id)
    if form.validate_on_submit():
        trip = Trip(user_id=current_user.id, trip_name=form.trip_name.data)
        db.session.add(trip)
        db.session.commit()
        flash('Your trip has been added!')
        return redirect(url_for('index'))
    return render_template('index.html', title='Home', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title="Login", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    trips = db.session.scalars(user.trips.select())
    return render_template('user.html', user=user, trips=trips)

@app.route('/trip/<trip_id>', methods=['GET', 'POST'])
@login_required
def trip(trip_id):
    trip = db.first_or_404(sa.select(Trip).where(Trip.id == trip_id))
    form = ComponentForm()
    if form.validate_on_submit():
        component = Component(
                trip_id = trip_id,
                category_id = 1,
                type_id = 1,
                component_name = form.component_name.data,
                base_cost = form.base_cost.data,
                currency = form.currency.data,
                description = form.description.data,
                start_date = form.start_date.data,
                end_date = form.end_date.data,)
        db.session.add(component)
        db.session.commit()
        flash('Your component has been added!')
        return redirect(url_for('trip', trip_id=trip_id))
    components = db.session.scalars(trip.components.select())
    return render_template('trip.html', trip=trip, components=components, form=form)


@app.route('/delete_trip/<trip_id>')
@login_required
def delete_trip(trip_id):
    trip = db.session.scalar(
        sa.select(Trip)
        .where(sa.and_(Trip.id == trip_id, Trip.user_id == current_user.id)))
    if trip is None:
        flash("Trip not found or you do not have permission to delete it.")
        return redirect(url_for('index'))
    db.session.delete(trip)
    db.session.commit()
    flash("Trip deleted successfully.")
    return redirect(url_for('index'))


@app.route('/component/<component_id>', methods=['GET', 'POST'])
@login_required
def component(component_id):
    component = db.first_or_404(sa.select(Component).where(Component.id == component_id))
    form = ComponentForm()
    if form.validate_on_submit():
        component.category_id = form.category_id.data,
        component.type_id = form.type_id.data,
        component.component_name = form.component_name.data,
        component.base_cost = form.base_cost.data,
        component.currency = form.currency.data,
        component.description = form.description.data,
        component.start_date = form.start_date.data,
        component.end_date = form.end_date.data
        db.session.commit()
        flash('Your component has been updated!')
        return redirect(url_for('trip', component_id=component_id))
    return render_template('component.html', component=component, form=form)


@app.route('/delete_component/<component_id>')
@login_required
def delete_component(component_id):
    component = db.session.scalar(
        sa.select(Component)
        .join(Trip)
        .where(sa.and_(Component.id == component_id, Trip.user_id == current_user.id)))
    if component is None:
        flash("Component not found or you do not have permission to delete it.")
        return redirect(url_for('index'))
    trip_id = component.trip_id
    db.session.delete(component)
    db.session.commit()
    flash("Component deleted successfully.")
    return redirect(url_for('trip', trip_id=trip_id))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.preferred_currency = form.currency.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.currency.data = current_user.preferred_currency
    return render_template('edit_profile.html', title='Edit Profile', form=form)