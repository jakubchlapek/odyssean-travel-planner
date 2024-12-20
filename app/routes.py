from flask import render_template, flash, redirect, url_for, request, session
import sqlalchemy as sa
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, TripForm, ComponentForm, EmptyForm, ParticipantForm
from app.models import User, Trip, Component, ComponentCategory, ComponentType, ExchangeRates, Participant


# Helper functions for dynamically populating form choices
def get_category_choices():
    return [(c.id, c.category_name) for c in db.session.scalars(sa.select(ComponentCategory).order_by(ComponentCategory.id)).all()]

def get_type_choices(category_id=None):
    query = sa.select(ComponentType)
    if category_id:
        query = query.where(ComponentType.category_id == category_id).order_by(ComponentType.id)
    return [(t.id, t.type_name) for t in db.session.scalars(query).all()]

def get_currency_choices():
    return [(e.currency_to, e.currency_to) for e in db.session.scalars(sa.select(ExchangeRates)).all()]

def get_participant_choices(trip_id):
    trip = db.first_or_404(sa.select(Trip).where(Trip.id == trip_id))
    participants = db.session.scalars(trip.participants.select())
    return [(p.id, p.participant_name) for p in participants]

# Helper auth
def is_current_user(user_id):
    return current_user.id == user_id

# Routes
@app.route('/', methods=['GET', 'POST'])
def welcome():
    """Landing page view."""
    form = EmptyForm()
    if form.validate_on_submit():
        return redirect(url_for('login'))
    return render_template('welcome.html', form=form, title='Welcome')


@app.route('/login', methods=["GET", "POST"])
def login():
    """Login page view."""
    if current_user.is_authenticated:
        return redirect(url_for("user", username=current_user.username))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            app.logger.warning(f"Failed login attempt for user {form.username.data}")
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        app.logger.info(f"User {user.username}, id: {user.id} logged in successfully.")
        return redirect(url_for('user', username=user.username))
    return render_template('login.html', title="Login", form=form)


@app.route('/logout')
def logout():
    """Logout route, used only for processing and a redirect."""
    app.logger.info(f"User {current_user.username}, id {current_user.id} logged out.")
    logout_user()
    return redirect(url_for("welcome"))


