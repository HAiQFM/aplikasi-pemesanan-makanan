from run import app


def get_client():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return app.test_client()


def test_checkout_page_loads():
    client = get_client()
    response = client.get('/order/checkout')
    assert response.status_code == 200


def test_order_history_page_loads():
    client = get_client()
    response = client.get('/order/history')
    assert response.status_code == 200


def test_order_success_page_loads():
    client = get_client()
    response = client.get('/order/success')
    assert response.status_code == 200


def test_checkout_post_redirects_to_success():
    client = get_client()
    response = client.post('/order/checkout', data={'payment_method': 'cash'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/order/success')


def test_checkout_name_prefilled_after_login():
    client = get_client()
    client.post('/auth/register', data={'name': 'Firas User', 'email': 'firas@mail.com', 'password': 'secret123'})
    client.post('/auth/login', data={'email': 'firas@mail.com', 'password': 'secret123'})

    response = client.get('/order/checkout')
    assert response.status_code == 200
    assert b'value="Firas User"' in response.data


def test_checkout_name_empty_when_not_logged_in():
    client = get_client()
    response = client.get('/order/checkout')
    assert response.status_code == 200
    assert b'value=""' in response.data
