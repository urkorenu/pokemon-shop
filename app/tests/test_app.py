import pytest
from flask import session, url_for
from app import create_app, db
from app.models import User, Card, Cart, Order

@pytest.fixture
def test_app():
    """
    Sets up a Flask test app for basic app verification.
    Does not delete or modify existing data in the database.
    """
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test_secret"
    app.config["CACHE_TYPE"] = "flask_caching.backends.NullCache"

    with app.app_context():
        db.create_all()  # Creates tables for the test
        yield app  # Test runs here
        db.session.remove()

@pytest.fixture
def client(test_app):
    """
    Provides a test client to simulate HTTP requests to the app.
    """
    return test_app.test_client()

def test_home_page(client):
    """
    Test to check if the home page is accessible and working.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Available" in response.data  # Check if "Welcome" text is in the page

def test_login_page(client):
    """
    Test to verify the login page renders correctly.
    """
    response = client.get("/auth/sign-in")
    assert response.status_code == 200
    assert b"Login" in response.data  # Check if "Login" text is in the page

def test_manage_users_get(client, admin_user):
    """
    Test to verify the manage users page renders correctly for an admin.
    """
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'password'})
    response = client.get('/admin/users')
    assert response.status_code == 200
    assert b'admin' in response.data
    assert b'user' in response.data

def test_manage_users_post_invalid_data(client, admin_user):
    """
    Test to verify invalid data submission on manage users page.
    """
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'password'})
    response = client.post('/admin/users', data={'user_id': '', 'role_': 'invalid_role'})
    assert response.status_code == 302
    assert b'Invalid user or role data.' in session['_flashes'][0][1]

def test_manage_users_post_valid_data(client, admin_user, normal_user):
    """
    Test to verify valid data submission on manage users page.
    """
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'password'})
    response = client.post('/admin/users', data={'user_id': normal_user.id, 'role_{}'.format(normal_user.id): 'uploader'})
    assert response.status_code == 302
    assert b"User user's role updated to uploader." in session['_flashes'][0][1]
    assert User.query.get(normal_user.id).role == 'uploader'

def test_manage_users_post_ban_user(client, admin_user, normal_user):
    """
    Test to verify banning a user on manage users page.
    """
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'password'})
    response = client.post('/admin/users', data={'user_id': normal_user.id, 'role_{}'.format(normal_user.id): 'banned', 'ban_reason_{}'.format(normal_user.id): 'Violation of terms'})
    assert response.status_code == 302
    assert b"User user has been banned." in session['_flashes'][0][1]
    assert User.query.get(normal_user.id).role == 'banned'
    assert Card.query.filter_by(uploader_id=normal_user.id).count() == 0

def test_manage_users_post_unban_user(client, admin_user, normal_user):
    """
    Test to verify unbanning a user on manage users page.
    """
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'password'})
    normal_user.role = 'banned'
    db.session.commit()
    response = client.post('/admin/users', data={'user_id': normal_user.id, 'role_{}'.format(normal_user.id): 'normal'})
    assert response.status_code == 302
    assert b"User user's role updated to normal." in session['_flashes'][0][1]
    assert User.query.get(normal_user.id).role == 'normal'

def test_auth_login_success(client, user):
    response = client.post('/auth/sign-in', data={'form_type': 'login', 'email': user.email, 'password': 'password'})
    assert response.status_code == 302
    assert b'Login successful!' in response.data

def test_auth_login_invalid_credentials(client):
    response = client.post('/auth/sign-in', data={'form_type': 'login', 'email': 'invalid@example.com', 'password': 'wrongpassword'})
    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data

def test_auth_register_success(client):
    response = client.post('/auth/sign-in', data={
        'form_type': 'register',
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password',
        'location': 'Tel Aviv',
        'contact_preference': 'phone',
        'contact_details': '123456789'
    })
    assert response.status_code == 302
    assert b'Registration successful! Please log in.' in response.data

def test_auth_register_missing_fields(client):
    response = client.post('/auth/sign-in', data={
        'form_type': 'register',
        'username': '',
        'email': 'newuser@example.com',
        'password': 'password',
        'location': 'Tel Aviv',
        'contact_preference': 'phone',
        'contact_details': '123456789'
    })
    assert response.status_code == 200
    assert b'All fields are required.' in response.data

def test_auth_register_existing_email(client, user):
    response = client.post('/auth/sign-in', data={
        'form_type': 'register',
        'username': 'newuser',
        'email': user.email,
        'password': 'password',
        'location': 'Tel Aviv',
        'contact_preference': 'phone',
        'contact_details': '123456789'
    })
    assert response.status_code == 200
    assert b'Email already registered. Please log in.' in response.data

def test_logout_user(client, user):
    client.post('/auth/sign-in', data={'form_type': 'login', 'email': user.email, 'password': 'password'})
    response = client.get('/logout')
    assert response.status_code == 302
    assert b'You have been logged out.' in response.data

def test_account_update_profile(client, user):
    client.post('/auth/sign-in', data={'form_type': 'login', 'email': user.email, 'password': 'password'})
    response = client.post('/account', data={
        'action': 'update_profile',
        'username': 'updateduser',
        'email': 'updateduser@example.com',
        'location': 'Jerusalem',
        'contact_preference': 'facebook',
        'contact_details': 'updatedcontact'
    })
    assert response.status_code == 302
    assert b'Profile updated successfully!' in response.data

def test_account_change_password(client, user):
    client.post('/auth/sign-in', data={'form_type': 'login', 'email': user.email, 'password': 'password'})
    response = client.post('/account', data={
        'action': 'change_password',
        'old_password': 'password',
        'new_password': 'newpassword'
    })
    assert response.status_code == 302
    assert b'Password updated successfully!' in response.data

def test_account_delete_account(client, user):
    client.post('/auth/sign-in', data={'form_type': 'login', 'email': user.email, 'password': 'password'})
    response = client.post('/account', data={'action': 'delete_account'})
    assert response.status_code == 302
    assert b'Your account has been deleted.' in response.data

def test_request_uploader_success(client, user):
    client.post('/auth/sign-in', data={'form_type': 'login', 'email': user.email, 'password': 'password'})
    response = client.post('/request_uploader', data={'rules_accepted': 'true'})
    assert response.status_code == 302
    assert b'Your request to become an uploader has been submitted successfully!' in response.data

def request_uploader_missing_details(client, user):
    client.post('/auth/sign-in', data={'form_type': 'login', 'email': user.email, 'password': 'password'})
    user.email = ''
    db.session.commit()
    response = client.post('/request_uploader', data={'rules_accepted': 'true'})
    assert response.status_code == 302
    assert b'Please ensure your profile details (email, location, and contact details) are updated.' in response.data

def test_view_cart(client, user):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    return client.get(url_for('cart.view_cart'))

def test_remove_from_cart(client, user, cart_item):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    return client.post(url_for('cart.remove_from_cart', cart_id=cart_item.id))

def test_checkout(client, user):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    return client.post(url_for('cart.checkout'))

def test_view_cart_displays_items(client, user, cart_items):
    response = view_cart(client, user)
    assert response.status_code == 200
    for item in cart_items:
        assert item.card.name.encode() in response.data

def test_view_cart_displays_total_price(client, user, total_price):
    response = view_cart(client, user)
    assert response.status_code == 200
    assert str(total_price).encode() in response.data

def test_remove_from_cart_success(client, user, cart_item):
    response = remove_from_cart(client, user, cart_item)
    assert response.status_code == 302
    assert b'Item removed from cart.' in response.data

def test_remove_from_cart_unauthorized(client, user, other_user_cart_item):
    response = remove_from_cart(client, user, other_user_cart_item)
    assert response.status_code == 302
    assert b'You are not authorized to perform this action.' in response.data

def test_checkout_empty_cart(client, user):
    response = checkout(client, user)
    assert response.status_code == 302
    assert b'Your cart is empty.' in response.data

def test_checkout_success(client, user, cart_items):
    response = checkout(client, user)
    assert response.status_code == 302
    assert b'Orders placed successfully! Sellers have been notified.' in response.data
    assert Cart.query.filter_by(user_id=user.id).count() == 0
    assert Order.query.filter_by(buyer_id=user.id).count() > 0

def test_place_order_success(client, user, card):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.post(url_for('order.place_order', card_id=card.id))
    assert response.status_code == 302
    assert b'Order placed successfully!' in response.data

def test_place_order_own_card(client, user, own_card):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.post(url_for('order.place_order', card_id=own_card.id))
    assert response.status_code == 302
    assert b'You cannot order your own card.' in response.data

def test_place_order_missing_seller(client, user, card_without_seller):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.post(url_for('order.place_order', card_id=card_without_seller.id))
    assert response.status_code == 302
    assert b'Seller information is missing for this card.' in response.data

def test_confirm_order_success(client, user, order):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.post(url_for('order.confirm_order', order_id=order.id))
    assert response.status_code == 302
    assert b'Order confirmed' in response.data

def test_confirm_order_unauthorized(client, user, other_user_order):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.post(url_for('order.confirm_order', order_id=other_user_order.id))
    assert response.status_code == 302
    assert b'You are not authorized to confirm this order.' in response.data

def test_reject_order_success(client, user, order):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.post(url_for('order.reject_order', order_id=order.id))
    assert response.status_code == 302
    assert b'Order rejected successfully.' in response.data

def test_reject_order_unauthorized(client, user, other_user_order):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.post(url_for('order.reject_order', order_id=other_user_order.id))
    assert response.status_code == 302
    assert b'You are not authorized to reject this order.' in response.data

def test_submit_feedback_success(client, user, order):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.post(url_for('order.submit_feedback', order_id=order.id), data={'feedback': 'Great!', 'rating': 5})
    assert response.status_code == 302
    assert b'Thank you for your feedback!' in response.data

def test_submit_feedback_unauthorized(client, user, other_user_order):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.post(url_for('order.submit_feedback', order_id=other_user_order.id), data={'feedback': 'Great!', 'rating': 5})
    assert response.status_code == 302
    assert b'You are not authorized to provide feedback for this order.' in response.data

def test_view_my_orders(client, user):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.get(url_for('order.my_orders'))
    assert response.status_code == 200
    assert b'My Orders' in response.data

def test_view_pending_orders(client, user):
    client.post(url_for('auth.login'), data={'email': user.email, 'password': 'password'})
    response = client.get(url_for('order.pending_orders'))
    assert response.status_code == 200
    assert b'Pending Orders' in response.data

def test_upload_card_success(client, admin_user):
    client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'password'})
    response = client.post(url_for('seller.upload_card'), data={
        'name': 'Pikachu',
        'follow_tcg': 'on',
        'price': '10.0',
        'condition': 'NM',
        'set_name': 'Base Set',
        'number': '25',
        'card_type': 'normal',
        'is_graded': 'off'
    })
    assert response.status_code == 302
    assert b'Card uploaded successfully!' in response.data

def test_upload_card_missing_details(client, admin_user):
    client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'password'})
    response = client.post(url_for('seller.upload_card'), data={
        'name': '',
        'follow_tcg': 'on',
        'price': '10.0',
        'condition': 'NM',
        'set_name': 'Base Set',
        'number': '25',
        'card_type': 'normal',
        'is_graded': 'off'
    })
    assert response.status_code == 200
    assert b'No card found. Please verify the set name and card number.' in response.data

def test_upload_card_name_mismatch(client, admin_user):
    client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'password'})
    response = client.post(url_for('seller.upload_card'), data={
        'name': 'Charizard',
        'follow_tcg': 'on',
        'price': '10.0',
        'condition': 'NM',
        'set_name': 'Base Set',
        'number': '25',
        'card_type': 'normal',
        'is_graded': 'off'
    })
    assert response.status_code == 200
    assert b'Card name does not match. Expected: Pikachu' in response.data

def test_get_card_details_success(client, admin_user):
    client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'password'})
    response = client.get(url_for('seller.get_card_details', set_name='Base Set', number='25'))
    assert response.status_code == 200
    assert b'Pikachu' in response.data

def test_get_card_details_missing_params(client, admin_user):
    client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'password'})
    response = client.get(url_for('seller.get_card_details', set_name='', number=''))
    assert response.status_code == 400
    assert b'Missing required parameters' in response.data

def test_get_card_details_not_found(client, admin_user):
    client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'password'})
    response = client.get(url_for('seller.get_card_details', set_name='Nonexistent Set', number='999'))
    assert response.status_code == 404
    assert b'No card found' in response.data

def test_view_cards_pagination(client):
    response = client.get(url_for('user.view_cards', page=2))
    assert response.status_code == 200
    assert b'Next' in response.data

def test_set_language_success(client):
    response = client.post(url_for('user.set_language'), data={'lang': 'en', 'referrer': '/'})
    assert response.status_code == 302
    assert 'lang' in session
    assert session['lang'] == 'en'

def test_set_language_invalid(client):
    response = client.post(url_for('user.set_language'), data={'lang': 'invalid', 'referrer': '/'})
    assert response.status_code == 302
    assert b'Invalid language selection.' in response.data

def test_report_user_success(client, admin_user, normal_user):
    client.post(url_for('auth.login'), data={'email': normal_user.email, 'password': 'password'})
    response = client.post(url_for('user.report_user', user_id=admin_user.id), data={'reason': 'Spam', 'details': 'Spamming messages'})
    assert response.status_code == 302
    assert b'User has been reported successfully.' in response.data

def test_report_user_missing_reason(client, admin_user, normal_user):
    client.post(url_for('auth.login'), data={'email': normal_user.email, 'password': 'password'})
    response = client.post(url_for('user.report_user', user_id=admin_user.id), data={'reason': '', 'details': 'Spamming messages'})
    assert response.status_code == 302
    assert b'Please provide a reason for the report.' in response.data

def test_profile_view_success(client, normal_user):
    response = client.get(url_for('user.profile', user_id=normal_user.id))
    assert response.status_code == 200
    assert b'Profile' in response.data

def test_my_cards_access_denied(client, normal_user):
    client.post(url_for('auth.login'), data={'email': normal_user.email, 'password': 'password'})
    response = client.get(url_for('user.my_cards'))
    assert response.status_code == 302
    assert b'You do not have permission to access this page.' in response.data

def test_edit_card_success(client, uploader_user, card):
    client.post(url_for('auth.login'), data={'email': uploader_user.email, 'password': 'password'})
    response = client.post(url_for('user.edit_card', card_id=card.id), data={'name': 'New Name', 'price': '20.0'})
    assert response.status_code == 302
    assert b'Card updated successfully!' in response.data

def test_delete_card_success(client, admin_user, card):
    client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'password'})
    response = client.post(url_for('user.delete_card', card_id=card.id))
    assert response.status_code == 302
    assert b'Card deleted successfully!' in response.data

def test_report_card_success(client, normal_user, card):
    client.post(url_for('auth.login'), data={'email': normal_user.email, 'password': 'password'})
    response = client.post(url_for('user.report_card', card_id=card.id), data={'reason': 'Inappropriate content', 'details': 'Contains offensive language'})
    assert response.status_code == 302
    assert b'Report submitted successfully.' in response.data

def test_add_to_cart_success(client, normal_user, card):
    client.post(url_for('auth.login'), data={'email': normal_user.email, 'password': 'password'})
    response = client.post(url_for('user.add_to_cart'), data={'card_id': card.id})
    assert response.status_code == 302
    assert b'has been added to your cart.' in response.data

def test_view_cart_success(client, normal_user):
    client.post(url_for('auth.login'), data={'email': normal_user.email, 'password': 'password'})
    response = client.get(url_for('user.view_cart'))
    assert response.status_code == 200
    assert b'Your Cart' in response.data

def test_contact_us_success(client):
    response = client.post(url_for('user.contact_us'), data={'name': 'John Doe', 'email': 'john@example.com', 'message': 'Hello!'})
    assert response.status_code == 302
    assert b'Your message has been sent successfully!' in response.data

def test_about_us_view(client):
    response = client.get(url_for('user.about_us'))
    assert response.status_code == 200
    assert b'About Us' in response.data