@app.route('/register', methods=["GET", "POST"])
def register():
    """Register page view for new users."""
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        app.logger.info(f"New user registered: {form.username.data}, id: {user.id}")
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username: str):
    """User profile page view where the user can add and see their trips."""
    user = db.first_or_404(sa.select(User).where(User.username == username))
    trips = db.session.scalars(user.trips.select())
    app.logger.info(f"User {current_user.username}, id: {current_user.id} viewed user's {username} profile.")
    form = TripForm(user_id=current_user.id)
    if form.validate_on_submit():
        trip = Trip(user_id=current_user.id, trip_name=form.trip_name.data)
        db.session.add(trip)
        db.session.commit()
        app.logger.info(f"User {current_user.username}, id: {current_user.id} added a new trip: {form.trip_name.data}, id: {trip.id}.")
        flash('Your trip has been added!')
        return redirect(url_for('user', username=username)) # Reload
    return render_template('user.html', user=user, trips=trips, form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit profile page view where the user can change their username and preferred currency."""
    form = EditProfileForm(current_user.username)
    form.currency.choices = get_currency_choices()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.preferred_currency = form.currency.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        app.logger.info(f"User {current_user.username}, id: {current_user.id} updated their profile.")
        flash("Your changes have been saved.")
        return redirect(session['url_on_return'])
    elif request.method == 'GET':
        if request.referrer:
            session['url_on_return'] = request.referrer
        form.username.data = current_user.username
        form.currency.data = current_user.preferred_currency
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form, url_on_return = session['url_on_return'])


@app.route('/trip/<trip_id>', methods=['GET', 'POST'])
@login_required
def trip(trip_id: int):
    """Trip page view where the user can see, add and delete trip components."""
    trip = db.first_or_404(sa.select(Trip).where(Trip.id == trip_id))
    if not is_current_user(trip.user_id):
        flash("You do not have permission to view this trip.")
        app.logger.warning(f"User {current_user.username}, id: {current_user.id} tried to access unauthorized trip {trip_id}.")
        return redirect(url_for('user', username=current_user.username))
    components = db.session.scalars(trip.components.select())
    participants = db.session.scalars(trip.participants.select())
    form = ParticipantForm()
    if form.validate_on_submit():
        participant = Participant(
            trip_id = trip.id,
            participant_name = form.participant_name.data
        )
        db.session.add(participant)
        db.session.commit()
        app.logger.info(f"User {current_user.username}, id: {current_user.id} added a new participant: {form.participant_name.data}, id: {participant.id} to trip id: {trip.id}.")
        flash('Your participant has been added!')
        return redirect(url_for('trip', trip_id=trip_id))
    return render_template('trip.html', title=f"{trip.trip_name}", trip=trip, form=form,
                           components=components, participants=participants,
                           preferred_currency=current_user.preferred_currency)


@app.route('/component/<component_id>', methods=['GET', 'POST'])
@login_required
def component(component_id: int):
    """Component page view where the user can edit a component."""
    component = db.first_or_404(sa.select(Component).where(Component.id == component_id))
    form = ComponentForm()
    # Populate category and type choices from the database
    form.category_id.choices = get_category_choices()
    form.type_id.choices = get_type_choices(category_id=form.category_id.data)
    form.currency.choices = get_currency_choices()
    form.participant_name.choices = get_participant_choices(component.trip_id)

    if form.validate_on_submit(): # Update the component
        component.category_id = form.category_id.data
        component.type_id = form.type_id.data
        component.component_name = form.component_name.data
        component.base_cost = form.base_cost.data
        component.currency = form.currency.data
        component.participant_id = form.participant_name.data
        component.description = form.description.data
        component.link = form.link.data
        component.start_date = form.start_date.data
        component.end_date = form.end_date.data
        db.session.commit()
        app.logger.info(f"User {current_user.username} edited the component {component.component_name}, id: {component.id}.")
        flash('Your component has been updated!')
        return render_template('__reload.html')
    elif request.method == 'GET': # If it's a GET, then no data has been submitted from form so we fill with the component data
        form.category_id.data = component.category_id
        form.type_id.data = component.type_id
        form.component_name.data = component.component_name
        form.base_cost.data = component.base_cost
        form.currency.data = component.currency
        form.participant_name.data = component.participant_id
        form.description.data = component.description
        form.link.data = component.link
        form.start_date.data = component.start_date
        form.end_date.data = component.end_date
    return render_template('component.html', component=component, form=form)


@app.route('/create_component/<trip_id>', methods=['GET', 'POST'])
@login_required
def create_component(trip_id: int):
    """Create component page view where the user can add a new component to a trip."""
    trip = db.first_or_404(sa.select(Trip).where(Trip.id == trip_id))
    form = ComponentForm()
    form.category_id.choices = get_category_choices()
    form.type_id.choices = get_type_choices(category_id=form.category_id.data)
    form.currency.choices = get_currency_choices()
    form.participant_name.choices = get_participant_choices(trip_id)
    if form.validate_on_submit():
        component = Component(
                trip_id = trip_id,
                category_id = form.category_id.data,
                type_id = form.type_id.data, 
                component_name = form.component_name.data,
                base_cost = form.base_cost.data,
                participant_id = form.participant_name.data,
                currency = form.currency.data,
                description = form.description.data,
                link = form.link.data,
                start_date = form.start_date.data,
                end_date = form.end_date.data,)
        db.session.add(component)
        db.session.commit()
        app.logger.info(f"User {current_user.username} added a new component to trip {trip.trip_name}, id: {trip_id}.")
        flash('Your component has been added!')
        return render_template('__reload.html')
    return render_template('_edit_component.html', form=form)
        


@app.route('/type/<category_id>')
@login_required
def type(category_id: int):
    """AJAX route to get component types based on category_id."""
    types = db.session.scalars(
        sa.select(ComponentType)
        .where(ComponentType.category_id == category_id)).all()
    types_list = [(t.id, t.type_name) for t in types]
    return {'types': types_list}


@app.route('/delete_trip/<trip_id>', methods=['POST'])
@login_required
def delete_trip(trip_id: int):
    """AJAX route for processing the deletion in JS scripts."""
    trip = db.session.scalar(
        sa.select(Trip)
        .where(sa.and_(Trip.id == trip_id, Trip.user_id == current_user.id))
    )
    if trip is None:
        app.logger.warning(f"User {current_user.username} tried to delete a non-existing or unauthorized trip {trip_id}")
        return {"success": False, "message": "Trip not found or you do not have permission to delete it."}, 404

    db.session.delete(trip)
    db.session.commit()
    app.logger.info(f"User {current_user.username} deleted trip {trip_id} successfully.")
    return {"success": True, "message": "Trip deleted successfully."}, 200



@app.route('/delete_component/<component_id>', methods=['POST'])
@login_required
def delete_component(component_id: int):
    """AJAX route for processing the deletion in JS."""
    component = db.session.scalar(
        sa.select(Component)
        .join(Trip)
        .where(sa.and_(Component.id == component_id, Trip.user_id == current_user.id)))
    if component is None:
        app.logger.warning(f"User {current_user.username}, id: {current_user.id} tried to delete a non-existing or unauthorized component {component_id}")
        return {"success": False, "message": "Component not found or you do not have permission to delete it."}, 404

    trip_id = component.trip_id
    db.session.delete(component)
    db.session.commit()
    app.logger.info(f"User {current_user.username}, id: {current_user.id} deleted component id: {component_id} from trip id: {trip_id}.")
    return {"success": True, "trip_id": trip_id, "message": "Component deleted successfully."}, 200


@app.route('/delete_participant/<participant_id>', methods=['POST'])
@login_required
def delete_participant(participant_id: int):
    """AJAX route for processing the deletion in JS."""
    participant = db.session.scalar(
        sa.select(Participant)
        .join(Trip)
        .where(sa.and_(Participant.id == participant_id, Trip.user_id == current_user.id)))
    if participant is None:
        app.logger.warning(f"User {current_user.username}, id: {current_user.id} tried to delete a non-existing or unauthorized participant {participant_id}")
        return {"success": False, "message": "Participant not found or you do not have permission to delete it."}, 404

    # Remove the participant from all components
    db.session.execute(
            sa.update(Component)
            .where(Component.participant_id == participant_id)
            .values(participant_id=None)
        )
    
    trip_id = participant.trip_id
    db.session.delete(participant)
    db.session.commit()
    app.logger.info(f"User {current_user.username}, id: {current_user.id} deleted participant id: {participant_id} from trip id: {trip_id}.")
    return {"success": True, "trip_id": trip_id, "message": "Participant deleted successfully."}, 200

@app.route('/activate_component/<component_id>', methods=['POST'])
@login_required
def activate_component(component_id: int):
    """AJAX route for processing the activation in JS."""
    component = db.session.scalar(
        sa.select(Component)
        .join(Trip)
        .where(sa.and_(Component.id == component_id, Trip.user_id == current_user.id)))
    if component is None:
        app.logger.warning(f"User {current_user.username}, id: {current_user.id} tried to activate a non-existing or unauthorized component {component_id}")
        return {"success": False, "message": "Component not found or you do not have permission to activate it."}, 404

    component.is_active = not component.is_active
    db.session.commit()
    app.logger.info(f"User {current_user.username}, id: {current_user.id} activated component id: {component_id}.")
    return {"success": True, "message": "Component activated successfully."}, 200

# WIP
@app.route('/summary/<trip_id>')
@login_required
def get_trip_summary(trip_id: int):
    """Route to get a file with the trip summary."""
    trip = db.first_or_404(sa.select(Trip).where(Trip.id == trip_id))
    if not is_current_user(trip.user_id):
        flash("You do not have permission to view this trip.")
        app.logger.warning(f"User {current_user.username}, id: {current_user.id} tried to access unauthorized trip {trip_id} summary.")
        return redirect(url_for('user', username=current_user.username))
    components = db.session.scalars(trip.components.select())
    participants = db.session.scalars(trip.participants.select())
    return render_template('summary.html', trip=trip, components=components, participants=participants, preferred_currency=current_user.preferred_currency)
